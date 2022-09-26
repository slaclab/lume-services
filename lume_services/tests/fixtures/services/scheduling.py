import pytest
import os

from lume_services.services.scheduling.backends import (
    DockerBackend,
    DockerRunConfig,
)
from lume_services.services.scheduling.service import SchedulingService

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def lume_env():
    lume_env = {name: val for name, val in os.environ.items() if "LUME" in name}
    # Need to convert to docker network hostnames
    lume_env["LUME_RESULTS_DB__HOST"] = "mongodb"
    lume_env["LUME_MODEL_DB__HOST"] = "mysql"
    return lume_env


@pytest.mark.usefixtures("prefect_job_docker")
@pytest.fixture(scope="session", autouse=True)
def docker_run_config(prefect_docker_tag, rootdir):

    return DockerRunConfig(
        image=prefect_docker_tag,
        env={"EXTRA_PIP_PACKAGES": "/lume/flows"},  # installation of test packages
        host_config={
            "mounts": [
                {
                    "type": "bind",
                    "target": "/lume/flows",
                    "source": f"{rootdir}/lume_services/tests/flows",  # noqa
                }
            ]
        },
    )


# has lume env vars
@pytest.fixture(scope="session")
def docker_run_config_local(lume_services_settings, prefect_docker_tag, rootdir):
    return DockerRunConfig(
        image=prefect_docker_tag,
        env={"EXTRA_PIP_PACKAGES": "/lume/flows"}.update(lume_services_settings),
        host_config={
            "mounts": [
                {
                    "type": "bind",
                    "target": "/lume/flows",
                    "source": f"{rootdir}/lume_services/tests/flows",  # noqa
                }
            ]
        },
    )


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="class", autouse=True)
def docker_backend(lume_services_settings):
    return DockerBackend(config=lume_services_settings.prefect)


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="class", autouse=True)
def scheduling_service(docker_backend):
    return SchedulingService(backend=docker_backend)
