from prefect import Flow
from pydantic import validator
from prefect.run_configs import LocalRun
from typing import Optional, Dict, Any
import logging
import warnings
import os

from lume_services.services.scheduling.backends import Backend, RunConfig
from lume_services.errors import (
    EmptyResultError,
    LocalBackendError,
    TaskNotCompletedError,
    TaskNotInFlowError,
)

logger = logging.getLogger(__name__)


class LocalRunConfig(RunConfig):
    """Local run configuration. If no directory is found at the filepath passed as
    working_dir, an error will be raised.

    Attributes:
        labels (Optional[Iterable[str]]): an iterable of labels to apply to this run
            config. Labels are string identifiers used by Prefect Agents for selecting
            valid flow runs when polling for work
        env (Optional[Dict[str, str]]): Dictionary of environment variables to use for
            run
        working_dir (Optional[str]): Working directory

    """

    env: Optional[Dict[str, str]]
    working_dir: Optional[str] = str(os.getcwd())

    @validator("working_dir", pre=True)
    def validate(cls, v):
        """Pydantic validator checking working directory existence"""
        if not os.path.isdir(v):
            raise FileNotFoundError("No directory found at %s", v)

        return v

    def build(self) -> LocalRun:
        """Method for converting to Prefect RunConfig type LocalRun.

        Returns:
            LocalRun

        """
        return LocalRun(**self.dict(exclude_none=True))


class LocalBackend(Backend):
    """Backend used for local execution. This backend will raise errors on any function
    calls requiring registration with the Prefect server.

    Attributes:
        run_config (Optional[LocalRunConfig]): Default configuration object for a given
            run.

    """

    def run(
        self,
        data: Dict[str, Any],
        run_config: LocalRunConfig = None,
        *,
        flow: Flow,
        **kwargs
    ) -> None:
        """Run flow execution. Does not return result.

        Args:
            labels (Optional[Iterable[str]]): an iterable of labels to apply to this run
                config. Labels are string identifiers used by Prefect Agents for
                selecting valid flow runs when polling for work.
            env (Optional[dict]): Additional environment variables to set on the job
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value.
            run_config (Optional[LocalRunConfig]): LocalRunConfig object to configure
                flow fun.
            flow (Flow): Prefect flow to execute.
            **kwargs: Keyword arguments to intantiate the LocalRunConfig.

        Raises:
            pydantic.ValidationError: Error validating run configuration.

        """

        if run_config is not None and len(kwargs):
            warnings.warn(
                "Both run_config and kwargs passed to LocalBackend.run. Flow\
                will execute using passed run_config."
            )

        if run_config is None:
            run_config = LocalRunConfig(**kwargs)

        # convert to Prefect LocalRun
        prefect_run_config = run_config.build()

        # apply run config
        flow.run_config = prefect_run_config
        flow.run(parameters=data)

    def run_and_return(
        self,
        data: Dict[str, Any],
        run_config: LocalRunConfig = None,
        task_name: str = None,
        *,
        flow: Flow,
        **kwargs
    ) -> Any:
        """Run flow execution and return result.

        Args:
            data (Optional[Dict[str, Any]]): Dictionary mapping flow parameter name to
                value.
            run_config (Optional[LocalRunConfig]): LocalRunConfig object to configure
                flow fun.
            task_name (Optional[str]): Name of task to return result. If no task slug
                is passed, will return the flow result.
            flow (Flow): Prefect flow to execute.
            **kwargs: Keyword arguments to intantiate the LocalRunConfig.

        Raises:
            pydantic.ValidationError: Error validating run configuration.
            EmptyResultError: No result is associated with the flow.
            TaskNotCompletedError: Result reference task was not completed.
            TaskNotInFlowError: Provided task slug not in flow.

        """
        if run_config is not None and len(kwargs):
            warnings.warn(
                "Both run_config and kwargs passed to LocalBackend.run. Flow\
                will execute using passed run_config."
            )

        if run_config is None:
            run_config = LocalRunConfig(**kwargs)

        # convert to Prefect LocalRun
        prefect_run_config = run_config.build()

        # apply run config
        flow.run_config = prefect_run_config
        flow_run = flow.run(parameters=data)

        result = flow_run.result

        if result is None:
            raise EmptyResultError

        task_to_slug_map = {task: slug for task, slug in flow.slugs.items()}
        # slug_to_task_map = {slug: task for task, slug in flow.slugs.items()}

        # account for task slug
        if task_name is not None:
            # get tasks
            tasks = flow.get_tasks(name=task_name)
            if not len(tasks):
                raise TaskNotInFlowError(flow.name, task_name)

            results = []
            for task in tasks:
                slug = task_to_slug_map.get(task)
                state = result[task]
                if not state.is_successful():
                    raise TaskNotCompletedError(
                        slug, flow_id="local_flow", flow_run_id="local_flow_run"
                    )

                res = state.result
                if res is None:
                    raise EmptyResultError("local_flow", "local_flow_run", slug)

                results.append(state.result)

            if len(tasks) == 1:
                return results[0]

            else:
                return results

        # else return dict of task slug to value
        else:
            return {
                slug: result[task].result for task, slug in task_to_slug_map.items()
            }

    def create_project(self, *args, **kwargs) -> None:
        """Raise LocalBackendError for calls to register_flow server-type method.

        Raises:
            LocalBackendError

        """
        raise LocalBackendError

    def register_flow(self, *args, **kwargs) -> None:
        """Raise LocalBackendError for calls to register_flow server-type method.

        Raises:
            LocalBackendError

        """
        raise LocalBackendError

    def load_flow(self, *args, **kwargs) -> None:
        """Raise LocalBackendError for calls to load_flow server-type method.

        Raises:
            LocalBackendError

        """
        raise LocalBackendError
