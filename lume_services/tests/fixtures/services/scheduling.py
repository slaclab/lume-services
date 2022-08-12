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
def docker_run_config(prefect_docker_tag, file_service, lume_env):

    mounted_filesystems = file_service.get_mounted_filesystems()
    mounts = []
    for filesystem in mounted_filesystems.values():
        mounts.append(
            {
                "target": filesystem.mount_alias,
                "source": filesystem.mount_path,
                "type": "bind",
            }
        )

    host_config = {"mounts": mounts}

    return DockerRunConfig(
        image=prefect_docker_tag, env=lume_env, host_config=host_config
    )


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="class", autouse=True)
def docker_backend(lume_services_settings):
    return DockerBackend(config=lume_services_settings.prefect)


@pytest.mark.usefixtures("docker_services")
@pytest.fixture(scope="class", autouse=True)
def scheduling_service(docker_backend):
    return SchedulingService(backend=docker_backend)
