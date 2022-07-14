from pydantic import validator, Field
from typing import Optional, Iterable
import logging

from prefect.run_configs import DockerRun

from docker.types import HostConfig
from lume_services.services.scheduling.backends.backend import RunConfig
from lume_services.services.scheduling.backends.server import ServerBackend
from lume_services.utils import (
    SignatureModel,
    validate_and_compose_signature,
)

logger = logging.getLogger(__name__)


class DockerRunConfig(RunConfig):
    """Pydantic representation of a Docker Prefect run configuration:
    https://docs.prefect.io/api/latest/run_configs.html#dockerrun

    Attributes:
        image (str): Tag of image in which flow should run.
        host_config (BaseModel): SignatureModel generated from docker HostConfig type
            representing runtime args to be passed to Docker agent.
            Full documentation of args can be found here: https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_host_config
        ports (Optional[Iterable[int]]): An iterable of ports numbers to expose on
            container.

    """  # noqa

    image: str
    host_config: SignatureModel
    ports: Optional[Iterable[int]]

    @validator("host_config", pre=True)
    def validate_host_config(cls, v):
        """Composes a model for the Docker host configuration and applies any passed
        values.

        """

        if isinstance(v, (dict,)):
            return validate_and_compose_signature(HostConfig.__init__, **v)

        else:
            return v

    def build(self) -> DockerRun:
        """Method for converting to Prefect RunConfig type DockerRun.

        Returns:
            DockerRun

        """
        return DockerRun(self.dict(exclude_none=True))


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
