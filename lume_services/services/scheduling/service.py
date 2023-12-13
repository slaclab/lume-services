from typing import Optional, Dict, Any, Union, List
from prefect import Flow

import logging

logger = logging.getLogger(__name__)

# from prefect.schedules import CronSchedule
# weekday_schedule = CronSchedule(
#    "30 9 * * 1-5", start_date=pendulum.now(tz="US/Eastern")
# )


class SchedulingService:
    """Scheduler handling job submission with Prefect."""

    def __init__(self, backend: Any):
        """Initialize PrefectScheduler using configuration

        Args:
            backend (Backend): Scheduling service client configuration

        """

        self.backend = backend

    def create_project(self, project_name: str) -> None:
        """Create a Prefect project.

        Args:
            project_name (str): Create a named Prefect project.

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            lume_services.errors.LocalBackendError: Using local run configuration,
                no server backend methods permitted.

        """
        self.backend.create_project(project_name=project_name)

    def register_flow(
        self,
        flow: Flow,
        project_name: str,
        image: Optional[str],
        labels: Optional[List[str]],
    ) -> str:
        """Register a flow with Prefect. Backend implementations without server
        connecton should raise errors when this method is called.

        Args:
            flow (Flow): Prefect flow to register.
            project_name (str): Name of project to register flow to.
            image (str): Name of Docker image to run flow inside.

        Returns:
            str: ID of registered flow.

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            lume_services.errors.LocalBackendError: Using local run configuration, no
                server backend methods permitted.

        """
        return self.backend.register_flow(flow, project_name, image, labels=labels)

    def load_flow(self, flow_name: str, project_name: str) -> dict:
        """Load a Prefect flow object. Backend implementations without server connecton
        should raise errors when this method is called.

        Args:
            flow_name (str): Name of flow.
            project_name (str): Name of project flow is registered with.

        Returns:
            dict: Dictionary with keys "flow_id" and "flow"

        Raises:
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            lume_services.errors.LocalBackendError: Using local run configuration, no
                server backend methods permitted.

        """
        return self.backend.load_flow(flow_name, project_name)

    def run(
        self, parameters: Dict[str, Any], run_config=None, **kwargs
    ) -> Union[str, None]:
        """Run a flow. Does not return result. Implementations should cover
        instantiation of run_config from kwargs as well as backend-specific kwargs.

        Args:
            parameters (Dict[str, Any]): Dictionary mapping flow parameter
                name to value
            **kwargs: Keyword arguments for RunConfig init and backend-specific
                execution.

        Returns:
            Union[str, None]: Return run_id in case of server backend, None in the case
                of local execution.

        Raises:
            docker.errors.DockerException: Run configuration error for docker api.
            pydantic.ValidationError: Error validating run configuration.
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            ValueError: Value error on flow run

        """
        return self.backend.run(parameters, run_config=run_config, **kwargs)

    def run_and_return(
        self,
        parameters: Optional[Dict[str, Any]],
        run_config: Optional[Any] = None,
        task_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Run a flow and return result. Implementations should cover instantiation of
        run_config from kwargs as well as backend-specific kwargs.

        Args:
            parameters (Optional[Dict[str, Any]]): Dictionary mapping flow parameter
                name to value
            run_config (Optional[RunConfig]): RunConfig object to configure flow fun.
            task_name (Optional[str]): Name of task to return result. If no task slug
                is passed, will return the flow result.
            **kwargs: Keyword arguments for RunConfig init and backend-specific
                execution.

        Returns:
            Any: Result of flow run.

        Raises:
            lume_services.errors.EmptyResultError: No result is associated with the
                flow.
            docker.errors.DockerException: Run configuration error for docker api.
            pydantic.ValidationError: Error validating run configuration.
            prefect.errors.ClientError: if the GraphQL query is bad for any reason
            lume_services.errors.TaskNotInFlowError: Task slug does not exist in flow.
            lume_services.errors.TaskNotCompletedError: Result reference task was not
                completed.
            RuntimeError: Flow did not complete within given timeout.
            ValueError: Value error on flow run

        """
        return self.backend.run_and_return(parameters, run_config, task_name, **kwargs)
