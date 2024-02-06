import sys
from subprocess import PIPE, run

import pytest


@pytest.mark.integration
def test_hello_world(deployment):
    p = run([sys.executable, '-m', 'mtap.examples.tutorial.pipeline', deployment['events'], deployment['py_hello']],
            stdout=PIPE)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'


@pytest.mark.integration
def test_java_hello_world(deployment):
    p = run([sys.executable, '-m', 'mtap.examples.tutorial.pipeline', deployment['events'],
             deployment['java_hello']], stdout=PIPE)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'
