from abc import abstractproperty
from datetime import timedelta
import warnings
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from prefect import Client, Flow, config as prefect_config
from prefect.run_configs import RunConfig as PrefectRunConfig
from prefect.backend import FlowRunView, FlowView
from prefect.backend.flow_run import watch_flow_run

from lume_services.services.scheduling.backends.backend import Backend, RunConfig
from lume_services.errors import TaskNotCompletedError, EmptyResultError

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


class ServerBackend(Backend):
    """Abstract backend used for connecting to a Prefect server.

    Attributes:
        config (PrefectConfig): Instantiated PrefectConfig object describing connection
            to Prefect server.
        default_image (str): Default image used for registering flow storage.
        _client (Client): Prefect client connection created on instantiation.

    """

    config: PrefectConfig
    default_image: str = Field(None, alias="image")
    _client: Client = Field(None, exclude=True)

    @abstractproperty
    def run_config_type(self) -> PrefectRunConfig:
        """Abstract property that must return the Prefect RunConfig type pertinent to
        the Backend implementation.

        """
        ...

    # abstractmethod _build_run_config

    def __init__(self, **data):
        """Initialization instantiates the pydantic model, applies the
        Prefect configuration, and initiazes the client connection.

        """
        super().__init__(**data)
        # apply config
        self.config.apply()
        # create client
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
        image_tag: Optional[str],
    ) -> str:
        """Register a flow with Prefect.

        Args:
            flow (Flow): Prefect flow to register
            project_name (str): Name of project to register flow to
            image_tag (str): Name of Docker image to run flow inside

        Returns:
            str: ID of registered flow

        """
        if not image_tag:
            image_tag = self.default_image_tag

        flow.storage.image_tag = image_tag
        flow_id = flow.register(project_name=project_name)

        return flow_id

    def load_flow(self, flow_name: str, project_name: str):
        """Load a Prefect flow object.

        Args:
            flow_name (str): Name of flow.
            project_name (str): Name of project flow is registered with.

        Returns:
            Flow: Prefect Flow object.

        """
        return FlowView.from_flow_name(
            flow_name, project_name=project_name, last_updated=True
        ).flow

    def run(
        self,
        flow_id: str,
        data: Optional[Dict[str, Any]],
        run_config: Optional[RunConfig],
        **kwargs
    ) -> str:
        """Create a flow run for a flow.

        Args:
            flow_id (str): Flow identifier
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value
            run_config (Optional[RunConfig]): RunConfig object to configure flow fun.
            **kwargs: Keyword arguments to intantiate the RunConfig.

        Returns:
            str: ID of flow run

        Raises:
            pydantic.errors.ClientError: if the GraphQL query is bad for any reason

        """
        if run_config is not None and len(kwargs):
            warnings.warn(
                "Both run_config and kwargs passed to Backend.run. Flow\
                will execute using passed run_config."
            )

        # convert LUME-services run config to appropriate Prefect RunConfig object
        if run_config is None:
            run_config = self.run_config_type(**kwargs)

        prefect_run_config = run_config.build()

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=prefect_run_config
        )

        return flow_run_id

    def run_and_return(
        self,
        data: Optional[Dict[str, Any]],
        run_config: Optional[RunConfig],
        task_slug: Optional[str],
        flow_id: str,
        timeout: timedelta = timedelta(minutes=1),
        cancel_on_timeout: bool = True,
        **kwargs
    ):
        """Create a flow run for a flow and return the result.

        Args:
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value
            run_config (Optional[RunConfig]): RunConfig object to configure flow fun.
            task_slug (Optional[str]): Slug of task to return result. If no task slug
                is passed, will return the flow result.
            flow_id (str): ID of flow to run.
            timeout (timedelta): Time before stopping flow execution.
            cancel_on_timeout (bool=True): Whether to cancel execution on timeout
                error.
            **kwargs: Keyword arguments to intantiate the RunConfig.

        Raises:
            pydantic.errors.ClientError: Bad GraphQL query.
            EmptyResultError: No result is associated with the flow.
            TaskNotCompletedError: Result reference task was not completed.
            RuntimeError: Flow did not complete within given timeout.

        """
        if run_config is not None and len(kwargs):
            warnings.warn(
                "Both run_config and kwargs passed to Backend.run. Flow\
                will execute using passed run_config."
            )

        # convert LUME-services run config to appropriate Prefect RunConfig object
        if run_config is None:
            run_config = self.run_config_type(**kwargs)

        prefect_run_config = run_config.build()

        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=prefect_run_config
        )

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        # watch flow run and stream logs until timeout
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

        # assume flow result, return all results
        else:
            if not flow_run.state._result:
                raise EmptyResultError(flow_id, flow_run_id)

            return flow_run.state._result.value
