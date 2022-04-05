from abc import ABC, abstractmethod
from pydantic import BaseSettings
from typing import List

from sqlalchemy import insert, select, desc

from lume_services.database.schema import Base, Model, Deployment, Flow, FlowToDeployments, Project


class DBServiceConfig(BaseSettings, ABC):
    ...

class DBService(ABC):

    def __init__(self, db_config: DBServiceConfig):
        ...

    @abstractmethod
    def execute(self, orm_obj: Base):
        ...
        # Raise not implemented

    @abstractmethod
    def insert(self, orm_obj: Base):
        ...
        # Raise not implemented


    @abstractmethod
    def insert_many(self, orm_obj: Base):
        ...
        # Raise not implemented


class ModelDBService:

    def __init__(self, db_service: DBService):
        self._db_service = db_service

    def store_model(self, **kwargs) -> int:

        # store in db
        insert_stmt = insert(Model).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None


    def store_deployment(self, **kwargs) -> int:

        # store in db
        insert_stmt = insert(Deployment).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None


    def store_project(self, **kwargs) -> str:

        insert_stmt = insert(Project).values(**kwargs)

        # store in db
        result = self._db_service.insert(insert_stmt)

        if len(result):
            return result[0]

        else:
            return None

    
    def store_flow(self, deployment_ids=List[int], flow_id=str, **kwargs) -> str:
        """
        
        Returns:
            str: inserted flow id
        """

        insert_stmnts = []

        insert_stmt = insert(Flow).values(flow_id=flow_id, **kwargs)
        result = self._db_service.insert(insert_stmt)

        for deployment_id in deployment_ids:

            insert_stmnt = insert(FlowToDeployments).values(deployment_id=deployment_id, flow_id=flow_id)
            insert_stmnts.append(insert_stmnt)

        self._db_service.insert_many(insert_stmnts)

        if len(result):
            return result[0]

        else:
            return None

    def get_model(self, **kwargs) -> Model: 
        """
        
        Returns:
            Model:
        """
        # execute query
        query = select(Model).filter_by(**kwargs)
        result = self._db_service.execute(query)


        if len(result):
            return result[0]

        else:
            return None


    def get_deployment(self, **kwargs) -> Deployment:
        """
        
        Returns:
            Deployment:
        """

        query = select(Deployment).filter_by(**kwargs)
        result = self._db_service.execute(query)

        if len(result):
            return result[0]

        else:
            return None


    def get_latest_deployment(self, **kwargs) -> Deployment:
        """
        
        Returns:
            Deployment:
        """

        query = select(Deployment).filter_by(**kwargs).order_by(desc(Deployment.deploy_date))
        result = self._db_service.execute(query)

        if result:
            return result[0]

        else:
            return None


    def get_project(self, **kwargs) -> Project:
        """
        
        Returns:
            Project:
        """

        # execute query
        query = select(Project).filter_by(**kwargs).order_by(desc(Project.create_date))
        result = self._db_service.execute(query)

        if len(result):
            return result[0]

        else:
            return None

    def get_flow(self, **kwargs) -> Flow:
        """
        
        Returns:
            Flow:
        """

        query = select(Flow).filter_by(**kwargs).order_by(desc(Flow.deploy_date))
        result = self._db_service.execute(query)

        if len(result):
            return result[0]

        else:
            return None


    def apply_schema(self) -> None:
        """Applies database schema to connected service.
        
        
        """
        Base.metadata.create_all(self._db_service.engine)
