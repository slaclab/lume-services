from typing import Optional, List


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
    def __init__(self, flow_name: str, task_name: str):
        self.flow_name = flow_name
        self.task_name = task_name
        self.message = "Task %s not in flow %s."
        super().__init__(self.message, self.task_name, self.flow_name)


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
    def __init__(self, flow_id: str, flow_run_id: str):
        self.flow_id = flow_id
        self.flow_run_id = flow_run_id
        self.message = "Flow run: %s failed for flow_id: %s."
        super().__init__(self.message, self.flow_run_id, self.flow_id)


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
    def __init__(self):
        self.message = "Cannot run server-backend operation using LocalBackend."
        super().__init__(self.message)
