from datetime import datetime, timedelta
from pydantic import BaseModel, validator, Field
from prefect import Parameter
from prefect.backend.flow import FlowView
from prefect.run_configs import RunConfig
from typing import List, Optional, Dict, Literal, Any
from prefect import Flow as PrefectFlow

# Pydantic schema describing flow of flows composition


class MappedParameter(BaseModel):
    """There are three types of mapped parameters: file, db, and raw.

    file: File parameters are file outputs that will be loaded in downstream flows.
    Downstream loading must use the packaged `load_file` task in
    `lume_services.services.scheduling.tasks.file`.

    db: Database results ...

    raw: Raw values are passed from task output to parameter input.

    """

    parent_flow_name: str
    parent_task_name: str
    map_type: Literal["file", "db", "raw"] = "raw"


class RawMappedParameter(MappedParameter):
    map_type: str = Field("raw", const=True)


class FileMappedParameter(MappedParameter):
    map_type: str = Field("file", const=True)


class DBMappedParameter(MappedParameter):
    map_type: str = Field("db", const=True)
    attribute: str
    attribute_index: Optional[List[str]]


_string_to_mapped_parameter_type = {
    "db": DBMappedParameter,
    "file": FileMappedParameter,
    "raw": RawMappedParameter,
}


def _get_mapped_parameter_type(map_type: str):

    if map_type not in _string_to_mapped_parameter_type:
        raise ValueError("No mapped parameter type available for %s", map_type)

    return _string_to_mapped_parameter_type.get(map_type)


class Flow(BaseModel):
    name: str
    project_name: str
    parameters: Optional[Dict[str, Parameter]]
    mapped_parameters: Optional[Dict[str, MappedParameter]]
    prefect_flow: Optional[PrefectFlow]
    task_slugs: Optional[Dict[str, str]]
    labels: List[str] = ["lume-services"]

    class Config:
        arbitrary_types_allowed = True

    @validator("mapped_parameters", pre=True)
    def validate_mapped_parameters(cls, v):

        if v is None:
            return v

        mapped_parameters = {}

        for param_name, param in v.items():
            # persist instantiated params
            if isinstance(param, (MappedParameter,)):
                mapped_parameters[param_name] = param

            elif isinstance(param, (dict,)):
                # default raw
                if not param.get("map_type"):
                    mapped_parameters[param_name] = RawMappedParameter(**param)

                else:
                    mapped_param_type = _get_mapped_parameter_type(param["map_type"])
                    mapped_parameters[param_name] = mapped_param_type(**param)

            else:
                raise ValueError(
                    "Mapped parameters must be passed as instantiated \
                    MappedParameters or dictionary"
                )

        return mapped_parameters

    def load(self):
        flow = FlowView.from_flow_name(
            self.name, project_name=self.project_name, last_updated=True
        ).flow

        # assign attributes
        self.prefect_flow = flow
        self.task_slugs = {task.name: task.slug for task in flow.get_tasks()}
        self.parameters = {parameter.name: parameter for parameter in flow.parameters()}


class FlowConfig(BaseModel):
    image: Optional[str]
    env: Optional[List[str]]


class FlowRunConfig(BaseModel):
    flow_id: str
    poll_interval: timedelta = timedelta(seconds=10)
    scheduled_start_time: Optional[datetime]
    parameters: Optional[Dict[str, Any]]
    run_config: Optional[RunConfig]
    labels: Optional[List[str]]
    run_name: Optional[str]


def build_parameters(task, prefix: str = None):
    """

    Args:
        task: Task for which to build params
        prefix (str): Prefix to add to parameter names

    """

    params = {}

    for input_name, input in task.inputs.items():
        if not prefix:
            params[input_name] = Parameter(
                name=input_name, default=input["default"], required=input["required"]
            )
        else:
            params[f"{prefix}{input_name}"] = Parameter(
                name=f"{prefix}{input_name}",
                default=input["default"],
                required=input["required"],
            )

    return params
