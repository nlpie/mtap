package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Document;
import edu.umn.nlpnewt.Event;
import edu.umn.nlpnewt.Internal;

@Internal
public interface DocumentFactory {
  Document createDocument(EventsClient client, Event event, String documentName);
}
