from mtap.pipeline import ProcessingErrorHandler, SimpleErrorHandler, TerminationErrorHandler, LoggingErrorHandler, \
    ErrorsDirectoryErrorHandler, SuppressAllErrorsHandler


def test_registry():
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'simple'}), SimpleErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'termination'}), TerminationErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'logging'}), LoggingErrorHandler)
    directory = ProcessingErrorHandler.from_dict({'name': 'to_directory', 'params': {'output_directory': "."}})
    assert isinstance(directory, ErrorsDirectoryErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'suppress'}), SuppressAllErrorsHandler)
