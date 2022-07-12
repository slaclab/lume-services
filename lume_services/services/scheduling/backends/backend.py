from pydantic import BaseModel
from prefect.run_configs import RunConfig
from typing import Literal
from abc import ABC, abstractmethod


class Backend(BaseModel, ABC):
    backend_type: Literal["server", "cloud"] = "server"

    @abstractmethod
    def get_run_config(self) -> RunConfig:
        ...
