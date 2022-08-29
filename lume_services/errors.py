from typing import Optional, List, Literal
from pydantic import ValidationError
import os


class EnvironmentNotConfiguredError(Exception):
    """Error for marking unconfigured environment."""

    def __init__(self, env_vars, validation_error: ValidationError = None):
        self.env = dict(os.environ)
        self.env_vars = []

        for service in env_vars:
            self.env_vars += env_vars[service]

        self.missing_vars = [var for var in self.env_vars if var not in self.env]

        if validation_error is None:
            self.message = "Environment variables not defined: %s."
            super().__init__(self.message, ", ".join(self.missing_vars))

        else:
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


class DeploymentNotRegisteredError(Exception):
    """DeploymentNotRegisteredError indicates that a deployment was not found for the
    given model. If no deployment_id is passed, assumes that the user is attempting to
    load the latest deployment for that model.

    """

    def __init__(self, model_id: int, deployment_id: int = None):
        self.model_id = model_id
        self.deployment_id = deployment_id
        if deployment_id is None:
            self.message = "No deployment registered for model_id=%s."
            super().__init__(self.message, self.model_id)
        else:
            self.message = (
                "Deployment not found for model_id = %s with deploymend_id=%s"
            )
            super().__init__(self.message, self.model_id, self.deployment_id)


# Environment resolution


class WritePermissionError(Exception):
    """Error indicates missing write permission on a directory."""

    def __init__(self, directory: str):
        """
        Args:
            directory (str): Directory that is missing write permissions.

        """
        self.directory = directory
        self.user = os.getlogin()
        self.message = "User %s does not have write permissions for directory %s."

        super().__init__(self.message, self.user, self.directory)


class NoPackagesToInstallError(Exception):
    """Error indicates no packages were returned from environment resolution."""

    def __init__(self):
        self.message = "No packages were returned from environment resolution."
        super().__init__(self.message)


class UnableToInstallCondaDependenciesError(Exception):
    """Error indicating that certain conda dependencies were not installed during
    resolution.

    """

    def __init__(self, conda_dependencies: List[str]):
        """
        Args:
            conda_dependencies (List[str]): List of conda dependencies that were not
                installed.
        """
        self.deps = conda_dependencies

        self.message = "Unable to install conda dependencies: %s"
        super().__init__(self.message, ", ".join(self.deps))


class UnableToInstallPipDependenciesError(Exception):
    """Error indicating failed pip installation."""

    def __init__(
        self,
        pip_dependencies: List[str],
        python_version: float,
        platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"],
        e: Exception,
    ):
        """

        Args:
            pip_dependencies (List[str]): List of dependencies to be installed with pip
            python_version (float): Python version used for installation
            platform (Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]):
                Platform used for installation
            e (Exception): Exception raised from installation subprocess


        """
        self.deps = pip_dependencies
        self.python_version = python_version
        self.platform = platform

        self.message = "Unable to install pip dependencies: %s for python=%s on \
            platform=%s with error: %s"
        super().__init__(self.message, ", ".join(self.deps), self.python_version, e)


class UnableToIndexLocalChannelError(Exception):
    """Error raised when unable to index the local channel during conda environment
    resolution to local channel.

    """

    def __init__(self, local_channel_directory: str, return_code: int, output: str):
        """
        Args:
            local_channel_directory (str): Directory holding local channel.
            return_code (int): Return code of the subprocess.
            output (str): Output of the subprocess.


        """
        self.local_channel_directory = local_channel_directory
        self.return_code = return_code
        self.output = output

        self.message = "Unable to index local channel at %s. Subprocess returned \
            code %s with output: %s"
        super().__init__(
            self.message, self.local_channel_directory, self.return_code, self.output
        )


class MissingEnvironmentYamlError(Exception):
    """Error raised when a model package directory is missing an environment.yml
    spec.

    """

    def __init__(self, directory: str):
        """
        Args:
            directory (str): Local directory holding the package source.

        """
        self.directory = directory
        self.message = "Poorly formed package at %s. No Environment yaml provided."

        super().__init__(self.message, self.directory)


class NoCondaEnvironmentFoundError(Exception):
    """Error raised when CONDA_PREFIX is not defined."""

    def __init__(self):
        super().__init__("CONDA_PREFIX environment variabe is not set.")
