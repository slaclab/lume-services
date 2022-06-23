from pydantic import BaseModel
from prefect.run_configs import RunConfig

from abc import ABC, abstractmethod


class Backend(BaseModel, ABC):
    ...

    @abstractmethod
    def get_run(self) -> RunConfig:
        ...
