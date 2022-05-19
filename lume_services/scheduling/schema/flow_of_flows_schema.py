from pydantic import BaseModel, validator
from prefect.backend.flow import FlowView
from typing import List, Optional


# Pydantic schema describing flow of flows composition

class ParameterNotInFlowError(Exception):
    def __init__(
        self, parameter_name: str, flow_name: str):
        self.flow_name = flow_name
        self.parameter_name = parameter_name
        self.message = f"Parameter {self.parameter_name} not in flow {self.flow_name}."
        super().__init__(self.message)


class ParentFlowNotInFlowsError(Exception):
    def __init__(
        self, flow_name: str, flows: List[str]):
        self.flow_name = flow_name
        self.flows = flows
        self.message = f"Parent flow {self.flow_name} not in flows: {', '.join(self.flows)}."
        super().__init__(self.message)


class TaskNotInFlowError(Exception):
    def __init__(
        self, flow_name: str, task_name: str):
        self.flow_name = flow_name
        self.task_name = task_name
        self.message = f"Task {flow_name} not in flow {task_name}."
        super().__init__(self.message)

class ParameterMap(BaseModel):
    name: str
    parent_flow_name: str
    parent_task_name: str

class Flow(BaseModel):
    name: str
    project_name: str
    mapped_parameters: Optional[List[ParameterMap]]

class FlowOfFlows(BaseModel):
    name: str
    project_name: str
    composing_flows: List[Flow]

    def compose(self):
        flows = {}

        # validate composing flow existence
        for flow in self.composing_flows:
            deserialized_flow = FlowView.from_flow_name(flow.flow_name, project_name=flow.project_name, last_updated=True).flow()
            flows[flow] = {"flow": deserialized_flow, 
                            "parameters": deserialized_flow.parameters, 
                            "tasks": {
                                task.name: task for task in deserialized_flow.get_tasks()
                            }
                        }

        # validate flow parameters
        for flow in self.composing_flows:
            if flow.mapped_parameters is not None:
                for parameter in flow.mapped_parameters:

                    # validate parameter is in flow spec
                    # assumes this is dict, may be list
                    parameter_obj = flows[flow]["parameters"].get(parameter.name)
                    if parameter is None:
                        raise ParameterNotInFlowError(parameter.name, flow)

                    parent_flow = flows.get(parameter.parent_flow_name)
                    if parent_flow is None:
                        raise ParentFlowNotInFlowsError(parameter.parent_flow_name, list(flows.keys()))

                    task = parent_flow["tasks"].get(parameter.parent_task_name)
                    if task is None:
                        raise TaskNotInFlowError(parameter.parent_flow_name, parameter.parent_task_name)

                    # validate parameter type against result type
                    #parameter_obj.type
                    #task.result.