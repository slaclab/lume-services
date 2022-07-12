from pydantic import BaseModel
from prefect.run_configs import RunConfig

from abc import ABC, abstractmethod


class Backend(BaseModel, ABC):
    backend_type: str = "server"

    @abstractmethod
    def get_run_config(self) -> RunConfig:
        ...
