from pydantic import BaseModel
from prefect.run_configs import LocalRun
from typing import Optional, Dict
import logging


from lume_services.services.scheduling.backends import Backend


logger = logging.getLogger(__name__)


class LocalRunConfig(BaseModel):
    """Local run configuration.

    Attr:
        env (Optional[Dict[str, str]]): Dictionary of environment variables to use for \
            run
        working_dir (Optional[str]): Working directory

    """

    env: Optional[Dict[str, str]]
    working_dir: Optional[str]

    # VAlIDATE?
    #        # check working directory exists in file service
    #    if not file_service.dir_exists("local", self.working_dir):
    #        raise FileNotFoundError(f"Directory {self.working_dir} does not exist.")


#    labels: Optional[List[str]]


class LocalBackend(Backend):
    def get_run_config(
        self,
        run_config: LocalRunConfig,
    ):

        return LocalRun(**run_config)
