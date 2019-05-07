package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Event;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

class EventsImplTest {

  private EventsClient eventsClient;
  private EventsImpl tested;
  private EventFactory eventFactory;
  private Event event;

  @BeforeEach
  void setUp() {
    eventsClient = mock(EventsClient.class);
    eventFactory = mock(EventFactory.class);
    event = mock(Event.class);
    when(eventFactory.createEvent(any(), any())).thenReturn(event);
    tested = new EventsImpl(eventsClient, eventFactory);
  }

  @Test
  void openEvent() {
    Event event = tested.openEvent("Foo");
    verify(eventsClient).openEvent("Foo", false);
    verify(eventFactory).createEvent(eventsClient, "Foo");
    assertSame(this.event, event);
  }

  @Test
  void createEventRandomId() {
    Event event = tested.createEvent();
    verify(eventsClient).openEvent(anyString(), eq(true));
    verify(eventFactory).createEvent(same(eventsClient), anyString());
    assertSame(this.event, event);
  }

  @Test
  void createEvent() {
    Event event = tested.createEvent("Foo");
    verify(eventsClient).openEvent("Foo", true);
    verify(eventFactory).createEvent(eventsClient, "Foo");
    assertSame(this.event, event);
  }

  @Test
  void openNullIdThrows() {
    assertThrows(IllegalArgumentException.class, () -> tested.openEvent(null));
  }

  @Test
  void createNullIdThrows() {
    assertThrows(IllegalArgumentException.class, () -> tested.createEvent(null));
  }

  @Test
  void close() {
    tested.close();
    verify(eventsClient).close();
  }
}
