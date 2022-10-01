from abc import abstractproperty
from datetime import timedelta
import warnings
from typing import Dict, Any, List, Literal

from pydantic import BaseModel, Field

import prefect
from prefect import Client, Flow, config as prefect_config
from prefect.run_configs import RunConfig as PrefectRunConfig
from prefect.backend import FlowRunView, FlowView
from prefect.backend.flow_run import watch_flow_run

from lume_services.services.scheduling.backends.backend import Backend, RunConfig
from prefect.utilities.backend import save_backend
from lume_services.errors import (
    TaskNotCompletedError,
    EmptyResultError,
    TaskNotInFlowError,
    FlowFailedError,
)

import logging

logger = logging.getLogger(__name__)


class PrefectAgentConfig(BaseModel):
    host: str = "http://localhost"
    host_port: str = "5000"


class PrefectServerConfig(BaseModel):
    tag: str = "core-1.2.4"
    host: str = "http://localhost"
    host_port: str = "4200"
    host_ip: str = "127.0.0.1"


class PrefectUIConfig(BaseModel):
    host: str = "http://localhost"
    host_port: str = "8080"
    host_ip: str = "127.0.0.1"
    apollo_url: str = "http://localhost:4200/graphql"


class PrefectTelemetryConfig(BaseModel):
    enabled: bool = True


class PrefectConfig(BaseModel):
    # https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml
    server: PrefectServerConfig = PrefectServerConfig()
    ui: PrefectUIConfig = PrefectUIConfig()
    telemetry: PrefectTelemetryConfig = PrefectTelemetryConfig()
    agent: PrefectAgentConfig = PrefectAgentConfig()
    home_dir: str = "~/.prefect"
    debug: bool = False
    backend: Literal["server", "cloud"] = "server"
    default_image: str = Field("jgarrahan/lume-services-prefect:latest", alias="image")
    isolated: bool = False

    def apply(self):
        prefect_config.update(
            home_dir=self.home_dir, debug=self.debug, backend=self.backend
        )
        # must set endpoint because referenced by client
        prefect_config.server.update(
            endpoint=f"{self.server.host}:{self.server.host_port}", **self.server.dict()
        )
        prefect_config.server.ui.update(**self.ui.dict())
        prefect_config.server.telemetry.update(**self.telemetry.dict())
        # client requires api set
        prefect_config.cloud.update(api=f"{self.server.host}:{self.server.host_port}")
        save_backend(self.backend)
        return prefect_config


class ServerBackend(Backend):
    """Abstract backend used for connecting to a Prefect server.

    Prefect manages its own contexts for the purpose of registering flow objects
    etc. This introduced issues with management of clients, namely that even after
    setting the prefect configuration in the PrefectConfig.apply method, the
    original cloud context was still being used to construct the client. For this
    reason, all clients are constructed inside a context constructed from the backend
    configuration.


    Attributes:
        config (PrefectConfig): Instantiated PrefectConfig object describing connection
            to Prefect server.
        default_image (str): Default image used for registering flow storage.

    """

    config: PrefectConfig

    class Config:
        underscore_attrs_are_private = True

    @abstractproperty
    def run_config_type(self) -> PrefectRunConfig:
        """Abstract property that must return the Prefect RunConfig type pertinent to
        the Backend implementation.

        """
        ...

    def create_project(self, project_name: str) -> None:
        """Create a Prefect project.

        Args:
            project_name (str): Create a named Prefect project.

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason

        """
        with prefect.context(config=self.config.apply()):
            client = Client()
            client.create_project(project_name=project_name)

    def register_flow(
        self,
        flow: Flow,
        project_name: str,
        image: str = None,
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
            image (str): Name of Docker image to run flow inside. If not specified,
                this will use the default image packaged with this repository.
            build (bool): Whether the flows storage should be built prior to
                serialization. By default lume-services flows use the same
                image for execution with additional packages passed for installation
                configured at runtime.
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
        if not image:
            image = self.default_image

        # configure run config for backend
        run_config = self.run_config_type(image=image)
        flow.run_config = run_config.build()
        if labels is not None:
            logger.info(
                "Flow run config is not empty. Clearing existing labels and assigning \
                    new."
            )
            flow.run_config.labels = set(labels)

        flow.run_config.image_tag = image

        with prefect.context(config=self.config.apply()):
            flow_id = flow.register(
                project_name=project_name,
                build=build,
                set_schedule_active=set_schedule_active,
                version_group_id=version_group_id,
                no_url=no_url,
                idempotency_key=idempotency_key,
            )

        return flow_id

    def load_flow(self, flow_name: str, project_name: str) -> dict:
        """Load a Prefect flow object.

        Args:
            flow_name (str): Name of flow.
            project_name (str): Name of project flow is registered with.

        Returns:
            dict: Dictionary with keys "flow_id" and "flow"

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason

        """

        flow_view = FlowView.from_flow_name(
            flow_name, project_name=project_name, last_updated=True
        )
        with prefect.context(config=self.config.apply()):
            flow_view = FlowView.from_flow_name(
                flow_name, project_name=project_name, last_updated=True
            )
            return {"flow_id": flow_view.flow_id, "flow": flow_view.flow}

    def run(
        self,
        parameters: Dict[str, Any] = None,
        run_config: RunConfig = None,
        *,
        flow_id: str,
        **kwargs,
    ) -> str:
        """Create a flow run for a flow.

        Args:
            flow_id (str): Flow identifier
            parameters (Optional[Dict[str, Any]]): Dictionary mapping flow parameter
                name to value
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

        with prefect.context(config=self.config.apply()):
            client = Client()

            flow_view = FlowView.from_flow_id(flow_id)

            # convert LUME-services run config to appropriate Prefect RunConfig object
            if run_config is None:
                run_config = self.run_config_type(
                    env={"PREFECT__CONTEXT__PROJECT_NAME": flow_view.project_name},
                    **kwargs,
                )

            prefect_run_config = run_config.build()

            flow_run_id = client.create_flow_run(
                flow_id=flow_id, parameters=parameters, run_config=prefect_run_config
            )

        return flow_run_id

    def run_and_return(
        self,
        parameters: Dict[str, Any] = None,
        run_config: RunConfig = None,
        task_name: str = None,
        *,
        flow_id: str,
        timeout: timedelta = timedelta(minutes=1),
        cancel_on_timeout: bool = True,
        **kwargs,
    ):
        """Create a flow run for a flow and return the result.

        Args:
            parameters (Optional[Dict[str, Any]]): Dictionary mapping flow parameter
                name to value
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

        with prefect.context(config=self.config.apply()):
            client = Client()

            flow_view = FlowView.from_flow_id(flow_id)

            # convert LUME-services run config to appropriate Prefect RunConfig object
            if run_config is None:
                run_config = self.run_config_type(
                    env={"PREFECT__CONTEXT__PROJECT_NAME": flow_view.project_name},
                    **kwargs,
                )

            logger.info(
                "Creating Prefect flow run for %s with parameters %s and run_config %s",
                flow_id,
                parameters,
                run_config.json(),
            )

            prefect_run_config = run_config.build()

            flow_run_id = client.create_flow_run(
                flow_id=flow_id, parameters=parameters, run_config=prefect_run_config
            )

            # watch flow run and stream logs until timeout
            try:
                for log in watch_flow_run(
                    flow_run_id,
                    stream_states=True,
                    stream_logs=True,
                    max_duration=timeout,
                ):
                    logger.info(log)
            except RuntimeError as err:
                if cancel_on_timeout:
                    client.cancel_flow_run(flow_run_id=flow_run_id)
                raise err

            logger.debug("Watched flow completed.")
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
