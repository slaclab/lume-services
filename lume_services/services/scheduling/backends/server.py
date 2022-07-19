from abc import abstractproperty
from datetime import timedelta
import warnings
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, SecretStr

from prefect import Client, Flow, config as prefect_config
from prefect.run_configs import RunConfig as PrefectRunConfig
from prefect.backend import FlowRunView, FlowView
from prefect.backend.flow_run import watch_flow_run
from prefect.utilities import backend as backend_util

from lume_services.services.scheduling.backends.backend import Backend, RunConfig
from lume_services.errors import (
    TaskNotCompletedError,
    EmptyResultError,
    TaskNotInFlowError,
    FlowFailedError,
)

import logging

logger = logging.getLogger(__name__)


class PrefectPostgresConfig(BaseModel):
    host: str = "0.0.0.0"
    host_port: str = "5432"
    db: str
    user: str
    password: SecretStr = SecretStr("lume_services")
    data_path: str = "/tmp/lume/postgresql"


class PrefectGraphQLConfig(BaseModel):
    host: str = "0.0.0.0"
    host_port: str = "4201"


class PrefectServerConfig(BaseModel):
    tag: str = "core-1.2.4"
    host: str = "http://localhost"
    host_port: str = "4200"
    host_ip: str = "127.0.0.1"


class PrefectHasuraConfig(BaseModel):
    host: str = "localhost"
    host_port: str = "3000"
    claims_namespace: str = "hasura-claims"
    execute_retry_seconds: str = 10


class PrefectUIConfig(BaseModel):
    host: str = "http://localhost"
    host_port: str = "8080"
    host_ip: str = "127.0.0.1"
    apollo_url: str = "http://localhost:4200/graphql"


class PrefectTelemetryConfig(BaseModel):
    enabled: bool = True


class PrefectConfig(BaseModel):
    # https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml
    postgres: Optional[PrefectPostgresConfig]
    server: PrefectServerConfig = PrefectServerConfig()
    graphql: PrefectGraphQLConfig = PrefectGraphQLConfig()
    hasura: PrefectHasuraConfig = PrefectHasuraConfig()
    ui: PrefectUIConfig = PrefectUIConfig()
    telemetry: PrefectTelemetryConfig = PrefectTelemetryConfig()
    home_dir: str = "~/.prefect"
    debug: bool = False
    backend: str = "server"

    def apply(self):
        prefect_config.update(home_dir=self.home_dir, debug=self.debug)
        backend_util.save_backend(self.backend)
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

    class Config:
        underscore_attrs_are_private = True

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

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason

        """
        self._client.create_project(project_name=project_name)

    def register_flow(
        self,
        flow: Flow,
        project_name: str,
        image_tag: str = None,
        labels: List[str] = None,
        idempotency_key: str = None,
        version_group_id: str = None,
        build: bool = True,
        no_url: bool = False,
        set_schedule_active: bool = True,
    ) -> str:
        """Register a flow with Prefect.

        Args:
            flow (Flow): Prefect flow to register
            project_name (str): Name of project to register flow to
            image_tag (str): Name of Docker image to run flow inside
            build (bool): Whether the flows storage should be build prior to
                serialization. By default lume-services flows use the same
                image for execution with additional environment configured at runtime.
            labels (Optional[List[str]]): A list of labels to add to this Flow.
            idempotency_key (Optional[str]): a key that, if matching the most recent
                registration call for this flow group, will prevent the creation of
                another flow version and return the existing flow id instead.
            version_group_id (Optional[str]): The UUID version group ID to use for
                versioning this Flow in Cloud. If not provided, the version group ID
                associated with this Flow's project and name will be used.
            no_url (Optional[bool]): If True, the stdout from this function will not
                contain the URL link to the newly-registered flow in the UI
            set_schedule_active (Optional[bool]): If False, will set the schedule to
                inactive in the database to prevent auto-scheduling runs (if the Flow
                has a schedule)

        Returns:
            str: ID of registered flow

        Notes:
            prefect registration idempotency key omitted and version group...

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason

        """
        if not image_tag:
            image_tag = self.default_image_tag

        # flow.storage.image_tag = image_tag
        flow_id = flow.register(
            project_name=project_name,
            build=build,
            labels=labels,
            set_schedule_active=set_schedule_active,
            version_group_id=version_group_id,
            no_url=no_url,
            idempotency_key=idempotency_key,
        )

        return flow_id

    def load_flow(self, flow_name: str, project_name: str):
        """Load a Prefect flow object.

        Args:
            flow_name (str): Name of flow.
            project_name (str): Name of project flow is registered with.

        Returns:
            Flow: Prefect Flow object.

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason

        """
        return FlowView.from_flow_name(
            flow_name, project_name=project_name, last_updated=True
        ).flow

    def run(
        self,
        data: Dict[str, Any] = None,
        run_config: RunConfig = None,
        *,
        flow_id: str,
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
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            docker.errors.DockerException: Run configuration error for docker api.
            pydantic.ValidationError: Error validating run configuration.
            ValueError: Value error on flow run
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
        data: Dict[str, Any] = None,
        run_config: RunConfig = None,
        task_name: str = None,
        *,
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
            task_name (Optional[str]): Name of task to return result. If no task slug
                is passed, will return the flow result.
            flow_id (str): ID of flow to run.
            timeout (timedelta): Time before stopping flow execution.
            cancel_on_timeout (bool): Whether to cancel execution on timeout
                error.
            **kwargs: Keyword arguments to intantiate the RunConfig.

        Raises:
            EmptyResultError: No result is associated with the flow.
            TaskNotCompletedError: Result reference task was not completed.
            RuntimeError: Flow did not complete within given timeout.
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            docker.errors.DockerException: Run configuration error for docker api.
            pydantic.ValidationError: Error validating run configuration.
            TaskNotInFlowError: Provided task slug not in flow.
            ValueError: Value error on flow run
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

        logger.info(
            "Creating Prefect flow run for %s with parameters %s and run_config %s",
            flow_id,
            data,
            run_config.json(),
        )
        flow_run_id = self._client.create_flow_run(
            flow_id=flow_id, parameters=data, run_config=prefect_run_config
        )
        flow_view = FlowView.from_flow_id(flow_id)

        # watch flow run and stream logs until timeout
        try:
            for log in watch_flow_run(
                flow_run_id, stream_states=True, stream_logs=True, max_duration=timeout
            ):
                logger.info(log)
        except RuntimeError as err:
            if cancel_on_timeout:
                self._client.cancel_flow_run(flow_run_id=flow_run_id)
            raise err

        logger.info("Watched flow completed.")
        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        # check state
        if flow_run.state.is_failed():
            logger.exception(flow_run.state.message)
            raise FlowFailedError(
                flow_id=flow_run.flow_id,
                flow_run_id=flow_run.flow_run_id,
                exception_message=flow_run.state.message,
            )

        task_runs = flow_run.get_all_task_runs()

        # populate tasks
        results = {}
        for task_run in task_runs:
            slug = task_run.task_slug
            if not task_run.state.is_successful():
                raise TaskNotCompletedError(slug, flow_id, flow_run_id)

            try:
                res = task_run.get_result()
            # location is not set, no result
            except ValueError:
                res = None

            results[slug] = res

        # get task run
        if task_name is not None:
            # filter tasks based on name
            task_runs = {
                slug: res for slug, res in results.items() if task_name in slug
            }
            logger.debug(task_runs)

            if not len(task_runs):
                raise TaskNotInFlowError(
                    flow_name=flow_view.name,
                    project_name=flow_view.project_name,
                    task_name=task_name,
                )

            if len(task_runs) == 1:
                res = list(task_runs.values())[0]
                if res is None:
                    raise EmptyResultError(flow_id, flow_run_id, slug)

                return res

            else:
                return task_runs

        # assume flow result, return all results
        else:
            return results
