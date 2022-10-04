/*
 * Copyright 2021 Regents of the University of Minnesota.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

package edu.umn.nlpie.mtap;

import com.google.protobuf.ByteString;
import com.google.protobuf.Message;
import edu.umn.nlpie.mtap.api.v1.EventsGrpc;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass.GetLabelIndicesInfoResponse;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass.GetLabelIndicesInfoResponse.LabelIndexInfo;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass.GetLabelsResponse;
import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.common.ConfigImpl;
import edu.umn.nlpie.mtap.discovery.Discovery;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.discovery.ServiceInfo;
import edu.umn.nlpie.mtap.processing.HSMHealthService;
import edu.umn.nlpie.mtap.processing.HealthService;
import edu.umn.nlpie.mtap.utilities.Helpers;
import io.grpc.Server;
import io.grpc.Status;
import io.grpc.netty.shaded.io.grpc.netty.NettyServerBuilder;
import io.grpc.stub.StreamObserver;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;
import org.kohsuke.args4j.OptionHandlerFilter;
import org.kohsuke.args4j.spi.PathOptionHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

public class EventsServer implements edu.umn.nlpie.mtap.common.Server, Closeable {
  private static final List<String> RESERVED_FIELD_NAMES = Arrays.asList(
      "document", "location", "text", "id", "label_index_name"
  );

  private static final Logger LOGGER = LoggerFactory.getLogger(EventsServer.class);
  private final @NotNull Server grpcServer;
  private final @NotNull String host;
  private final boolean writeAddress;
  private final @NotNull HealthService healthService;
  private final @Nullable DiscoveryMechanism discoveryMechanism;

  private boolean running = false;
  private int port = -1;
  private @Nullable Path addressFile = null;
  private @Nullable ServiceInfo serviceInfo;

  EventsServer(
      @NotNull Server grpcServer,
      @NotNull String host,
      boolean writeAddress,
      @NotNull HealthService healthService,
      @Nullable DiscoveryMechanism discoveryMechanism
      ) {
    this.grpcServer = grpcServer;
    this.host = host;
    this.writeAddress = writeAddress;
    this.healthService = healthService;
    this.discoveryMechanism = discoveryMechanism;
  }

  @Override
  public void start() throws IOException {
    if (running) {
      return;
    }
    running = true;
    grpcServer.start();
    port = grpcServer.getPort();

    if (writeAddress) {
      Path homeDir = Helpers.getHomeDirectory();
      addressFile = homeDir.resolve("addresses").resolve("" + ProcessHandle.current().pid()
          + ".address");
      try (BufferedWriter w = Files.newBufferedWriter(addressFile, StandardOpenOption.CREATE_NEW)) {
        w.write("" + host + ":" + port);
      }
    }

    healthService.startedServing("");
    healthService.startedServing(MTAP.EVENTS_SERVICE_NAME);
    if (discoveryMechanism != null) {
      UUID uuid = UUID.randomUUID();
      serviceInfo = new ServiceInfo(
          MTAP.EVENTS_SERVICE_NAME,
          uuid.toString(),
          host,
          port,
          Collections.singletonList("v1")
      );
      discoveryMechanism.register(serviceInfo);
    }
    Runtime.getRuntime().addShutdownHook(new Thread(this::shutdown));
    LOGGER.info("Started events service on port: {}", port);
  }

  @Override
  public void shutdown() {
    if (!running) {
      return;
    }
    healthService.stoppedServing(MTAP.PROCESSOR_SERVICE_TAG);
    healthService.stoppedServing("");
    if (discoveryMechanism != null) {
      assert serviceInfo != null;
      discoveryMechanism.deregister(serviceInfo);
    }
    grpcServer.shutdown();
    running = false;
    if (addressFile != null) {
      try {
        Files.delete(addressFile);
      } catch (IOException e) {
        LOGGER.error("Failed to delete address file", e);
      }
    }
    System.out.println("Stopped events service on port: " + port);
  }

  @Override
  public void blockUntilShutdown() throws InterruptedException {
    grpcServer.awaitTermination();
  }

  @Override
  public int getPort() {
    return port;
  }

  @Override
  public boolean isRunning() {
    return running;
  }

  @Override
  public void close() throws IOException {

  }

  private static class EventsServicer extends EventsGrpc.EventsImplBase {
    private final @NotNull ConcurrentHashMap<@NotNull String, @NotNull EventStore> backingMap;
    private final UUID instanceId;

    private EventsServicer() {
      backingMap = new ConcurrentHashMap<>();
      instanceId = UUID.randomUUID();
    }

    @Override
    public void getEventsInstanceId(EventsOuterClass.GetEventsInstanceIdRequest request, StreamObserver<EventsOuterClass.GetEventsInstanceIdResponse> responseObserver) {
      LOGGER.debug("Get Instance Id called");
      responseObserver.onNext(EventsOuterClass.GetEventsInstanceIdResponse.newBuilder()
          .setInstanceId(instanceId.toString()).build());
      responseObserver.onCompleted();
      LOGGER.debug("Get Instance Id completed");
    }

    @Override
    public void openEvent(EventsOuterClass.OpenEventRequest request,
                          StreamObserver<EventsOuterClass.OpenEventResponse> responseObserver) {
      LOGGER.debug("Open Event called");
      String eventId = request.getEventId();
      LOGGER.debug("Open Event eventId: {}", eventId);
      if (eventId.length() == 0) {
        LOGGER.debug("Null or empty eventId.");
        responseObserver.onError(Status.INVALID_ARGUMENT
            .withDescription("Null or empty eventId").asException());
        responseObserver.onCompleted();
        return;
      }

      AtomicBoolean created = new AtomicBoolean(false);
      EventStore store = backingMap.computeIfAbsent(eventId, (unused) -> {
        created.set(true);
        return new EventStore();
      });

      if (request.getOnlyCreateNew() && !created.get()) {
        LOGGER.debug("Event already exists: {}", eventId);
        responseObserver.onError(Status.ALREADY_EXISTS
            .withDescription("Event already exists: " + eventId).asException());
        responseObserver.onCompleted();
        return;
      }

      store.clients.incrementAndGet();
      responseObserver.onNext(EventsOuterClass.OpenEventResponse.newBuilder()
          .setCreated(created.get()).build());
      responseObserver.onCompleted();
      LOGGER.debug("Open Event completed.");
    }

    @Override
    public void closeEvent(EventsOuterClass.CloseEventRequest request,
                           StreamObserver<EventsOuterClass.CloseEventResponse> responseObserver) {
      LOGGER.debug("Close Event called.");
      backingMap.computeIfPresent(request.getEventId(), (k, v) -> {
        int clients = v.clients.decrementAndGet();
        if (clients > 0) {
          return v;
        }
        return null;
      });
      responseObserver.onNext(EventsOuterClass.CloseEventResponse.newBuilder().build());
      responseObserver.onCompleted();
      LOGGER.debug("Close Event completed.");
    }

    @Override
    public void getAllMetadata(
        EventsOuterClass.GetAllMetadataRequest request,
        StreamObserver<EventsOuterClass.GetAllMetadataResponse> responseObserver
    ) {
      LOGGER.debug("GetAllMetadata called");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      responseObserver.onNext(EventsOuterClass.GetAllMetadataResponse.newBuilder()
          .putAllMetadata(eventStore.metadata).build());
      responseObserver.onCompleted();
      LOGGER.debug("GetAllMetadata completed");
    }

    @Override
    public void addMetadata(
        EventsOuterClass.AddMetadataRequest request,
        StreamObserver<EventsOuterClass.AddMetadataResponse> responseObserver
    ) {
      LOGGER.debug("AddMetadata called");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      String key = request.getKey();
      if (key.length() == 0) {
        LOGGER.debug("Empty metadata key.");
        responseObserver.onError(Status.INVALID_ARGUMENT
            .withDescription("Empty or null metadata key.").asException());
        responseObserver.onCompleted();
        return;
      }

      AtomicBoolean exists = new AtomicBoolean(false);
      eventStore.metadata.compute(key, (k, v) -> {
        if (v != null) {
          exists.set(true);
          return v;
        }
        return request.getValue();
      });
      if (exists.get()) {
        String msg = String.format("Metadata with key %s already exists on event %s", key, eventId);
        LOGGER.debug(msg);
        responseObserver.onError(Status.ALREADY_EXISTS.withDescription(msg).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.AddMetadataResponse.newBuilder().build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("AddMetadata completed");
    }

    @Override
    public void addDocument(
        EventsOuterClass.AddDocumentRequest request,
        StreamObserver<EventsOuterClass.AddDocumentResponse> responseObserver
    ) {
      LOGGER.debug("AddDocument started");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      String documentName = request.getDocumentName();
      if (documentName.length() == 0) {
        LOGGER.debug("Empty documentName.");
        responseObserver.onError(Status.INVALID_ARGUMENT
            .withDescription("Empty or null documentName.").asException());
        responseObserver.onCompleted();
        return;
      }

      AtomicBoolean exists = new AtomicBoolean(false);
      eventStore.documents.compute(documentName, (k, v) -> {
        if (v != null) {
          exists.set(true);
          return v;
        }
        return new DocumentStore(request.getText());
      });

      if (exists.get()) {
        String msg = String.format("Document with name %s already exists on event %s",
            documentName, eventId);
        LOGGER.debug(msg);
        responseObserver.onError(Status.ALREADY_EXISTS.withDescription(msg).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.AddDocumentResponse.newBuilder().build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("AddDocument completed");
    }

    @Override
    public void getAllDocumentNames(
        EventsOuterClass.GetAllDocumentNamesRequest request,
        StreamObserver<EventsOuterClass.GetAllDocumentNamesResponse> responseObserver
    ) {
      LOGGER.debug("GetAllDocumentNames called.");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      responseObserver.onNext(EventsOuterClass.GetAllDocumentNamesResponse.newBuilder()
          .addAllDocumentNames(eventStore.documents.keySet()).build());
      responseObserver.onCompleted();
      LOGGER.debug("GetAllDocumentNames completed.");
    }

    @Override
    public void getDocumentText(
        EventsOuterClass.GetDocumentTextRequest request,
        StreamObserver<EventsOuterClass.GetDocumentTextResponse> responseObserver
    ) {
      LOGGER.debug("GetDocumentText called.");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      String documentName = request.getDocumentName();
      DocumentStore documentStore = eventStore.documents.get(documentName);
      if (documentStore == null) {
        String message = String.format("No document with name %s on event %s", documentName,
            eventId);
        LOGGER.debug(message);
        responseObserver.onError(Status.NOT_FOUND.withDescription(message).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.GetDocumentTextResponse.newBuilder()
            .setText(documentStore.text).build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("GetDocumentText completed.");
    }

    @Override
    public void getLabelIndicesInfo(
        EventsOuterClass.GetLabelIndicesInfoRequest request,
        StreamObserver<GetLabelIndicesInfoResponse> responseObserver
    ) {
      LOGGER.debug("GetLabelIndicesInfo called.");
      String eventId = request.getEventId();
      String documentName = request.getDocumentName();
      DocumentStore documentStore = getDocumentStore(responseObserver, eventId, documentName);
      if (documentStore == null) return;
      GetLabelIndicesInfoResponse.Builder response = GetLabelIndicesInfoResponse.newBuilder();
      for (Map.Entry<String, LabelIndexStore> e : documentStore.labelIndices.entrySet()) {
        LabelIndexInfo.Builder info = response.addLabelIndexInfosBuilder();
        info.setIndexName(e.getKey());
        switch (e.getValue().labelsCase) {
          case GENERIC_LABELS:
            info.setType(LabelIndexInfo.LabelIndexType.GENERIC);
            break;
          case CUSTOM_LABELS:
            info.setType(LabelIndexInfo.LabelIndexType.CUSTOM);
            break;
          default:
            info.setType(LabelIndexInfo.LabelIndexType.UNKNOWN);
            break;
        }
        info.build();
      }
      responseObserver.onNext(response.build());
      responseObserver.onCompleted();
      LOGGER.debug("GetLabelIndicesInfo completed.");
    }

    @Override
    public void addLabels(
        EventsOuterClass.AddLabelsRequest request,
        StreamObserver<EventsOuterClass.AddLabelsResponse> responseObserver
    ) {
      LOGGER.debug("AddLabels called");
      String eventId = request.getEventId();
      String documentName = request.getDocumentName();
      DocumentStore documentStore = getDocumentStore(responseObserver, eventId, documentName);
      if (documentStore == null) return;
      String indexName = request.getIndexName();
      if (indexName.length() == 0) {
        String message = String.format(
            "AddLabels called with empty index name for document %s on event %s",
            documentName,
            eventId
        );
        LOGGER.debug(message);
        responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(message).asException());
        responseObserver.onCompleted();
        return;
      }
      EventsOuterClass.AddLabelsRequest.LabelsCase labelsCase = request.getLabelsCase();
      Message labels;
      switch (labelsCase) {
        case GENERIC_LABELS:
          EventsOuterClass.GenericLabels genericLabels = request.getGenericLabels();
          if (!request.getNoKeyValidation()) {
            for (EventsOuterClass.GenericLabel label : genericLabels.getLabelsList()) {
              if (usesReservedKey(responseObserver, eventId, documentName, indexName,
                  label.getFields().getFieldsMap().keySet())) return;
              if (usesReservedKey(responseObserver, eventId, documentName, indexName,
                  label.getReferenceIds().getFieldsMap().keySet())) return;
            }
          }
          labels = genericLabels;
          break;
        case CUSTOM_LABELS:
          labels = request.getCustomLabels();
          break;
        default:
          labelsCase = EventsOuterClass.AddLabelsRequest.LabelsCase.GENERIC_LABELS;
          labels = EventsOuterClass.GenericLabels.newBuilder().build();
          break;
      }
      AtomicBoolean exists = new AtomicBoolean(false);
      EventsOuterClass.AddLabelsRequest.LabelsCase labelsCaseFinal = labelsCase;
      documentStore.labelIndices.compute(indexName, (k, v) -> {
        if (v != null) {
          exists.set(true);
          return v;
        }
        return new LabelIndexStore(labelsCaseFinal, labels);
      });
      if (exists.get()) {
        String message = String.format(
            "EventId: %s, Document Name: %s, Index Name: %s already exists",
            eventId, documentName, indexName
        );
        LOGGER.debug(message);
        responseObserver.onError(Status.ALREADY_EXISTS.withDescription(message).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.AddLabelsResponse.newBuilder().build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("AddLabels completed.");
    }

    @Override
    public void getLabels(
        EventsOuterClass.GetLabelsRequest request,
        StreamObserver<GetLabelsResponse> responseObserver
    ) {
      LOGGER.debug("GetLabels called");
      String eventId = request.getEventId();
      String documentName = request.getDocumentName();
      DocumentStore documentStore = getDocumentStore(responseObserver, eventId, documentName);
      if (documentStore == null) return;
      String indexName = request.getIndexName();
      LabelIndexStore indexStore = documentStore.labelIndices.get(indexName);
      if (indexStore == null) {
        String message = String.format(
            "EventId: %s, Document Name: %s does not have label index with name: %s",
            eventId, documentName, indexName
        );
        LOGGER.debug(message);
        responseObserver.onError(Status.NOT_FOUND.withDescription(message).asException());
        responseObserver.onCompleted();
        return;
      }
      GetLabelsResponse.Builder response = GetLabelsResponse.newBuilder();
      switch (indexStore.labelsCase) {
        case GENERIC_LABELS:
          response.getGenericLabelsBuilder().mergeFrom(indexStore.labelsObject).build();
          break;
        case CUSTOM_LABELS:
          response.getCustomLabelsBuilder().mergeFrom(indexStore.labelsObject).build();
          break;
      }
      responseObserver.onNext(response.build());
      responseObserver.onCompleted();
      LOGGER.debug("GetLabels completed");
    }

    @Override
    public void getAllBinaryDataNames(
        EventsOuterClass.GetAllBinaryDataNamesRequest request,
        StreamObserver<EventsOuterClass.GetAllBinaryDataNamesResponse> responseObserver
    ) {
      LOGGER.debug("GetAllBinaryDataNames called");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      responseObserver.onNext(EventsOuterClass.GetAllBinaryDataNamesResponse.newBuilder()
          .addAllBinaryDataNames(eventStore.binaries.keySet()).build());
      responseObserver.onCompleted();
      LOGGER.debug("GetAllBinaryDataNames completed");
    }

    @Override
    public void addBinaryData(
        EventsOuterClass.AddBinaryDataRequest request,
        StreamObserver<EventsOuterClass.AddBinaryDataResponse> responseObserver
    ) {
      LOGGER.debug("AddBinaryData called.");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      String name = request.getBinaryDataName();
      if (name.length() == 0) {
        String message = String.format("Add binary data on event: %s missing name.", eventId);
        LOGGER.debug(message);
        responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(message).asException());
        responseObserver.onCompleted();
        return;
      }
      AtomicBoolean exists = new AtomicBoolean(false);
      eventStore.binaries.compute(name, (k, v) -> {
        if (v != null) {
          exists.set(true);
          return v;
        }
        return request.getBinaryData();
      });
      if (exists.get()) {
        String message = String.format("Event %s already has binary data with name: %s",
            eventId, name);
        LOGGER.debug(message);
        responseObserver.onError(Status.ALREADY_EXISTS.withDescription(message).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.AddBinaryDataResponse.newBuilder().build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("AddBinaryData completed.");
    }

    @Override
    public void getBinaryData(
        EventsOuterClass.GetBinaryDataRequest request,
        StreamObserver<EventsOuterClass.GetBinaryDataResponse> responseObserver
    ) {
      LOGGER.debug("GetBinaryData called");
      String eventId = request.getEventId();
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return;
      }
      String name = request.getBinaryDataName();
      ByteString bytes = eventStore.binaries.get(name);
      if (bytes == null) {
        String message = String.format("Event %s doesn't have binary data with name: %s",
            eventId, name);
        LOGGER.debug(message);
        responseObserver.onError(Status.NOT_FOUND.withDescription(message).asException());
      } else {
        responseObserver.onNext(EventsOuterClass.GetBinaryDataResponse.newBuilder()
            .setBinaryData(bytes).build());
      }
      responseObserver.onCompleted();
      LOGGER.debug("GetBinaryData completed");
    }

    private void eventNotFound(StreamObserver<?> responseObserver, String eventId) {
      LOGGER.debug("Event not found: {}", eventId);
      responseObserver.onError(Status.NOT_FOUND.withDescription("Event not found: " + eventId)
          .asException());
      responseObserver.onCompleted();
    }

    @Nullable
    private DocumentStore getDocumentStore(
        StreamObserver<?> responseObserver,
        String eventId,
        String documentName
    ) {
      EventStore eventStore = backingMap.get(eventId);
      if (eventStore == null) {
        eventNotFound(responseObserver, eventId);
        return null;
      }
      DocumentStore documentStore = eventStore.documents.get(documentName);
      if (documentStore == null) {
        String message = String.format("No document with name %s on event %s",
            documentName, eventId);
        LOGGER.debug(message);
        responseObserver.onError(Status.NOT_FOUND.withDescription(message).asException());
        responseObserver.onCompleted();
        return null;
      }
      return documentStore;
    }

    private boolean usesReservedKey(
        StreamObserver<EventsOuterClass.AddLabelsResponse> responseObserver,
        String eventId,
        String documentName,
        String indexName,
        Set<String> fieldKeys
    ) {
      for (String fieldKey : fieldKeys) {
        if (RESERVED_FIELD_NAMES.contains(fieldKey)) {
          String message = String.format("%s:%s:%s labels use reserved field key %s",
              eventId, documentName, indexName, fieldKey);
          responseObserver.onError(Status.INVALID_ARGUMENT
              .withDescription(message).asException());
          LOGGER.debug(message);
          responseObserver.onCompleted();
          return true;
        }
      }
      return false;
    }
  }

  private static class DocumentStore {
    private final @NotNull String text;
    private final @NotNull ConcurrentMap<@NotNull String, @NotNull LabelIndexStore> labelIndices;

    public DocumentStore(@NotNull String text) {
      this.text = text;
      this.labelIndices = new ConcurrentHashMap<>();
    }
  }

  private static class LabelIndexStore {
    private final @NotNull EventsOuterClass.AddLabelsRequest.LabelsCase labelsCase;
    private final @NotNull Message labelsObject;

    public LabelIndexStore(
        @NotNull EventsOuterClass.AddLabelsRequest.LabelsCase labelsCase,
        @NotNull Message labelsObject
    ) {
      this.labelsCase = labelsCase;
      this.labelsObject = labelsObject;
    }
  }

  private static class EventStore {
    private final AtomicInteger clients = new AtomicInteger(0);
    private final @NotNull ConcurrentMap<@NotNull String, @Nullable String> metadata;
    private final @NotNull ConcurrentMap<@NotNull String, @NotNull ByteString> binaries;
    private final @NotNull ConcurrentMap<@NotNull String, @NotNull DocumentStore> documents;

    private EventStore() {
      metadata = new ConcurrentHashMap<>();
      binaries = new ConcurrentHashMap<>();
      documents = new ConcurrentHashMap<>();
    }
  }

  public static Builder newBuilder() {
    return new Builder();
  }

  public static class Builder {
    @NotNull
    @Option(name = "--address", aliases = {"--host", "-a"}, metaVar = "HOST",
        usage = "Host i.e. IP address or hostname to bind to.")
    private String hostname = "127.0.0.1";

    @Option(name = "-p", aliases = {"--port"}, metaVar = "PORT",
        usage = "Port to host the processor service on or 0 if it should bind to a random port.")
    private int port = 0;

    @Option(name = "-r", aliases = {"--register"},
        usage = "Whether to register with service discovery.")
    private boolean register = false;

    @Nullable
    @Option(name = "--mtap-config", handler = PathOptionHandler.class, metaVar = "CONFIG_PATH",
        usage = "A path to a config file to load.")
    private Path configFile = null;

    @Option(name = "--workers", aliases = {"-w"}, metaVar = "N_WORKERS",
        usage = "The number of threads to respond to process requests with.")
    private int workers = 10;

    @Option(name = "--write-address",
        usage = "If set, will write the server's resolved address to a file in the MTAP home " +
            "directory")
    private boolean writeAddress = false;

    public Builder() { }

    public @NotNull String getHostname() {
      return hostname;
    }

    public void setHostname(@NotNull String hostname) {
      this.hostname = hostname;
    }

    public @NotNull Builder withAddress(@NotNull String address) {
      this.hostname = address;
      return this;
    }

    public int getPort() {
      return port;
    }

    public void setPort(int port) {
      this.port = port;
    }

    public @NotNull Builder withPort(int port) {
      this.port = port;
      return this;
    }

    public boolean isRegister() {
      return register;
    }

    public void setRegister(boolean register) {
      this.register = register;
    }

    public @NotNull Builder register() {
      this.register = true;
      return this;
    }

    public @Nullable Path getConfigFile() {
      return configFile;
    }

    public void setConfigFile(@Nullable Path configFile) {
      this.configFile = configFile;
    }

    public @NotNull Builder withConfigFile(@Nullable Path configFile) {
      this.configFile = configFile;
      return this;
    }

    public int getWorkers() {
      return workers;
    }

    public void setWorkers(int workers) {
      this.workers = workers;
    }

    public @NotNull Builder withWorkers(int workers) {
      this.workers = workers;
      return this;
    }

    public boolean isWriteAddress() {
      return writeAddress;
    }

    public void setWriteAddress(boolean writeAddress) {
      this.writeAddress = writeAddress;
    }

    public @NotNull Builder writeAddress() {
      this.writeAddress = true;
      return this;
    }

    public EventsServer build() {
      Config config = ConfigImpl.loadConfigFromLocationOrDefaults(configFile);
      DiscoveryMechanism discoveryMechanism = null;
      if (register) {
        discoveryMechanism = Discovery.getDiscoveryMechanism(config);
      }
      HealthService healthService = new HSMHealthService();
      EventsServicer eventsServicer = new EventsServicer();
      NettyServerBuilder builder = NettyServerBuilder.forAddress(new InetSocketAddress(hostname, port));
      Integer maxInboundMessageSize = config.getIntegerValue("grpc.events_options.grpc.max_receive_message_length");
      if (maxInboundMessageSize != null) {
        builder.maxInboundMessageSize(maxInboundMessageSize);
      }
      Integer keepAliveTime = config.getIntegerValue("grpc.events_options.grpc.keepalive_time_ms");
      if (keepAliveTime != null) {
        builder.keepAliveTime(keepAliveTime, TimeUnit.MILLISECONDS);
      }
      Integer keepAliveTimeout = config.getIntegerValue("grpc.events_options.grpc.keepalive_timeout_ms");
      if (keepAliveTimeout != null) {
        builder.keepAliveTimeout(keepAliveTimeout, TimeUnit.MILLISECONDS);
      }
      Boolean permitKeepAliveWithoutCalls = config.getBooleanValue("grpc.events_options.grpc.permit_keepalive_without_calls");
      if (permitKeepAliveWithoutCalls != null) {
        builder.permitKeepAliveWithoutCalls(permitKeepAliveWithoutCalls);
      }
      Integer permitKeepAliveTime = config.getIntegerValue("grpc.events_options.grpc.http2.min_ping_interval_without_data_ms");
      if (permitKeepAliveTime != null) {
        builder.permitKeepAliveTime(permitKeepAliveTime, TimeUnit.MILLISECONDS);
      }
      Server grpcServer = builder.executor(Executors.newFixedThreadPool(workers))
          .addService(healthService.getService())
          .addService(eventsServicer).build();
      return new EventsServer(grpcServer, hostname, writeAddress, healthService,
          discoveryMechanism);
    }
  }

  public static void main(String[] args) {
    Builder builder = EventsServer.newBuilder();
    CmdLineParser parser = new CmdLineParser(builder);
    try {
      parser.parseArgument(args);
      EventsServer server = builder.build();
      server.start();
      server.blockUntilShutdown();
    } catch (CmdLineException e) {
      System.err.println(e.getMessage());
      System.err.println("java " + EventsServer.class.getCanonicalName() + " [options...]");
      System.err.flush();
      parser.printUsage(System.err);
      System.err.println();

      System.err.println("Example: " + EventsServicer.class.getCanonicalName() + parser.printExample(OptionHandlerFilter.ALL));
      System.err.flush();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    }
  }
}
