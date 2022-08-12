import os
import yaml
from pydantic import root_validator
from typing import get_args
from prefect.storage.docker import Docker
from prefect.tasks.prefect import (
    create_flow_run,
    wait_for_flow_run,
    get_task_run_result,
)
from prefect import Flow as PrefectFlow
from lume_services.flows.flow import Flow, MappedParameter
from lume_services.tasks import LoadDBResult
from lume_services.errors import (
    ParameterNotInFlowError,
    ParentFlowNotInFlowsError,
    TaskNotInFlowError,
)

from dependency_injector.wiring import Provide, inject
from lume_services.config import Context


from lume_services.services.scheduling import SchedulingService


class FlowOfFlows(Flow):
    composing_flows: dict

    class Config:
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    def validate(cls, values: dict):
        """Validate composing flow data against Prefect server."""
        flows = {}

        scheduling_service = None
        if "scheduling_service" in values:
            scheduling_service = values.pop("scheduling_service")

        # validate composing flow existence
        composing_flows = values.get("composing_flows")

        if isinstance(composing_flows, (dict,)):
            pass

        # iterate to create dict
        elif isinstance(composing_flows, (list,)):
            for flow in values["composing_flows"]:

                # compose flow objects
                flow_obj = Flow(
                    name=flow["name"],
                    project_name=flow["project_name"],
                    mapped_parameters=flow.get("mapped_parameters"),
                )

                # load Prefect parameters
                if scheduling_service is not None:
                    flow_obj.load_flow(scheduling_service=scheduling_service)
                else:
                    flow_obj.load_flow()

                flows[flow["name"]] = flow_obj

        # validate flow parameters
        for flow_name, flow in flows.items():
            if flow.mapped_parameters is not None:
                for parameter_name, parameter in flow.mapped_parameters.items():

                    # validate parameter is in flow spec
                    parameter_obj = flow.parameters.get(parameter_name)
                    if parameter_obj is None:
                        raise ParameterNotInFlowError(parameter_name, flow_name)

                    # validate parent flow is included in listed flows
                    parent_flow = flows.get(parameter.parent_flow_name)
                    if parent_flow is None:
                        raise ParentFlowNotInFlowsError(
                            parameter.parent_flow_name, list(flows.keys())
                        )

                    # validate task is in the parent flow
                    task = parent_flow.task_slugs.get(parameter.parent_task_name)

                    if task is None:
                        raise TaskNotInFlowError(
                            parameter.parent_flow_name, parameter.parent_task_name
                        )

        values["composing_flows"] = flows

        return values

    def compose(
        self,
        image_name: str,
        image_tag: str = "latest",
        local: bool = False,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
    ) -> PrefectFlow:
        """Compose Prefect flow from FlowOfFlows object. Uses base image assigned to
        the FlowOfFlows Object and builds a new Docker image containing the composite
        flow.


        Args:
            image_name (str): Name of generated image.
            image_tag (str): Tag of generated image.
            local (bool=False): Whether to use local images for the base image.


        Returns:
            PrefectFlow

        """

        # compose flow of flows
        with PrefectFlow(
            self.name,
            storage=Docker(
                base_image=self.image,
                image_name=image_name,
                image_tag=image_tag,
                local_image=local,
            ),
        ) as composed_flow:

            flow_runs = {}
            flow_waits = {}
            params = {}

            for i, (flow_name, flow) in enumerate(self.composing_flows.items()):

                # begin by creating parameters for all flow parameters
                flow_params = {}
                for param_name, param in flow.parameters.items():

                    # update name and slug
                    param.name = f"{flow_name}-{param_name}"
                    param.slug = f"{flow_name}-{param_name}"
                    params[param.name] = param

                    # use original param name for flow config
                    flow_params[param_name] = param

                # set up entry task
                if i == 0:
                    flow_run = create_flow_run(
                        flow_id=flow.flow_id,
                        parameters=flow_params,
                        labels=flow.labels,
                    )

                # setup other tasks
                elif i > 0:

                    # create references to parameters
                    upstream_flows = set()
                    if flow.mapped_parameters is not None:

                        # update flow_params with mapping
                        for param_name, mapped_param in flow.mapped_parameters.items():
                            task_slug = self.composing_flows[
                                mapped_param.parent_flow_name
                            ].task_slugs[mapped_param.parent_task_name]

                            task_run_result = get_task_run_result(
                                flow_runs[mapped_param.parent_flow_name], task_slug
                            )

                            # raw results and file results use their values directly
                            if mapped_param.map_type in ["raw", "file"]:
                                flow.prefect_flow.replace(
                                    flow_params.pop(param_name), task_run_result
                                )

                            # handle database results
                            elif mapped_param.map_type == "db":
                                load_db_result = LoadDBResult()
                                db_result = load_db_result(
                                    task_run_result,
                                    attribute_index=mapped_param.attribute_index,
                                )
                                flow.prefect_flow.replace(
                                    flow_params.pop(param_name), db_result
                                )

                                # add db result parameters to the task and create edge
                                for param in load_db_result.parameters:
                                    flow.prefect_flow.add_task(param)
                                    flow.prefect_flow.add_edge(
                                        param, load_db_result, mapped=True
                                    )

                            else:
                                # should never reach if instantiating MappedParameter
                                mapped_param_types = get_args(
                                    MappedParameter.__fields__["map_type"].type_
                                )
                                raise ValueError(
                                    f"Task type {mapped_param.map_type} not in task. \
                                        Allowed types: {mapped_param_types}."
                                )

                            # add flow to upstream
                            upstream_flows.add(mapped_param.parent_flow_name)

                        # add creation of flow run to flow
                        flow_run = create_flow_run(
                            flow_id=flow.flow_id,
                            parameters=flow_params,
                            labels=flow.labels,
                        )

                    # configure upstreams if any
                    for upstream in upstream_flows:
                        flow_run.set_upstream(flow_waits[upstream])

                flow_wait = wait_for_flow_run(flow_run, raise_final_state=True)
                flow_runs[flow_name] = flow_run
                flow_waits[flow_name] = flow_wait

        # validate flow of flows
        composed_flow.validate()

        # assign to obj
        self.prefect_flow = composed_flow
        self.image = f"{image_name}:{image_tag}"

        return composed_flow

    def compose_and_register(self) -> str:
        """Compose flow and register with project.

        Returns:
            str: Registered flow id

        """

        flow = self.compose()
        self.prefect_flow = flow
        return self.register(self.project_name)

    @classmethod
    @inject
    def from_yaml(
        cls,
        yaml_obj,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
    ):
        if os.path.exists(yaml_obj):
            flow_of_flow_config = yaml.safe_load(open(yaml_obj))

        else:
            flow_of_flow_config = yaml_obj

        # now validate
        return cls(**flow_of_flow_config, scheduling_service=scheduling_service)

    def _compose_local(self):
        """

        Note:
            Prefect 1.0 does not allow subflow run without previous registration with
            the server. This function is a workaround, but will be massively simplified
            once moved to Prefect 2.0, which does support direct subflow run.
        """
        ...
