from typing import Optional, List
from pydantic import ValidationError
import os


class EnvironmentNotConfiguredError(Exception):
    """Error for marking unconfigured environment."""

    def __init__(self, env_vars, validation_error: ValidationError):
        self.env = dict(os.environ)
        self.env_vars = []

        for service in env_vars:
            self.env_vars += env_vars[service]

        self.missing_vars = [var for var in self.env_vars if var not in self.env]

        self.message = "%s. Evironment variables not defined: %s"

        super().__init__(
            self.message, str(validation_error), ", ".join(self.missing_vars)
        )


# Model errors


class FlowNotFoundError(Exception):
    def __init__(self, query):
        self.query = query
        self.message = "Flow not found for query: %s."
        super().__init__(self.message, self.query)


class FlowOfFlowsNotFoundError(Exception):
    def __init__(self, query):
        self.query = query
        self.message = "Flow not found for query: %s."
        super().__init__(self.message, self.query)


class ProjectNotFoundError(Exception):
    def __init__(self, query):
        self.query = query
        self.message = "Project not found for query: %s."
        super().__init__(self.message, self.query)


class ModelNotFoundError(Exception):
    def __init__(self, query):
        self.query = query
        self.message = "Model not found for query: %s."
        super().__init__(self.message, self.query)


class DeploymentNotFoundError(Exception):
    def __init__(self, query):
        self.query = query
        self.message = "Deployment not found for query: %s."
        super().__init__(self.message, self.query)


# Scheduling errors


class ParameterNotInFlowError(Exception):
    def __init__(self, parameter_name: str, flow_name: str):
        self.flow_name = flow_name
        self.parameter_name = parameter_name
        self.message = "Parameter %s not in flow %s."
        super().__init__(self.message, self.parameter_name, self.flow_name)


class ParentFlowNotInFlowsError(Exception):
    def __init__(self, flow_name: str, flows: List[str]):
        self.flow_name = flow_name
        self.flows = flows
        self.message = "Parent flow %s not in flows: %s"
        super().__init__(self.message, self.flow_name, ", ".join(self.flows))


class TaskNotInFlowError(Exception):
    def __init__(self, flow_name: str, project_name: str, task_name: str):
        self.flow_name = flow_name
        self.task_name = task_name
        self.project_name = project_name
        self.message = "Task %s not in flow %s."
        super().__init__(
            self.message, self.task_name, self.project_name, self.flow_name
        )


class TaskNotCompletedError(Exception):
    def __init__(self, task_slug: str, flow_id: str, flow_run_id: str):
        self.flow_id = flow_id
        self.flow_run_id = flow_run_id
        self.task_slug = task_slug
        self.message = (
            "Task with slug: %s not completed for flow_run_id: %s, flow_id: %s."
        )
        super().__init__(self.message, self.task_slug, self.flow_run_id, self.flow_id)


class FlowFailedError(Exception):
    def __init__(self, flow_id: str, flow_run_id: str, exception_message: str = None):
        self.flow_id = flow_id
        self.flow_run_id = flow_run_id
        self.exception_message = exception_message
        self.message = "Flow run: %s failed for flow_id: %s. %s"
        super().__init__(
            self.message, self.flow_run_id, self.flow_id, self.exception_message
        )


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


class LocalBackendError(Exception):
    """LocalBackendError indicates that a server-backend operation has been executed
    against the LocalBackend. Server-backend operations include flow registration and
    remote execution.

    """

    def __init__(self):
        self.message = "Cannot run server-backend operation using LocalBackend."
        super().__init__(self.message)
