/*
 * Copyright 2019 Regents of the University of Minnesota
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
 */
package edu.umn.nlpnewt;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.netty.NettyServerBuilder;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;

import static org.junit.jupiter.api.Assertions.*;

public class DocumentsProcessorIT {

  @Test
  void documentProcessor() throws IOException {
    io.grpc.Server eventsServer = NettyServerBuilder.forAddress(new InetSocketAddress("127.0.0.1", 0))
        .addService(new EventsService())
        .build();
    eventsServer.start();
    int eventsPort = eventsServer.getPort();

    Newt newt = new Newt();
    Server server = newt.createProcessorServer(ProcessorServerOptions.emptyOptions()
        .withProcessorClass(TestDocumentProcessorBase.class)
        .withEventsTarget("localhost:" + eventsPort));
    server.start();
    int port = server.getPort();

    ManagedChannel channel = ManagedChannelBuilder.forAddress("127.0.0.1", port)
        .usePlaintext()
        .build();
    try (Events events = newt.events("127.0.0.1:" + eventsPort)) {
      try (Event event = events.createEvent("1")) {
        Document document = event.addDocument("blah", "foo");
        ProcessorGrpc.ProcessorBlockingStub processorStub = ProcessorGrpc.newBlockingStub(channel);
        Processing.ProcessResponse response = processorStub.process(
            Processing.ProcessRequest.newBuilder()
                .setEventId(event.getEventID())
                .setParams(Struct.newBuilder()
                    .putFields("document_name", Value.newBuilder()
                        .setStringValue(document.getName())
                        .build())
                    .putFields("do_work", Value.newBuilder().setBoolValue(true).build())
                    .build())
                .build());
        assertNotNull(response);
        assertEquals(42.0, response.getResult().getFieldsOrThrow("answer").getNumberValue());
        LabelIndex<GenericLabel> labelIndex = document.getLabelIndex("foo");
        assertFalse(labelIndex.isDistinct());
        GenericLabel genericLabel = labelIndex.first();
        assertEquals(0, genericLabel.getStartIndex());
        assertEquals(5, genericLabel.getEndIndex());

        LabelIndex<GenericLabel> bar = document.getLabelIndex("bar");
        assertTrue(bar.isDistinct());
        genericLabel = bar.first();
        assertEquals(0, genericLabel.getStartIndex());
        assertEquals(5, genericLabel.getEndIndex());
      }
    } finally {
      channel.shutdown();
      server.shutdown();
    }
  }

  @Processor("test-processor")
  public static class TestDocumentProcessorBase extends DocumentProcessorBase {

    private final ProcessorContext context;

    public TestDocumentProcessorBase(ProcessorContext context) {
      this.context = context;
    }

    @Override
    protected void process(@NotNull Document document,
                           @NotNull JsonObject params,
                           @NotNull JsonObjectBuilder result) {
      Boolean doWork = params.getBooleanValue("do_work");
      if (doWork != null && doWork) {
        Timer fooTimer = context.startTimer("foo_timer");
        try (Labeler<GenericLabel> labeler = document.getLabeler("foo")) {
          labeler.add(GenericLabel.createSpan(0, 5));
        }
        fooTimer.stop();
        try (Labeler<GenericLabel> labeler = document.getLabeler("bar", true)) {
          labeler.add(GenericLabel.createSpan(0, 5));
        }
        result.setProperty("answer", 42);
      }
    }
  }
}
