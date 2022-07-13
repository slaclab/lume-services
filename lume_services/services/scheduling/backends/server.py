from datetime import timedelta
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, root_validator, Field

from prefect import Client, Flow, config as prefect_config
from prefect.backend import FlowRunView, FlowView
from prefect.backend.flow_run import watch_flow_run

from lume_services.services.files.service import FileService

from lume_services.services.scheduling.backends.backend import Backend, RunConfig, TaskNotCompletedError, EmptyResultError

import logging

logger = logging.getLogger(__name__)



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
    admin_secret: str = (
        ""  # a string. One will be automatically generated if not provided.
    )
    claims_namespace: str = "hasura-claims"
    graphql_url: str = (
        "http://${server.hasura.host}:${server.hasura.port}/v1alpha1/graphql"
    )
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
        prefect_config.update(
            backend=self.backend.backend_type, home_dir=self.home_dir, debug=self.debug
        )
        prefect_config.server.update(**self.server.dict())
        prefect_config.server.graphql.update(**self.graphql.dict())
        prefect_config.server.hasura.update(**self.hasura.dict())
        prefect_config.server.ui.update(**self.ui.dict())
        prefect_config.server.telemetry.update(**self.telemetry.dict())


# make this server and abstract more...
class ServerRunConfig(RunConfig):
    image: str


class ServerBackend(Backend):
    config: PrefectConfig
    default_image: str = Field(None, alias="image")

    _client: Client = Field(None, exclude=True)
    run_config: ServerRunConfig


    def __init__(self, **data):
        super().__init__(**data)
        # apply config
        self.config.apply()
        # create client
        self._client = Client()

    def register_flow(
            self,
            flow: Flow,
            project_name: str,
            image_tag: Optional[str],
        ) -> str:
        """Register a flow with Prefect.

        Args:
            flow (Flow): Prefect flow to register
            project_name (str): Name of project to register flow to
            image_tag (str): Name of Docker image to run flow inside

        Returns:
            ID of registered flow

        """
        if not image_tag:
            image_tag = self.default_image_tag
        
        flow.storage.image_tag = image_tag
        flow_id = flow.register(project_name=project_name)

        return flow_id

    def load_flow(self, name, project_name):
        return FlowView.from_flow_name(
            name, project_name=project_name, last_updated=True
        ).flow


    def run(
        self,
        flow_id: str,
        data: dict = None,
        **kwargs
    ) -> str:
        """Schedule a run for a flow.

        Args:
            flow_id (str): Flow identifier
            data (dict): Dictionary mapping flow parameter to value
            resource_requests (dict): Dictionary representative of resource request
            **kwargs: Prefect run config kwargs

        """
        run_config = self.run_config.copy(update=kwargs)

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=run_config
        )

        return flow_run_id

    def run_and_return(
        self,
        flow_id: str,
        task_slug: Optional[str],
        data: Optional[Dict[str, Any]],
        timeout: timedelta = timedelta(minutes=1),
        cancel_on_timeout: bool = True,
        **kwargs
    ):
        """

        Args:
            flow_id (str):
            project_name (str):
            task_slug (str): Slug of task to return
            data (dict): Dictionary mapping flow parameter name to value
            timeout ()
            cancel_on_timeout (bool=True): Whether to cancel execution on timeout error.
            **kwargs: Prefect run config kwargs
        """

        run_config = self.run_config.copy(update=kwargs)

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=run_config
        )

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        try:
            watch_flow_run(flow_run_id, stream_logs=True, max_duration=timeout)
        except RuntimeError as err:
            if cancel_on_timeout:
                self._client.cancel_flow_run()
            raise err

        # get task run
        if task_slug is not None:
            task_run = flow_run.get_task_run(task_slug=task_slug)
            if not task_run.state.is_successful():
                raise TaskNotCompletedError(task_slug, flow_id, flow_run_id)

            res = task_run.get_result()
            if res is None:
                raise EmptyResultError(flow_id, flow_run_id, task_slug)

        # assume flow result
        else:
            if not flow_run.state._result:
                raise EmptyResultError(flow_id, flow_run_id)

            return flow_run.state._result.value
