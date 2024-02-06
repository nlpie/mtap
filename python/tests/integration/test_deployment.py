from pathlib import Path

import pytest

from mtap.deployment import Deployment
from mtap.utilities import find_free_port


@pytest.mark.integration
def test_minimal_deployment_configuration():
    deploy_file = Path(__file__).parent / 'minimalDeploymentConfiguration.yml'
    deployment = Deployment.from_yaml_file(deploy_file)
    deployment.processors[0].port = find_free_port()
    with deployment.run_servers() as (event_addresses, processor_addresses):
        assert len(event_addresses) == 0
        assert processor_addresses[0][0].endswith(f':{deployment.processors[0].port}')
