from prefect import Client, config as prefect_config
from prefect.backend import FlowRunView
from typing import List, Optional

from pydantic import BaseModel
from lume_services.services.data.files.service import FileService


from lume_services.services.scheduling.backends.backend import Backend

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lume_services.services.scheduling.flows import FlowOfFlows, Flow


import logging

logger = logging.getLogger(__name__)
# from prefect.schedules import CronSchedule
# weekday_schedule = CronSchedule(
#    "30 9 * * 1-5", start_date=pendulum.now(tz="US/Eastern")
# )

class PrefectGraphQLConfig(BaseModel):
    host: str = "0.0.0.0"
    port: str = "4201"
    host_port: str = "4201"
    debug: bool = False
    path: str = "/graphql/"


class PrefectServerConfig(BaseModel):
    host = "http://localhost"
    port = "4200"
    host_port = "4200"
    host_ip = "127.0.0.1"

class PrefectHasuraConfig(BaseModel):
    host: str = "localhost"
    port: str = "3000"
    host_port: str = "3000"
    admin_secret: str = "" # a string. One will be automatically generated if not provided.
    claims_namespace: str = "hasura-claims"
    graphql_url: str  = "http://${server.hasura.host}:${server.hasura.port}/v1alpha1/graphql"
    ws_url: str = "ws://${server.hasura.host}:${server.hasura.port}/v1alpha1/graphql"
    execute_retry_seconds: str = 10

class PrefectUIConfig(BaseModel):
    host: str = "http://localhost"
    port: str = "8080"
    host_port: str = "8080"
    host_ip: str = "127.0.0.1"
    endpoint: str = "${server.ui.host}:${server.ui.port}"
    apollo_url: str = "http://localhost:4200/graphql"

class PrefectTelemetryConfig(BaseModel):
    enabled: bool = True


class PrefectConfig(BaseModel):
    # https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml
    server: PrefectServerConfig = PrefectServerConfig()
    graphql: PrefectGraphQLConfig = PrefectGraphQLConfig()
    hasura: PrefectHasuraConfig = PrefectHasuraConfig()
    ui: PrefectUIConfig = PrefectUIConfig()
    telemetry: PrefectTelemetryConfig = PrefectTelemetryConfig()
    home_dir: str = "~/.prefect"
    backend: Backend
    debug: bool = False

    def apply(self):
        prefect_config.update(backend=self.backend.backend_type, home_dir=self.home_dir, debug=self.debug)
        prefect_config.server.update(**self.server.dict())
        prefect_config.server.graphql.update(**self.graphql.dict())
        prefect_config.server.hasura.update(**self.hasura.dict())
        prefect_config.server.ui.update(**self.ui.dict())
        prefect_config.server.telemetry.update(**self.telemetry.dict())

class SchedulingService:
    """Scheduler handling job submission with Prefect."""

    def __init__(self, config: PrefectConfig, file_service: Optional[FileService]):
        """Initialize PrefectScheduler using configuration

        Args:
            config (PrefectConfig): Scheduling service client configuration
            file_service (FileService): File service used for fetching resources

        """

        # apply Prefect config
        config.apply()

        self._config = config
        self._client = Client()
        self._file_service = file_service

    def create_project(self, project_name: str) -> None:
        """Create a Prefect project.

        Args:
            project_name (str): Create a named Prefect project.

        """
        self._client.create_project(project_name=project_name)

    def register_flow(
        self,
        flow: "Flow",
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

    def register_flow_of_flows(self, flow_of_flows: "FlowOfFlows") -> str:
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
        resource_requests: dict = None,
    ) -> str:
        """Schedule a run for a flow.

        Args:
            flow_id (str): Flow identifier
            data (dict): Dictionary mapping flow parameter to value
            resource_requests (dict): Dictionary representative of resource request

        """

        # prefect.core.flow.Flow.run(parameters=None, run_on_schedule=None,
        #  runner_cls=None, **kwargs)

        run_config = self.config.backend_config.get_run_config(file_service=self.file_service)

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=run_config
        )

        return flow_run_id

    def schedule_and_return_run(
        self,        
        flow_id: str,
        data: dict = None,
    ):
        """

        Args:
            flow_name (str):
            project_name (str):
            data (dict): Dictionary mapping flow parameter name to value
        """

        schedule_run = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=run_config
        )
        
        ...
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

