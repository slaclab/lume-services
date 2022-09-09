from pydantic import BaseModel, root_validator
from typing import Optional, List
import importlib
from importlib_metadata import distribution
from dependency_injector.wiring import Provide

from lume_services.config import Context
from lume_services.errors import (
    FlowOfFlowsNotFoundError,
    DeploymentNotFoundError,
    DeploymentNotRegisteredError,
    NoFlowFoundError,
)

from lume_services.services.scheduling import SchedulingService
from lume_services.flows.flow import Flow
from lume_services.flows.flow_of_flows import FlowOfFlows
from lume_services.environment.solver import EnvironmentResolver
from lume_services.results import Result
from lume_services.results.utils import get_result_from_string
from lume_services.utils import get_callable_from_string
from lume_services.services.models.service import ModelDBService
from lume_services.services.models.db.schema import (
    DeploymentDependency as DeploymentDependencySchema,
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
    dependencies: Optional[List[DeploymentDependencySchema]]
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
            load_artifacts (bool): True requires local installation of package
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

                dependencies = model_db_service.get_dependencies(
                    deployment_id=deployment.deployment_id
                )

            except DeploymentNotFoundError:
                raise DeploymentNotRegisteredError(model_id=self.metadata.model_id)

        else:
            logger.info("Loading deployment %s", deployment_id)
            try:
                deployment = model_db_service.get_deployment(
                    model_id=self.metadata.model_id, deployment_id=deployment_id
                )
                dependencies = model_db_service.get_dependencies(
                    deployment_id=deployment.deployment_id
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
            )

        # if not flow of flow, use standard flow
        except FlowOfFlowsNotFoundError:
            flow = Flow(
                flow_id=flow_metadata.flow_id,
                name=flow_metadata.flow_name,
                project_name=flow_metadata.project_name,
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
            dependencies=dependencies,
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
        environment_resolver: EnvironmentResolver = Provide[
            Context.environment_resolver
        ],
    ):
        """

        Args:
            source_path (str): Path to local or remote source
            project_name (str): Name of Prefect project for storing flow.
            is_live (bool): Whether the model is live or not
            model_db_service (ModelDBService):
            environment_resolver (EnvironmentResolver):

        """

        source = environment_resolver.get_source(source_path)

        dependencies = environment_resolver.solve(source_path=source_path)

        logger.info("installing package")

        # in order to store the flow, we have to install
        environment_resolver.install(source_path=source_path)

        dist = distribution(source.name)

        flow_entrypoint = dist.entry_points.select(
            group="orchestration", name=f"{source.name}.flow"
        )
        if len(flow_entrypoint):
            prefect_flow = flow_entrypoint[0].load()

        else:
            raise NoFlowFoundError(source_path)

        flow = Flow(
            prefect_flow=prefect_flow, name=prefect_flow.name, project_name=project_name
        )

        deployment_id = model_db_service.store_deployment(
            model_id=self.metadata.model_id,
            version=source.version,
            source=source.path,
            is_live=is_live,
            sha256=source.checksum,
            image=scheduling_service.backend.config.default_image,
            package_import_name=source.name,
        )

        model_db_service.store_dependencies(dependencies, deployment_id=deployment_id)

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
    ):
        """

        Args:
            parameters (dict): Dictionary of values to pass to flow parameters.
            scheduling_service (SchedulingService): Instantiated SchedulingService
                object.

        """
        if self.deployment is None:
            self.load_deployment()

        pip_dependencies = " ".join(
            [
                dep.name
                for dep in self.deployment.dependencies
                if dep.dependency_type.type == "pip"
            ]
        )
        conda_dependencies = " ".join(
            [
                dep.name
                for dep in self.deployment.dependencies
                if dep.dependency_type.type == "conda"
            ]
        )

        run_config = scheduling_service.backend.run_config_type(
            env={
                "EXTRA_CONDA_PACKAGES": conda_dependencies,
                "EXTRA_PIP_PACKAGES": pip_dependencies,
                "LOCAL_CHANNEL_ONLY": scheduling_service.backend.config.isolated,
            },
            image=scheduling_service.backend.config.default_image,
        )

        self.deployment.flow.run(
            parameters,
            run_config=run_config,
            scheduling_service=scheduling_service,
        )

    def run_and_return(
        self,
        parameters: dict,
        task_name: str = None,
        scheduling_service: SchedulingService = Provide[Context.scheduling_service],
    ):
        """

        Args:
            parameters (dict)
            task_name (str)
            scheduling_service (SchedulingService): Instantiated SchedulingService
                object.

        """

        if self.deployment is None:
            self.load_deployment()

        pip_dependencies = " ".join(
            [
                dep.name
                for dep in self.deployment.dependencies
                if dep.dependency_type.type == "pip"
            ]
        )
        conda_dependencies = " ".join(
            [
                dep.name
                for dep in self.deployment.dependencies
                if dep.dependency_type.type == "conda"
            ]
        )

        # all of this should be inside the scheduling service and not here...

        # move all of scheduling service interface into  Flow and then dependencies
        run_config = scheduling_service.backend.run_config_type(
            env={
                "EXTRA_CONDA_PACKAGES": conda_dependencies,
                "EXTRA_PIP_PACKAGES": pip_dependencies,
                "LOCAL_CHANNEL_ONLY": scheduling_service.backend.config.isolated,
            },
            image=scheduling_service.backend.config.default_image,
        )

        self.deployment.flow.run_and_return(
            parameters,
            run_config=run_config,
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
            author (str):
            laboratory (str):
            facility (str):
            beampath (str):
            description (str):
            model_db_service (ModelDBService):

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
    ):

        # self.metadata.model_id

        ...
        # result_type = get_result_from_string  entrypoint???
        # result_type.load_from_query(


"""
    @inject
    def install(self, deployment_id: str = None, model_db_service:
        ModelDBService = Provide[Context.model_db_service]):
        global _model_registry

        if deployment_id is None:
            deployment = model_db_service.get_latest_deployment()

        else:
            deployment = model_db_service.get_deployment(deployment_id=deployment_id)


        # check if the package is installed...


        # check if this is in the registry
        if deployment.model_id not in _model_registry:

            model_loader = find_loader(deployment.package_name)

            if model_loader is not None:
                # install the deployment
                self._install(deployment)
                self._register_deployment(deployment)


            # loader found but missing from registry
            else:
                self._register_deployment(deployment)
                # check if correct version
                version = getattr(import_module(deployment.package_name), "__version__")
                if f"v{version}" != deployment.version:
                    self._install_deployment(deployment)



        return self._model_registry[deployment.model_id]


    def _install(deployment):
        # move to remote conda tarball

        env_url = deployment.url.replace("github", "raw.githubusercontent")

        version_url = deployment.url + f".git@{deployment.version}"
        env_url = deployment.url.replace("github", "raw.githubusercontent")
        env_url = env_url + f"/{deployment.version}/environment.yml"

        # get active env name
        env_name = os.environ["CONDA_DEFAULT_ENV"]

        # try install of environment
        try:
            output = subprocess.check_call(["conda", "env", "update",
            "--name",  env_name, "--file", env_url])

        except:
            print(f"Unable to install environment for {deployment.package_name}")
            sys.exit()

        # try install of package
        try:
            output = subprocess.check_call([sys.executable, '-m', 'pip',
            'install', f"git+{version_url}"])

        except:
            print(f"Unable to install {deployment.package_name}")
            sys.exit()


    def run_flow_and_return(self):
        ...



    # local methods
    def predict(self, *, model_id: int, input_variables):
        model = self.get_latest_model(model_id)
        return model.evaluate(input_variables)

    @staticmethod
    def _check_installed(...):
        return model_class()

    def get_latest_flow(self, model_id: int):
        # add function to get old deployment

        if self._model_registry.get(model_id) is not None:
            pass

        else:
            deployment = self._model_db.get_latest_deployment(model_id)
            model_info = self._get_model_info(deployment)

        return self._load_flow_from_entrypoint(model_info["flow_entrypoint"])


    def build_flow(self):
        ...

    # remote methods
    def predict(self, *, model_id, data):

        #only using latest for now
        flow_id = self._model_db.get_latest_model_flow(model_id)
        flow_run_id = self._scheduler.schedule_run(flow_id=flow_id, data=data)
        print(f"Run scheduled for model {model_id} with flow_run_id = {flow_run_id}")


    def save_model(self):
        ...

    def load_model(self):
        ...
"""
