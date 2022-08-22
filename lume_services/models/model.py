from pydantic import BaseModel, root_validator, create_model
import os
import sys
import subprocess
from typing import Optional, List
from importlib import import_module, find_loader
from importlib_metadata import distribution
from dependency_injector.wiring import Provide, inject
from datetime import datetime

from lume_services.config import Context
from lume_services.errors import (
    FlowOfFlowsNotFoundError,
    DeploymentNotFoundError,
    DeploymentNotRegisteredError,
)
from lume_services.flows.flow import Flow
from lume_services.flows.flow_of_flows import FlowOfFlows
from lume_services.results import Result
from lume_services.services.models.service import ModelDBService
from lume_services.services.models.db.schema import (
    Model as ModelSchema,
    Deployment as DeploymentSchema,
    Project as ProjectSchema,
)


import logging

logger = logging.getLogger(__name__)

# maintain cache of loaded models
_model_registry = {}


class Project(BaseModel):
    metadata: Optional[ProjectSchema]

    class Config:
        arbitrary_types_allowed = True


class Deployment(BaseModel):
    metadata: Optional[DeploymentSchema]
    project: Optional[Project]

    class Config:
        arbitrary_types_allowed = True


class Model(BaseModel):
    """Class used for interacting with models."""

    metadata: Optional[ModelSchema]
    deployment: Optional[Deployment]
    model_obj: Optional[BaseModel]  # lume-model model
    flow: Optional[Flow]  # local flow
    results: Optional[List[Result]]

    class Config:
        arbitrary_types_allowed = True

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
                        "Either model_id or deployment_id must be passed to Model on construction."
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
                    flow = model_db_service.get_deployment_flow(
                        deployment_id=deployment_id
                    )
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

                        values["flow"] = FlowOfFlows(
                            flow_id=flow.flow_id,
                            name=flow.flow_name,
                            project_name=flow.project_name,
                            composing_flows=composing_flows,
                        )

                    # if not flow of flow, use standard flow
                    except FlowOfFlowsNotFoundError:
                        values["flow"] = Flow(
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

    def register_deployment(
        self,
        project_name,
        version,
        asset_dir,
        sha256,
        source,
        is_live,
        image,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        # register the deployment
        deployment_id = model_db_service.store_deployment(
            model_id=self.metadata.model_id,
            version=version,
            asset_dir=asset_dir,
            sha256=sha256,
            source=source,
            is_live=is_live,
            image=image,
        )

        # load the flow

    def load_model(self):
        if self.deployment is None:
            raise ValueError()

    def load_deployment(
        self,
        deployment_id: int = None,
        model_db_service: ModelDBService = Provide[Context.model_db_service],
    ):
        """If no deployment_id passed, assume loading the latest deployment.

        Raises:
            DeploymentNotRegisteredError: A matiching deployment cannot be found for
                this model.


        """
        # load deployment
        if deployment_id is None:
            try:
                deployment = model_db_service.get_latest_deployment(
                    model_id=self.metadata.model_id
                )
            except DeploymentNotFoundError:
                raise DeploymentNotRegisteredError(model_id=self.metadata.model_id)

        else:
            try:
                deployment = model_db_service.get_deployment(
                    model_id=self.metadata.model_id, deployment_id=deployment_id
                )
            except DeploymentNotFoundError:
                raise DeploymentNotRegisteredError(
                    model_id=self.metadata.model_id, deployment_id=deployment_id
                )

        # load flow
        flow_metadata = model_db_service.get_deployment_flow(
            deployment_id=deployment.deployment_id
        )
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

        self.deployment = Deployment(
            metadatata=deployment, project=flow_metadata.project
        )
        self.flow = flow


"""
    @inject
    def install(self, deployment_id: str = None, model_db_service: ModelDBService = Provide[Context.model_db_service]):
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
            output = subprocess.check_call(["conda", "env", "update", "--name",  env_name, "--file", env_url])

        except:
            print(f"Unable to install environment for {deployment.package_name}")
            sys.exit()

        # try install of package
        try:
            output = subprocess.check_call([sys.executable, '-m', 'pip', 'install', f"git+{version_url}"])

        except:
            print(f"Unable to install {deployment.package_name}")
            sys.exit()



    def run_flow(self):
        # add function to get old deployment

        if self._model_registry.get(model_id) is not None:
            pass

        else:
            deployment = self._model_db.get_latest_deployment(self.model_id)
            model_info = self._get_model_info(deployment)

        return self._load_model_from_entrypoint(model_info["model_entrypoint"])


    def run_flow_and_return(self):
        ...



    # local methods
    def predict(self, *, model_id: int, input_variables):
        model = self.get_latest_model(model_id)
        return model.evaluate(input_variables)


    def _register_deployment(self, deployment):
        dist = distribution(deployment.package_name)
        model_entrypoint = dist.entry_points.select(group="orchestration", name=f"{deployment.package_name}.model")
        if len(model_entrypoint):
            model_entrypoint = model_entrypoint[0].value

        flow_entrypoint = dist.entry_points.select(group="orchestration", name=f"{deployment.package_name}.flow")
        if len(flow_entrypoint):
            flow_entrypoint = flow_entrypoint[0].value

        # add to registry
        self._model_registry[deployment.model_id] = {"model_entrypoint": model_entrypoint, "package": deployment.package_name, "flow_entrypoint": flow_entrypoint}


    @staticmethod
    def _load_flow_from_entrypoint(flow_entrypoint):
        module_name, fn_name = flow_entrypoint.rsplit(":", 1)
        fn = getattr(import_module(module_name), fn_name)
        return fn()

    @staticmethod
    def _load_model_from_entrypoint(model_entrypoint):
        module_name, class_name = model_entrypoint.rsplit(":", 1)
        model_class = getattr(import_module(module_name), class_name)
        return model_class()

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

    def register_deployment(self, *, deployment_id, project_name):
        deployment = self._model_db.get_deployment(deployment_id)
        model_info = self._get_model_info(deployment)

        flow_entrypoint = model_info["flow_entrypoint"]
        flow = self._load_flow_from_entrypoint(flow_entrypoint)

        flow_id = self._scheduler.register_flow(flow, project_name, deployment.version)

        self._model_db.store_flow(flow_id =flow_id, deployment_ids=[deployment_id],flow_name= self._model_registry[deployment.model_id]["package"], project_name=project_name)

        return flow_id

    def save_model(self):
        ...

    def load_model(self):
        ...
"""
