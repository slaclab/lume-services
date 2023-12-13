from datetime import datetime, timedelta
from pydantic import field_validator, ConfigDict, BaseModel
from typing import List, Optional, Dict, Literal, Any
from prefect import Flow as PrefectFlow
from dependency_injector.wiring import Provide, inject
from lume_services.config import Context

from lume_services.services.scheduling import SchedulingService


class MappedParameter(BaseModel):
    """There are three types of mapped parameters: file, db, and raw.

    file: File parameters are file outputs that will be loaded in downstream flows.
    Downstream loading must use the packaged `load_file` task in
    `lume_services.tasks.file`.

    db: Database results ...

    raw: Raw values are passed from task output to parameter input.

    Attr:
        parent_flow_name (str): Parent flow holding origin of mapped parameter.
        parent_task_name (str): Task whose result is mapped to the parameter.
        map_type (Literal["file", "db", "raw"]): Type of mapping describing the
            parameters.

    """

    parent_flow_name: str
    parent_task_name: str
    map_type: Literal["file", "db", "raw"] = "raw"


class RawMappedParameter(MappedParameter):
    """RawMappedParameters describe parameter mappings where the result of a task is
    used as the input to a parameter.

    Attr:
        parent_flow_name (str): Parent flow holding origin of mapped parameter.
        parent_task_name (str): Task whose result is mapped to the parameter.
        map_type (Literal["file", "db", "raw"] = "raw"): The "raw" map type describes
            the one-to-one result to parameter map.

    """

    map_type: Literal["raw"] = "raw"


class FileMappedParameter(MappedParameter):
    """FileMappedParameters describe files passed between different flows. Files are
    saved as json representations describing file type (and serialization) and
    filesystem information.

    Attr:
        parent_flow_name (str): Parent flow holding origin of mapped parameter.
        parent_task_name (str): Task whose result is mapped to the parameter.
        map_type (Literal["file", "db", "raw"] = "file"): The "file" map type describes
            the

    """

    map_type: Literal["file"] = "file"


class DBMappedParameter(MappedParameter):
    map_type: Literal["db"] = "db"
    attribute_index: Optional[list] = None


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
    """Interface to a workflow object.

    Attributes:
        name: Name of flow
        flow_id (Optional[str]): ID of flow as registered with Prefect. If running
            locally, this will be null.
        project_name (Optional[str]): Name of Prefect project with which the flow is
            registered. If running locally this will be null.
        parameters (Optional[Dict[str, Parameter]]): Dictionary of Prefect parameters
            associated with the flow.
        mapped_parameters (Optional[Dict[str, MappedParameter]]): Parameters to be
            collected from results of other flows.
        task_slugs (Optional[Dict[str, str]]): Slug of tasks associated with the
            Prefect flow.
        labels (List[str] = ["lume-services"]): List of labels to assign to flow when
            registering with Prefect backend. This label is used to assign agents that
            will manage deployment.
        image (str): Image inside which to run flow if deploying to remote backend.

    """

    name: str
    flow_id: Optional[str] = None
    project_name: Optional[str] = None
    prefect_flow: Optional[PrefectFlow] = None
    parameters: Optional[Dict[str, Any]] = None
    mapped_parameters: Optional[Dict[str, MappedParameter]] = None
    task_slugs: Optional[Dict[str, str]] = None
    labels: List[str] = ["lume-services"]
    image: str
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    @field_validator("mapped_parameters", mode="before")
    @classmethod
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

    @inject
    def load_flow(
        self,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
    ) -> None:
        """Loads Prefect flow artifact from the backend.

        Args:
            scheduling_service (SchedulingService): Scheduling service. If not
                provided, uses injected service.
        """
        flow_dict = scheduling_service.load_flow(self.name, self.project_name)

        flow = flow_dict["flow"]

        # assign attributes
        self.prefect_flow = flow
        self.task_slugs = {task.name: task.slug for task in flow.get_tasks()}
        self.parameters = {parameter.name: parameter for parameter in flow.parameters()}
        self.flow_id = flow_dict["flow_id"]

    @inject
    def register(
        self,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
    ) -> str:
        """Register flow with SchedulingService backend.

        Args:
            scheduling_service (SchedulingService): Scheduling service. If not
                provided, uses injected service.

        Returns:
            flow_id (str): ID of registered flow.

        """

        if self.prefect_flow is None:
            # attempt loading
            self.load_flow()

        self.flow_id = scheduling_service.register_flow(
            self.prefect_flow, self.project_name, labels=self.labels, image=self.image
        )

        self.parameters = {
            parameter.name: parameter for parameter in self.prefect_flow.parameters()
        }
        self.task_slugs = {
            task.name: task.slug for task in self.prefect_flow.get_tasks()
        }

        return self.flow_id

    def run(
        self,
        parameters,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
        **kwargs
    ):
        """Run the flow.

        Args:
            kwargs: Arguments passed to run config construction

        """
        scheduling_service.run(parameters=parameters, flow_id=self.flow_id, image=self.image, **kwargs)
#        if isinstance(scheduling_service.backend, (LocalBackend,)):
#            if self.prefect_flow is None:
#                self.load_flow()

#            scheduling_service.run(
#                parameters=parameters, flow=self.prefect_flow, **kwargs
#            )

#        elif isinstance(scheduling_service.backend, (ServerBackend,)):
#            scheduling_service.run(
#                parameters=parameters, flow_id=self.flow_id, image=self.image, **kwargs
#            )

    def run_and_return(
        self,
        parameters,
        task_name: Optional[str],
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
        **kwargs
    ):
        """Run flow and return result. Result will reference either passed task name or
        the result of all tasks.

        Args:
            kwargs: Arguments passed to run config construction


        """
        return scheduling_service.run_and_return(
            parameters=parameters,
            flow_id=self.flow_id,
            task_name=task_name,
            image=self.image,
            **kwargs
        )
#        if isinstance(scheduling_service.backend, (LocalBackend,)):
#            if self.prefect_flow is None:
#                self.load_flow()

#            return scheduling_service.run_and_return(
#                parameters=parameters,
#                flow=self.prefect_flow,
#                task_name=task_name,
#                image=self.image,
#                **kwargs
#            )

#        elif isinstance(scheduling_service.backend, (ServerBackend,)):
#            return scheduling_service.run_and_return(
#                parameters=parameters,
#                flow_id=self.flow_id,
#                task_name=task_name,
#                image=self.image,
#                **kwargs
#            )


# unused...
class FlowConfig(BaseModel):
    image: Optional[str] = None
    env: Optional[List[str]] = None


class FlowRunConfig(BaseModel):
    poll_interval: timedelta = timedelta(seconds=10)
    scheduled_start_time: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    run_config: Optional[Any] = None
    labels: Optional[List[str]] = None
    run_name: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)
