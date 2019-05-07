package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.internal.services.DiscoveryMechanism;
import edu.umn.nlpnewt.internal.services.NewtServices;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.jetbrains.annotations.NotNull;

import java.util.List;

@Internal
public class NewtEvents {
  private final NewtServices newtServices;

  private String address = null;
  private ProtoLabelAdapter<GenericLabel> distinctAdapter = null;
  private ProtoLabelAdapter<GenericLabel> standardAdapter = null;
  private ManagedChannel eventsChannel = null;
  private EventsClient eventsClient = null;
  private EventFactory eventFactory = null;
  private DocumentFactory documentFactory = null;
  private Events events = null;

  public NewtEvents(NewtServices newtServices) {
    this.newtServices = newtServices;
  }

  public String getAddress() {
    return address;
  }

  public NewtEvents setAddress(String address) {
    this.address = address;
    return this;
  }

  public ProtoLabelAdapter<GenericLabel> getDistinctAdapter() {
    if (distinctAdapter == null) {
      distinctAdapter = GenericLabelAdapter.DISTINCT_ADAPTER;
    }
    return distinctAdapter;
  }

  public NewtEvents setDistinctAdapter(ProtoLabelAdapter<GenericLabel> distinctAdapter) {
    this.distinctAdapter = distinctAdapter;
    return this;
  }

  public ProtoLabelAdapter<GenericLabel> getStandardAdapter() {
    if (standardAdapter == null) {
      standardAdapter = GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
    }
    return standardAdapter;
  }

  public NewtEvents setStandardAdapter(ProtoLabelAdapter<GenericLabel> standardAdapter) {
    this.standardAdapter = standardAdapter;
    return this;
  }

  public ManagedChannel getEventsChannel() {
    if (eventsChannel == null) {
      if (address == null) {
        DiscoveryMechanism discoveryMechanism = newtServices.getDiscoveryMechanism();
        eventsChannel = ManagedChannelBuilder
            .forTarget(discoveryMechanism.getServiceTarget(Newt.EVENTS_SERVICE_NAME, "v1"))
            .usePlaintext()
            .nameResolverFactory(discoveryMechanism.getNameResolverFactory())
            .build();
      } else {
        eventsChannel = ManagedChannelBuilder.forTarget(address).usePlaintext().build();
      }
    }
    return eventsChannel;
  }

  public NewtEvents setEventsChannel(ManagedChannel eventsChannel) {
    this.eventsChannel = eventsChannel;
    return this;
  }

  public EventsClient getEventsClient() {
    if (eventsClient == null) {
      eventsClient = new EventsClientImpl(getEventsChannel(), getDistinctAdapter(), getStandardAdapter());
    }
    return eventsClient;
  }

  public NewtEvents setEventsClient(EventsClient eventsClient) {
    this.eventsClient = eventsClient;
    return this;
  }

  public DocumentFactory getDocumentFactory() {
    if (documentFactory == null) {
      documentFactory = new DocumentFactory() {
        @Override
        public Document createDocument(EventsClient client, Event event, String documentName) {
          return new DocumentImpl(client, event, documentName);
        }
      };
    }
    return documentFactory;
  }

  public NewtEvents setDocumentFactory(DocumentFactory documentFactory) {
    this.documentFactory = documentFactory;
    return this;
  }

  public EventFactory getEventFactory() {
    if (eventFactory == null) {
      eventFactory = (client, eventID) -> new EventImpl(client, eventID, getDocumentFactory());
    }
    return eventFactory;
  }

  public NewtEvents setEventFactory(EventFactory eventFactory) {
    this.eventFactory = eventFactory;
    return this;
  }

  public Events getEvents() {
    if (events == null) {
      events = new EventsImpl(getEventsClient(), getEventFactory());
    }
    return events;
  }

  public NewtEvents setEvents(Events events) {
    this.events = events;
    return this;
  }

  public static <L extends Label> @NotNull LabelIndex<@NotNull L> standardLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return StandardLabelIndex.create(labels);
  }

  public static <L extends Label> @NotNull LabelIndex<@NotNull L> distinctLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return DistinctLabelIndex.create(labels);
  }
}
