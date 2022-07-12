from pydantic import BaseModel
from prefect.run_configs import DockerRun
from typing import Optional, Union, List
import logging

from dependency_injector.wiring import inject
from docker.types import Mount
from lume_services.services.scheduling.backends import Backend

logger = logging.getLogger(__name__)


class DockerResourceRequest(BaseModel):
    # CPU shares (relative weight).
    cpu_shares: int = None
    # CPUs in which to allow execution (0-3, 0,1).
    cpuset_cpus: int = None
    # Microseconds of CPU time that the container can get in a CPU period.
    cpu_quota: int = None
    # The length of a CPU period in microseconds.
    cpu_period: int = None
    # Memory limit. Accepts float values (which represent the memory limit of the
    # created container in bytes) or a string with a units identification char
    # (100000b, 1000k, 128m, 1g).
    mem_limit: Union[float, str] = None
    # Memory soft limit.
    mem_reservation: Union[float, str] = None
    # Tune a container’s memory swappiness behavior. Accepts number between 0 and 100.
    mem_swappiness: int = None
    #  Maximum amount of memory + swap a container is allowed to consume.
    memswap_limit: Union[str, int]


class DockerHostConfig(BaseModel):
    resource_request: Optional[DockerResourceRequest]
    privileged: bool = False
    read_only: bool = False
    mounts: Optional[List[Mount]]


# can extend to use
# https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_host_config
class DockerRunConfig(BaseModel):
    image: str
    env: Optional[dict]
    # labels:
    host_config: DockerHostConfig

    # can extend to use
    # https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_host_config


class DockerBackend(Backend):
    # default image
    default_image: str = None

    @inject
    def get_run_config(
        self,
        run_config: DockerRunConfig,
    ):

        return DockerRun(**run_config.dict(exclude_none=True))
