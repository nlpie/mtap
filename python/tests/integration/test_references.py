import pytest

from mtap import events_client, Pipeline, Event, GenericLabel, RemoteProcessor


def validate_references(deployment, pipeline):
    with events_client(deployment['events']) as c, \
            Event(event_id='1', client=c) as event:
        document = event.create_document('plaintext', 'abcd')
        pipeline.run(document)
        references = document.labels['references']
        assert references[0].a == GenericLabel(0, 1)
        assert references[0].b == GenericLabel(1, 2)
        assert references[1].a == GenericLabel(2, 3)
        assert references[1].b == GenericLabel(3, 4)

        map_references = document.labels['map_references']
        assert map_references[0].ref == {
            'a': GenericLabel(0, 1),
            'b': GenericLabel(1, 2),
            'c': GenericLabel(2, 3),
            'd': GenericLabel(3, 4)
        }

        list_references = document.labels['list_references']
        assert list_references[0].ref == [GenericLabel(0, 1),
                                          GenericLabel(1, 2)]
        assert list_references[1].ref == [GenericLabel(2, 3),
                                          GenericLabel(3, 4)]


@pytest.mark.integration
def test_java_references(deployment):
    pipeline = Pipeline(
        RemoteProcessor('mtap-java-reference-labels-example-processor',
                        address=(deployment['java_references'])),
        events_address=deployment['events']
    )
    validate_references(deployment, pipeline)


@pytest.mark.integration
def test_python_references(deployment):
    pipeline = Pipeline(
        RemoteProcessor('mtap-python-references-example',
                        address=deployment['py_references']),
        events_address=deployment['events']
    )
    validate_references(deployment, pipeline)
