from prefect import Client, config as prefect_config
from prefect.backend import FlowRunView
from typing import List

from pydantic import BaseModel
from datetime import datetime, timedelta
from pydantic import BaseSettings
from lume_services.services.scheduling.backends import Backend
from lume_services.services.scheduling.schema import FlowOfFlows, Flow

from typing import Optional
import yaml

import logging

logger = logging.getLogger(__name__)
# from prefect.schedules import CronSchedule
# weekday_schedule = CronSchedule(
#    "30 9 * * 1-5", start_date=pendulum.now(tz="US/Eastern")
# )


class FlowConfig(BaseModel):
    image: Optional[str]
    env: Optional[List[str]]


class FlowRunConfig(BaseModel):
    flow: Optional[Flow]
    #   parameters: ...
    #   run_config: RunConfig
    #   wait: ...
    #   new_flow_context: ...
    run_name: str = None
    scheduled_start_time: datetime = None
    poll_interval: timedelta = timedelta(seconds=10)


class PrefectGraphQLConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: str = "4201"
    host_port: str = "4201"
    debug: bool = False
    path: str = "/graphql/"


class PrefectServerConfig(BaseSettings):
    host = "http://localhost"
    port = "4200"
    host_port = "4200"
    host_ip = "127.0.0.1"

class PrefectConfig(BaseSettings):
    server: PrefectServerConfig = PrefectServerConfig()
    graphql: PrefectGraphQLConfig = PrefectGraphQLConfig()

    backend: Backend

    def apply(self):
        prefect_config.update(backend=self.backend.backend_type)
        prefect_config.server.update(**self.server.dict())
        prefect_config.server.graphql.update(**self.graphql.dict())
      #  prefect_config.cloud.update(api=self.api)
      #  prefect_config.cloud.update(graphql=self.graphql)

    #    prefect_config.server.ui.update(endpoint=self.ui)


class SchedulingService:
    """Scheduler handling job submission with Prefect."""

    def __init__(self, config: PrefectConfig):
        """Initialize PrefectScheduler using configuration, and file service.

        Args:
            config (PrefectConfig): Scheduling service client configuration

        """

        # apply Prefect config
        config.apply()

        self._config = config
        self._client = Client()

    def create_project(self, project_name: str) -> None:
        """Create a Prefect project.

        Args:
            project_name (str): Create a named Prefect project.

        """
        self._client.create_project(project_name=project_name)

    def register_flow(
        self,
        flow: Flow,
        project_name: str,
        image_tag: str,
    ) -> str:
        """Register a flow with Prefect.

        Args:
            flow (Flow): Prefect flow to register
            project_name (str): Name of project to register flow to
            image_tag (str): Name of Docker image to run flow inside

        Returns:
            ID of registered flow

        """
        flow.storage.image_tag = image_tag
        flow_id = flow.register(project_name=project_name)

        return flow_id

    def register_flow_of_flows(self, flow_of_flows: FlowOfFlows) -> str:
        """Register flow-of-flows in series.

        Args:
            flow_of_flows (FlowOfFlows): Instantiated flow of flows schema object

        """

        flow = flow_of_flows.compose_and_register()
        return flow

    def schedule_run(
        self,
        flow_id: str,
        data: dict = None,
        artifacts: List[str] = None,
        resource_requests: dict = None,
    ) -> str:
        """Schedule a run for a flow.

        Args:
            flow_id (str): Flow identifier
            data (dict): Dictionary mapping flow parameter to value
            mount_points (List[MountPoint]): List of points to mount for the job
            resource_requests (dict): Dictionary representative of resource request

        """

        # prefect.core.flow.Flow.run(parameters=None, run_on_schedule=None,
        #  runner_cls=None, **kwargs)

        run_config = self.config.backend_config.get_run_config()

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=run_config
        )

        return flow_run_id

    def schedule_and_return_run(
        self, flow_name: str, project_name: str, data: dict = None
    ):
        """

        Args:
            flow_name (str):
            project_name (str):
            data (dict): Dictionary mapping flow parameter name to value
        """

        schedule_run = ...
        # BROKEN

        # https://docs.prefect.io/api/latest/tasks/prefect.html?#wait-for-flow-run

        with Flow("schedule-run") as flow:
            flow_run_id = self._client.create_flow_run(
                flow_name=flow_name, project_name=project_name, parameters=data
            )

            slug = flow.serialize()["tasks"][0]["slug"]

            # slug should be absorbed into
            # child_data = get_task_run_result(flow_run_id, slug)
            # print(child_data)

            res = self._client.wait_for_flow_run(flow_run_id)
            # child_data = get_task_run_result(flow_run_id, slug)

        flow_runs = FlowRunView._query_for_flow_run(where={"flow_id": {"_eq": id}})


def load_flow_of_flows_from_yaml(yaml_obj):
    flow_of_flow_config = yaml.safe_load(yaml_obj)

    # now validate
    return FlowOfFlows(**flow_of_flow_config)
