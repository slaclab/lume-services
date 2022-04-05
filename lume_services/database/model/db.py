from abc import ABC, abstractmethod
from pydantic import BaseModel, BaseSettings
from typing import Optional, List
from sqlalchemy.schema import Column, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.types import Integer, String, DateTime
from sqlalchemy import insert, select, desc
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

##############################################################
# Define schema objecs using sqlalchemy ORM                  #
# https://docs.sqlalchemy.org/en/14/orm/quickstart.html      #
##############################################################


class Model(Base):
    __tablename__ = "models"
    model_id = Column('model_id', Integer, primary_key=True, autoincrement=True)
    created = Column("created", DateTime(timezone=True), server_default=func.now())
    author = Column("author", String(255), nullable=False)
    laboratory = Column("laboratory", String(255), nullable=False)
    facility = Column("facility", String(255), nullable=False)
    beampath = Column("beampath", String(255), nullable=False)
    description =Column("description", String(255), nullable=False)

    children = relationship("Deployment",
       # back_populates="parent",
       # cascade="all, delete",
       # passive_deletes= True
    )

    def __repr__(self):
        return f"Model( \
                    model_id={self.model_id!r}, \
                    created={self.created!r}, \
                    author={self.author!r}), \
                    laboratory={self.laboratory!r}, \
                    facility={self.facility!r}, \
                    beampath={self.beampath!r}, \
                    description={self.description!r} \
                )"


class Deployment(Base):
    __tablename__ = "deployments"
    deployment_id = Column('deployment_id', Integer, primary_key=True, autoincrement=True)
    version = Column('version', String(255), nullable=False)
    deploy_date = Column("deploy_date", DateTime(timezone=True), server_default=func.now())
    asset_dir = Column("asset_dir", String(255), nullable=True)
    asset_url = Column("asset_url", String(255), nullable=True)
    sha_256 = Column("sha256", String(255), nullable=False)
    package_name = Column("package_name", String(255), nullable=False)
    url = Column("url", String(255), nullable=False)

    # if model deleted from models table, all deployments will be deleted
    model_id = Column('model_id', Integer, ForeignKey("models.model_id", ondelete="CASCADE"), nullable=False)

    parent = relationship("Model", back_populates="children")

    __table_args__ = (
                ForeignKeyConstraint(['model_id'], ['models.model_id']),
               # UniqueConstraint('foo'),
                )

    def __repr__(self):
        return f"Deployment( \
                deployment_id={self.deployment_id!r}, \
                model_id={self.model_id}, \
                version={self.version!r}, \
                deploy_date={self.deploy_date!r}), \
                asset_dir={self.asset_dir!r}, \
                asset_url={self.asset_url!r}, \
                sha256={self.sha_256!r}, \
                package_name={self.package_name!r} \
                url={self.package_url!r} \
                )"

class Project(Base):
    __tablename__ = "projects"
    project_name = Column("project_name", String(255), primary_key=True)
    description = Column("description", String(255), nullable=False)
    create_date = Column("create_date", DateTime(timezone=True), server_default=func.now())

    children = relationship("Flow",
        back_populates="parent",
        cascade="all, delete",
        passive_deletes= True
    )

    def __repr__(self):
        return f"Project( \
                project_name={self.project_name!r}, \
                description={self.description!r}, \
                create_date={self.create_date!r}, \
                )"


class Flow(Base):
    __tablename__ = "flows"
    flow_id = Column("flow_id", String(255), primary_key=True)
    deploy_date = Column("deploy_date", DateTime(timezone=True), server_default=func.now())
    flow_name = Column("flow_name", String(255), nullable=False)
    project_name = Column("project_name", ForeignKey("projects.project_name"), nullable=False)

    parent = relationship("Project", back_populates="children")

    __table_args__ = (
        ForeignKeyConstraint(['project_name'], ['projects.project_name']),
        # UniqueConstraint('foo'),
    )

    def __repr__(self):
        return f"Flow( \
                flow_id={self.flow_id!r}, \
                deploy_date={self.deploy_date!r}, \
                flow_name={self.flow_name!r}, \
                project_name={self.project_name!r} \
                )"

    
class FlowToDeployments(Base):
    __tablename__ = "flow_to_deployments"
    flow_id = Column("flow_id", String(255), primary_key=True)
    deployment_id = Column("deployment_id", ForeignKey("deployments.deployment_id"), nullable=False)
    
    __table_args__ = (ForeignKeyConstraint(
        ['deployment_id'], ["deployments.deployment_id"],
        #ondelete="SET NULL"
        ),
    )

    def __repr__(self):
        return f"FlowToDeployments( \
                flow_id={self.flow_id!r}, \
                deployment_id={self.deployment_id!r} \
                )"


class DBServiceConfig(BaseSettings):
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


class ModelDBService:

    def __init__(self, db_service: DBService):
        self._db_service = db_service

    def store_model(self, **kwargs) -> Model:

        # store in db
        insert_stmt = insert(Model).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        print(result)

        if result is not None:
            return result[0]

        else:
            return None

    def store_deployment(self, **kwargs) -> Deployment:

        # store in db
        insert_stmt = insert(Deployment).values(**kwargs)

        result = self._db_service.insert(insert_stmt)

        # assign deployment id if successful
        if result is not None:
            return result[0]

        else:
            return None

    def store_project(self, **kwargs) -> Project:

        insert_stmt = insert(Project).values(**kwargs)

        # store in db
        result = self._db_service.insert(insert_stmt)

        # return inserted
        if result is not None:
            return result[0]

        else:
            return None

    
    def store_flow(self, deployment_ids=List[int], flow_id=str, **kwargs) -> Flow:

        insert_stmnts = []

        insert_stmt = insert(Flow).values(flow_id=flow_id, **kwargs)
        result = self._db_service.insert(insert_stmt)

        for deployment_id in deployment_ids:

            #drop the pop below once deployment ids removed from flow serialization
            insert_stmt = insert(FlowToDeployments).values(deployment_id=deployment_id, flow_id=flow_id)
            insert_stmnts.append(insert_stmt)

        self._db_service.insert(insert_stmnts)

        # return inserted
        if result is not None:
            return result

        else:
            return
    
    def get_model(self, **kwargs) -> Model: 
        # execute query
        query = select(Model).filter_by(**kwargs)
        result = self._db_service.execute(query)

        # assign project_name id if successful
        if result is not None:
            return result[0]

        else:
            return None


    def get_deployment(self, **kwargs) -> Deployment:

        query = select(Deployment).filter_by(**kwargs)
        result = self._db_service.execute(query)

        # assign project_name id if successful
        if result is not None:
            return result

        else:
            return None


    def get_latest_deployment(self, **kwargs) -> Deployment:

        query = select(Deployment).filter_by(**kwargs).order_by(desc(Deployment.deploy_date))
        result = self._db_service.execute(query)

        # assign project_name id if successful
        if result is not None:
            return result

        else:
            return None


    def get_project(self, **kwargs) -> Project:

        # execute query
        query = select(Project).filter_by(**kwargs).order_by(desc(Project.create_date))
        result = self._db_service.execute(query)

        # assign project_name id if successful
        if result is not None:
            return result[0]

        else:
            return None

    def get_flow(self, **kwargs) -> Flow:

        query = select(Flow).filter_by(**kwargs).order_by(desc(Flow.deploy_date))
        result = self._db_service.execute(query)

        # assign project_name id if successful
        if result is not None:
            return result[0]

        else:
            return None


    def apply_schema(self):

    
        Base.metadata.create_all(self._db_service.engine)
