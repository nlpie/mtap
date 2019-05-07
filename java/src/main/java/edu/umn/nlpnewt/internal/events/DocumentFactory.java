package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Document;
import edu.umn.nlpnewt.Event;

public interface DocumentFactory {
  Document createDocument(EventsClient client, Event event, String documentName);
}
