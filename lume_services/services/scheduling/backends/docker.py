from pydantic import BaseModel, validator
from prefect.run_configs import DockerRun
from typing import Optional, Union, List
import logging

from docker.types import Mount, DeviceRequest, HostConfig
from lume_services.services.scheduling.backends import Backend, ServerRunConfig
from lume_services.utils import SignatureModel, validate_and_compose_signature

logger = logging.getLogger(__name__)

class DockerRunConfig(ServerRunConfig):
    """

   https://docker-py.readthedocs.io/en/stable/api.html#docker.api.container.ContainerApiMixin.create_host_config
    
    
    """
    host_config: BaseModel
    ports: Optional[List[int]]

    @validator("host_config", pre=True)
    def validate_host_config(cls, v):


        if isinstance(v, (dict,)):
            return validate_and_compose_signature(v)

        else:
            return v
    

class DockerBackend(Backend):
    run_config: DockerRunConfig
