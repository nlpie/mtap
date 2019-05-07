package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Event;
import edu.umn.nlpnewt.Internal;

@Internal
public interface EventFactory {
  Event createEvent(EventsClient client, String eventID);
}
