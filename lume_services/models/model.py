from pydantic import BaseModel, root_validator
from typing import Optional, List
from importlib_metadata import distribution
from dependency_injector.wiring import Provide

from lume_services.config import Context
from lume_services.environment.solver import Source
from lume_services.errors import (
    FlowOfFlowsNotFoundError,
    DeploymentNotFoundError,
    DeploymentNotRegisteredError,
    NoFlowFoundError,
)

from lume_services.services.scheduling import SchedulingService
from lume_services.flows.flow import Flow
from lume_services.flows.flow_of_flows import FlowOfFlows
from lume_services.results import Result
from lume_services.results.utils import get_result_from_string
from lume_services.services.models.service import ModelDBService
from lume_services.services.models.db.schema import (
    Model as ModelSchema,
    Deployment as DeploymentSchema,
    Project as ProjectSchema,
)
from lume_services.services.results import ResultsDBService


import logging

logger = logging.getLogger(__name__)


class Project(BaseModel):
    metadata: Optional[ProjectSchema]

    class Config:
        arbitrary_types_allowed = True


class Deployment(BaseModel):
    metadata: Optional[DeploymentSchema]
    project: Optional[Project]
    flow: Optional[Flow]  # defined using template entrypoints
    model_type: Optional[type]

    class Config:
        arbitrary_types_allowed = True
        validate_on_assignment = True


class Model(BaseModel):
    """Class used for interacting with models."""

    metadata: Optional[ModelSchema]
    deployment: Optional[Deployment]
    results: Optional[List[Result]]

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
        **values,
    ):
        values["model_db_service"] = model_db_service
        super().__init__(**values)

    @root_validator(pre=True)
    def load_model_data(cls, values):
        """Loads relevant sqlalchemy objects from the database."""
        model_db_service = None
        if "model_db_service" in values:
            model_db_service = values.pop("model_db_service")

        deployment_id = values.get("deployment_id")
        model_id = values.get("model_id")

        new_values = {}
        if not model_id:
            if values.get("metadata"):
                new_values["metadata"] = values["metadata"]

            else:
                if not values.get("deployment_id"):
                    raise ValueError(
                        "Either model_id or deployment_id must be passed to Model on \
                            construction."
                    )

                deployment_id = values.get("deployment_id")
                deployment = None
                if deployment_id is not None:
                    logger.info("Getting deployment %s for model_id %s.", deployment_id)
                    deployment = model_db_service.get_deployment(
                        deployment_id=deployment_id
                    )

                # if a deployment is found, load the deployment
                if deployment is not None:
                    new_values["deployment"] = {"metadata": deployment}
                    flow = model_db_service.get_flow(deployment_id=deployment_id)
                    new_values["deployment"]["project"] = flow.project

                    # check if flow is flow of flows
                    try:
                        flows = model_db_service.get_flow_of_flows(
                            parent_flow_id=flow.flow_id
                        )

                        # TODO: Add mapped parameters
                        composing_flows = [
                            {"name": flow.name, "project_name": flow.project_name}
                            for flow in flows
                        ]

                        new_values["deployment"]["flow"] = FlowOfFlows(
                            flow_id=flow.flow_id,
                            name=flow.flow_name,
                            project_name=flow.project_name,
                            composing_flows=composing_flows,
                        )

                    # if not flow of flow, use standard flow
                    except FlowOfFlowsNotFoundError:
                        new_values["deployment"]["flow"] = Flow(
                            flow_id=flow.flow_id,
                            name=flow.flow_name,
                            project_name=flow.project_name,
                        )

        else:
            model = model_db_service.get_model(model_id=model_id)
            new_values["metadata"] = model

        return new_values

    @classmethod
    def register_model(
        cls,
        author,
        laboratory,
        facility,
        beampath,
        description,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        model_id = model_db_service.store_model(
            author=author,
            laboratory=laboratory,
            facility=facility,
            beampath=beampath,
            description=description,
        )
        # load model from service
        model = model_db_service.get_model(model_id=model_id)
        return cls(metadata=model)

    def load_deployment(
        self,
        deployment_id: int = None,
        load_artifacts: bool = False,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        """If no deployment_id passed, assume loading the latest deployment.


        Args:
            deployment_id (int):
            load_artifacts (bool): True requires local installation of package
            model_db_service (ModelDBService):
        Raises:
            DeploymentNotRegisteredError: A matiching deployment cannot be found for
                this model.


        """
        # load deployment
        if deployment_id is None:
            logger.info("Loading latest deployment.")
            try:
                deployment = model_db_service.get_latest_deployment(
                    model_id=self.metadata.model_id
                )

            except DeploymentNotFoundError:
                raise DeploymentNotRegisteredError(model_id=self.metadata.model_id)

        else:
            logger.info("Loading deployment %s", deployment_id)
            try:
                deployment = model_db_service.get_deployment(
                    model_id=self.metadata.model_id, deployment_id=deployment_id
                )

                logger.info("Deployment loaded.")

            except DeploymentNotFoundError:
                raise DeploymentNotRegisteredError(
                    model_id=self.metadata.model_id, deployment_id=deployment_id
                )

        # load flow
        logger.debug("Loading flow for deployment %s", deployment.deployment_id)
        flow_metadata = model_db_service.get_flow(
            deployment_id=deployment.deployment_id
        )

        project = model_db_service.get_project(project_name=flow_metadata.project_name)
        # check if flow is flow of flows
        try:
            flows = model_db_service.get_flow_of_flows(
                parent_flow_id=flow_metadata.flow_id
            )

            # TODO: Add mapped parameters
            composing_flows = [
                {"name": flow.name, "project_name": flow.project_name} for flow in flows
            ]

            flow = FlowOfFlows(
                flow_id=flow_metadata.flow_id,
                name=flow_metadata.flow_name,
                project_name=flow_metadata.project_name,
                composing_flows=composing_flows,
                image=deployment.image,
            )

        # if not flow of flow, use standard flow
        except FlowOfFlowsNotFoundError:
            flow = Flow(
                flow_id=flow_metadata.flow_id,
                name=flow_metadata.flow_name,
                project_name=flow_metadata.project_name,
                image=deployment.image,
            )

        model_type = None
        if load_artifacts:
            dist = distribution(deployment.package_import_name)

            model_entrypoint = dist.entry_points.select(
                group="orchestration", name=f"{deployment.package_import_name}.model"
            )
            if len(model_entrypoint):
                model_type = model_entrypoint[0].load()

            flow_entrypoint = dist.entry_points.select(
                group="orchestration", name=f"{deployment.package_import_name}.flow"
            )
            if len(flow_entrypoint):
                flow.prefect_flow = flow_entrypoint[0].load()

            else:
                raise NoFlowFoundError(deployment.package_import_name)

        self.deployment = Deployment(
            metadata=deployment,
            project={"metadata": project},
            flow=flow,
            model_type=model_type,
        )

    def store_deployment(
        self,
        source_path: str,
        project_name: str,
        is_live: bool = True,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        """

        Args:
            source_path (str): Path to local or remote source
            project_name (str): Name of Prefect project for storing flow.
            is_live (bool): Whether the model is live or not
            model_db_service (ModelDBService):

        """

        logger.info("installing package")

        # in order to store the flow, we have to install
        source = Source(path=source_path)
        source.install()

        dist = distribution(source.name)

        flow_entrypoint = dist.entry_points.select(
            group="orchestration", name=f"{source.name}.flow"
        )
        if len(flow_entrypoint):
            prefect_flow = flow_entrypoint[0].load()

        else:
            raise NoFlowFoundError(source_path)

        flow = Flow(
            prefect_flow=prefect_flow,
            name=prefect_flow.name,
            project_name=project_name,
            image=source.image,
        )

        deployment_id = model_db_service.store_deployment(
            model_id=self.metadata.model_id,
            version=source.version,
            source=source.path,
            is_live=is_live,
            sha256=source.checksum,
            image=source.image,
            package_import_name=source.name,
        )

        # register flow
        prefect_flow_id = flow.register(scheduling_service=scheduling_service)

        _ = model_db_service.store_flow(
            deployment_id=deployment_id,
            flow_id=prefect_flow_id,
            flow_name=prefect_flow.name,
            project_name=project_name,
        )

        logger.info("Loading deployment %s", deployment_id)

        # now load to update object
        self.load_deployment(
            deployment_id=deployment_id,
            load_artifacts=True,  # want to load flow and model class
        )

    def run(
        self,
        parameters: dict,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
        **kwargs,
    ):
        """

        Args:
            parameters (dict): Dictionary of values to pass to flow parameters.
            scheduling_service (SchedulingService): Instantiated SchedulingService
                object.
            kwargs: Arguments passed to run config construction


        """
        if self.deployment is None:
            self.load_deployment()

        self.deployment.flow.run(
            parameters, scheduling_service=scheduling_service, **kwargs
        )

    def run_and_return(
        self,
        parameters: dict,
        task_name: str = None,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
        **kwargs,
    ):
        """

        Args:
            parameters (dict)
            task_name (str)
            scheduling_service (SchedulingService): Instantiated SchedulingService
                object.
            kwargs: Arguments passed to run config construction


        """

        if self.deployment is None:
            self.load_deployment()

        return self.deployment.flow.run_and_return(
            parameters,
            task_name=task_name,
            scheduling_service=scheduling_service,
        )

    @classmethod
    def create_model(
        cls,
        author: str,
        laboratory: str,
        facility: str,
        beampath: str,
        description: str,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        """

        Args:
            author (str): Model author
            laboratory (str): Laboratory name
            facility (str): Laboratory facility name
            beampath (str): Beampath identifier
            description (str): Brief description of model
            model_db_service (ModelDBService): Model database service. This will be
                injected if not passed.

        """

        model_id = model_db_service.store_model(
            author=author,
            laboratory=laboratory,
            facility=facility,
            beampath=beampath,
            description=description,
        )

        return cls(model_id=model_id, model_db_service=model_db_service)

    def get_results(
        self,
        results_db_service: ResultsDBService = Provide[Context.results_db_service],
        model_db_service: ModelDBService = Provide[Context.model_db_service],
        all_deployments: bool = False,
        query: Optional[dict] = None,
    ):
        """Query model results.

        Args:
            model_db_service (ModelDBService): Model database service. Injected if
                not provided.
            results_db_service (ResultsDBService): Results database service. Injected
                if not provided.
            all_deployments (bool): The default behavior is to
                load the active deployment. If True is passed, the results from all
                deployments will be returned.
            query (Optional[dict]): Query formatted using pymongo convention

        """

        if query is None:
            query = {}

        if not all_deployments:
            query.update({"flow_id": self.deployment.flow.flow_id})

        else:
            # require all flows
            # these queries are bad. A join should be used instead, but going
            # with it because of time constraints.
            flow_ids = []
            deployments = model_db_service.get_deployments(
                model_id=self.metadata.model_id
            )
            for deployment in deployments:
                flow = model_db_service.get_flow(deployment_id=deployment.deployment_id)
                flow_ids.append(flow.flow_id)

        results = results_db_service.find_all(query=query)
        res_objs = []
        for res in results:
            result_type_string = res.pop("result_type_string")
            res_type = get_result_from_string(result_type_string)
            res_objs.append(res_type(**res))

        return res_objs

    def get_result_df(
        self,
        results_db_service: ResultsDBService = Provide[Context.results_db_service],
        model_db_service: ModelDBService = Provide[Context.model_db_service],
        all_deployments: bool = False,
        query: Optional[dict] = None,
    ):
        """Get results and format into a dataframe.

        Args:
            query: Query formatted using Pymongo convention
            model_db_service (ModelDBService): Model database service. Injected if
                not provided.
            results_db_service (ResultsDBService): Results database service. Injected
                if not provided.
            deployments (bool): The default behavior is to
                load the active deployment. If True is passed, the results from all
                deployments will be returned.

        """

        if query is None:
            query = {}

        if not all_deployments:
            query.update({"flow_id": self.deployment.flow.flow_id})

        else:
            # require all flows
            # these queries are bad. A join should be used instead, but going
            # with it because of time constraints.
            flow_ids = []
            deployments = model_db_service.get_deployments(
                model_id=self.metadata.model_id
            )
            for deployment in deployments:
                flow = model_db_service.get_flow(deployment_id=deployment.deployment_id)
                flow_ids.append(flow.flow_id)

        df = results_db_service.load_dataframe(query=query)
        return df
