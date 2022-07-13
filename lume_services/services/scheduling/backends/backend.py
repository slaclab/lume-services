from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Iterable, Dict, Any, Union
from prefect import Flow
from pydantic import BaseModel


class RunConfig(BaseModel):
    """Pydantic representation of Prefect UniversalRunConfig:
    https://docs.prefect.io/api/latest/run_configs.html#universalrun


    Attributes:
        labels (Optional[Iterable[str]]): an iterable of labels to apply to this run
            config. Labels are string identifiers used by Prefect Agents for selecting
            valid flow runs when polling for work
        env (Optional[dict]): Additional environment variables to set on the job

    """

    labels: Optional[Iterable[str]]
    env: Optional[dict]


class Backend(BaseModel, ABC):
    """Abstract base class for Prefect backends. Backends handle Prefect interactions
    including running of flows, result handling, and flow registration with server
    backends.

    """

    @abstractmethod
    def register_flow(
        self,
        flow: Flow,
        project_name: str,
        image_tag: Optional[str],
    ) -> str:
        """Register a flow with Prefect. Backend implementations without server connecton
        should raise errors when this method is called.

        Args:
            flow (Flow): Prefect flow to register.
            project_name (str): Name of project to register flow to.
            image_tag (str): Name of Docker image to run flow inside.

        Returns:
            str: ID of registered flow.

        """
        ...

    @abstractmethod
    def load_flow(self, flow_name: str, project_name: str) -> Flow:
        """Load a Prefect flow object. Backend implementations without server connecton
        should raise errors when this method is called.

        Args:
            flow_name (str): Name of flow.
            project_name (str): Name of project flow is registered with.

        Returns:
            Flow: Prefect Flow object.

        """
        ...

    @abstractmethod
    def run(
        self,
        data: Optional[Dict[str, Any]],
        run_config: Optional[RunConfig],
        task_slug: Optional[str],
        **kwargs
    ) -> Union[str, None]:
        """Run a flow. Does not return result. Implementations should cover instantiation
        of run_config from kwargs as well as backend-specific kwargs.

        Args:
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value
            run_config (Optional[RunConfig]): RunConfig object to configure flow fun.
            task_slug (Optional[str]): Slug of task to return result. If no task slug
                is passed, will return the flow result.
            **kwargs: Keyword arguments for RunConfig init and backend-specific
                execution.

        Returns:
            Union[str, None]: Return run_id in case of server backend, None in the case
                of local execution.

        """
        ...

    @abstractmethod
    def run_and_return(
        self,
        data: Optional[Dict[str, Any]],
        run_config: Optional[RunConfig],
        task_slug: Optional[str],
        timeout: timedelta = timedelta(minutes=1),
        **kwargs
    ) -> Any:
        """Run a flow and return result. Implementations should cover instantiation of
        run_config from kwargs as well as backend-specific kwargs.

        Args:
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value
            run_config (Optional[RunConfig]): RunConfig object to configure flow fun.
            task_slug (Optional[str]): Slug of task to return result. If no task slug
                is passed, will return the flow result.
            timeout (timedelta): Time before stopping flow execution.
            **kwargs: Keyword arguments for RunConfig init and backend-specific
                execution.

        Returns:
            Any: Result of flow run.

        Raises:
            lume_services.errors.EmptyResultError: No result is associated with the
                flow.

        """
        ...
