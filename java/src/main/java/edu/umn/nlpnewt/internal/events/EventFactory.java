package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Event;

public interface EventFactory {
  Event createEvent(EventsClient client, String eventID);
}
