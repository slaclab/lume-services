from sqlalchemy import insert, select, desc
from typing import List
import logging

from lume_services.data.model.db import DBService
from lume_services.data.model.db.schema import Base, Model, Deployment, Flow, FlowToDeployments, Project

from lume_services.data.model.utils import validate_kwargs_exist

logger = logging.getLogger(__name__)


class ModelDBService:

    def __init__(self, db_service: DBService):
        self._db_service = db_service

    @validate_kwargs_exist(Model)
    def store_model(self, **kwargs) -> int:

        # store in db
        insert_stmt = insert(Model).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None

    @validate_kwargs_exist(Deployment)
    def store_deployment(self, **kwargs) -> int:

        # store in db
        insert_stmt = insert(Deployment).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None

    @validate_kwargs_exist(Project)
    def store_project(self, **kwargs) -> str:

        insert_stmt = insert(Project).values(**kwargs)

        # store in db
        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None

    @validate_kwargs_exist(Flow, ignore="deployment_ids")
    def store_flow(self, deployment_ids=List[int], flow_id=str, **kwargs) -> str:
        """Store a flow. 
        
        Returns:
            str: inserted flow id
        """

        insert_stmnts = []

        insert_stmt = insert(Flow).values(flow_id=flow_id, **kwargs)
        result = self._db_service.insert(insert_stmt)

        for deployment_id in deployment_ids:

            # should be able to abstract the values here to reference table relationships
            insert_stmnt = insert(FlowToDeployments).values(deployment_id=deployment_id, flow_id=flow_id)
            insert_stmnts.append(insert_stmnt)

        self._db_service.insert_many(insert_stmnts)

        if len(result):
            return result[0]

        else:
            return None

    @validate_kwargs_exist(Model)
    def get_model(self, **kwargs) -> Model: 
        """
        
        Returns:
            Model:
        """
        # execute query
        query = select(Model).filter_by(**kwargs)
        result = self._db_service.select(query)


        if len(result):
            if len(result) > 1:
                # formatted this way to eventually move towards interpolated schema
                logger.warning("Multiple models returned from query. get_model is returning the first result with %s %s", "model_id", result[0].model_id)

            return result[0]

        else:
            return None

    @validate_kwargs_exist(Deployment)
    def get_deployment(self, **kwargs) -> Deployment:
        """
        
        Returns:
            Deployment:
        """

        query = select(Deployment).filter_by(**kwargs)
        result = self._db_service.select(query)


        if len(result):
            if len(result) > 1:
                # formatted this way to eventually move towards interpolated schema
                logger.warning("Multiple deployments returned from query. get_deployment is returning the first result with %s %s", "deployment_id", result[0].deployment_id)

            return result[0]


        else:
            return None

    @validate_kwargs_exist(Deployment)
    def get_latest_deployment(self, **kwargs) -> Deployment:
        """
        
        Returns:
            Deployment:
        """

        query = select(Deployment).filter_by(**kwargs).order_by(desc(Deployment.deploy_date))
        result = self._db_service.select(query)

        if len(result):
            return result[0]


        else:
            return None

    @validate_kwargs_exist(Project)
    def get_project(self, **kwargs) -> Project:
        """Get a single Project 
        
        Returns:
            Project:
        """

        # execute query
        query = select(Project).filter_by(**kwargs).order_by(desc(Project.create_date))
        result = self._db_service.select(query)

        if len(result):
            if len(result) > 1:
                # formatted this way to eventually move towards interpolated schema
                logger.warning("Multiple projects returned from query. get_project is returning the first result with %s %s", "name", result[0].project_name)

            return result[0]

        else:
            return None

    @validate_kwargs_exist(Flow)
    def get_flow(self, **kwargs) -> Flow:
        """
        
        Returns:
            Flow:
        """

        query = select(Flow).filter_by(**kwargs).order_by(desc(Flow.deploy_date))
        result = self._db_service.select(query)

        if len(result):
            if len(result) > 1:
                # formatted this way to eventually move towards interpolated schema
                logger.warning("Multiple flows returned from query. get_flow is returning the first result with %s %s", "flow_id", result[0].flow_id)
            
            return result[0]


        else:
            return None


    def apply_schema(self) -> None:
        """Applies database schema to connected service.
        
        """

        Base.metadata.create_all(self._db_service.engine)
