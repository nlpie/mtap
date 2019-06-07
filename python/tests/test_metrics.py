from nlpnewt import Events
from nlpnewt._events_service import EventsServicer
from nlpnewt.metrics import Accuracy, Metrics


def test_accuracy():
    with Events(stub=EventsServicer()) as events:
        with events.open_event(event_id='1') as event:
            doc = event.add_document('test', 'This is some text.')
            with doc.get_labeler('tested') as tested:
                tested(0, 5)
                tested(6, 10)
                tested(11, 20)
                tested(21, 29)
                tested(31, 39)

            with doc.get_labeler('target') as target:
                target(0, 5)
                target(6, 10)
                target(11, 20)
                target(21, 30)
                target(31, 39)

            acc = Accuracy()
            metrics = Metrics(acc, tested='tested', target='target')
            metrics.process_document(doc, params={})
            assert abs(acc.value - 0.8) < 1e-6
