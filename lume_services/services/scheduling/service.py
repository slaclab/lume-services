from datetime import timedelta
from typing import Optional, Dict, Any

from pydantic import BaseModel

from prefect import Client, Flow, config as prefect_config
from prefect.backend import FlowRunView, FlowView
from prefect.backend.flow_run import watch_flow_run

from lume_services.services.files.service import FileService

from lume_services.services.scheduling.backends.backend import Backend


import logging

logger = logging.getLogger(__name__)
# from prefect.schedules import CronSchedule
# weekday_schedule = CronSchedule(
#    "30 9 * * 1-5", start_date=pendulum.now(tz="US/Eastern")
# )


class TaskNotCompletedError(Exception):
    def __init__(self, task_slug: str, flow_id: str, flow_run_id: str):
        self.flow_id = flow_id
        self.flow_run_id = flow_run_id
        self.task_slug = task_slug
        self.message = (
            "Task with slug: %s not completed for flow_run_id: %s, flow_id: %s."
        )
        super().__init__(self.message, self.task_slug, self.flow_run_id, self.flow_id)


class EmptyResultError(Exception):
    def __init__(self, flow_id: str, flow_run_id: str, task_slug: Optional[str]):
        self.flow_id = flow_id
        self.flow_run_id = flow_run_id
        self.task_slug = task_slug
        if not self.task_slug:
            self.message = (
                "Task with slug: %s for flow run: %s of flow_id: %s has no result."
            )
            super().__init__(
                self.message, self.task_slug, self.flow_run_id, self.flow_id
            )

        else:
            self.message = "Flow run: %s of flow_id: %s has no result."
            super().__init__(self.message, self.flow_run_id, flow_id)


class SchedulingService:
    """Scheduler handling job submission with Prefect."""

    def __init__(self, backend: Backend):
        """Initialize PrefectScheduler using configuration

        Args:
            backend (Backend): Scheduling service client configuration

        """

        self.backend = backend

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
            ID of registered flow

        """
        if not image_tag:
            image_tag = self.backend.default_image_tag
        
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
        resource_requests: dict = None,
    ) -> str:
        """Schedule a run for a flow.

        Args:
            flow_id (str): Flow identifier
            data (dict): Dictionary mapping flow parameter to value
            resource_requests (dict): Dictionary representative of resource request

        """
        return self.backend.run(flow_id, data, resource_requests)

    def run_and_return(
        self,
        flow_id: str,
        task_slug: Optional[str],
        data: Optional[Dict[str, Any]],
        timeout: timedelta = timedelta(minutes=1),
        cancel_on_timeout: bool = True,
    ):
        """

        Args:
            flow_id (str):
            project_name (str):
            task_slug (str): Slug of task to return
            data (dict): Dictionary mapping flow parameter name to value
            timeout ()
            cancel_on_timeout (bool=True): Whether to cancel execution on timeout error.
        """
        return self.backend.run_and_return(flow_id, task_slug, data, timeout, cancel_on_timeout)


def _get_task_slugs_from_name(flow, name):

    return flow.get_tasks(name)


def _get_task_slugs_from_run_name(flow_run, name):
    return [
        task.task_slug for task in flow_run.get_all_task_runs() if task.name == name
    ]
