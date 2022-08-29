import pytest
from click.testing import CliRunner
from lume_services.cli.docker_compose import docker
from unittest import mock

runner = CliRunner()


@pytest.mark.skip(
    "Skip until able to order docker fixture so docker \
    services haven't already started..."
)
def test_start_services():
    response = runner.invoke(docker, ["start-services"])

    with mock.patch(
        "lume_services.cli.docker_compose.wait", side_effect=KeyboardInterrupt
    ):
        response = runner.invoke(docker, ["start-services"])
    assert response.exit_code == 0
    assert "Shutting down LUME-services" in response.output
