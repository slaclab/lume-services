from pydantic import validator, Field
from typing import Optional, List, Dict, Any
import logging

from prefect.run_configs import DockerRun

from docker.types import HostConfig
from lume_services.services.scheduling.backends.backend import RunConfig
from lume_services.services.scheduling.backends.server import ServerBackend

from lume_services.utils import docker_api_version

logger = logging.getLogger(__name__)


class DockerRunConfig(RunConfig):
    """Pydantic representation of a Docker Prefect run configuration:
    https://docs.prefect.io/api/latest/run_configs.html#dockerrun

    Attributes:
        labels (Optional[List[str]]): an list of labels to apply to this run
            config. Labels are string identifiers used by Prefect Agents for selecting
            valid flow runs when polling for work
        env (Optional[dict]): Additional environment variables to set on the job
        image (str): Tag of image in which flow should run.
        host_config (Optional[Dict[str, Any]]): Dictionary representing runtime args
            to be passed to Docker agent. Full documentation of args can be found here:
            https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_host_config
        ports (Optional[List[int]]): An list of ports numbers to expose on
            container.

    """  # noqa

    image: str
    host_config: Dict[str, Any] = None
    ports: Optional[List[int]]

    @validator("host_config", pre=True)
    def validate_host_config(cls, v):
        """Composes a model for the Docker host configuration and applies any passed
        values.

        """
        if isinstance(v, (dict,)):
            # test host config composition using api version
            try:
                HostConfig(version=docker_api_version(), **v)
            except Exception as e:
                logger.exception(e)
                raise e

        return v

    def build(self) -> DockerRun:
        """Method for converting to Prefect RunConfig type DockerRun.

        Returns:
            DockerRun

        """
        return DockerRun(**self.dict(exclude_none=True))


class DockerBackend(ServerBackend):
    """Implementation of Backend used for interacting with prefect deployed in
    cluster of Docker containers, as with docker-compose.

    Attributes:
        config (PrefectConfig): Instantiated PrefectConfig object describing connection
            to Prefect server.
        _client (Client): Prefect client connection created on instantiation.
        _run_config_type (type): Type used to compose Prefect run configuration.

    """

    _run_config_type: type = Field(DockerRunConfig, exclude=True)

    @property
    def run_config_type(self):
        return self._run_config_type
