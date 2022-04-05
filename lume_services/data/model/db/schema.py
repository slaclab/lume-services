import logging

from sqlalchemy.schema import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Integer, String, DateTime

logger = logging.getLogger(__name__)

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

    deployment = relationship("Deployment",
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

    model = relationship("Model", back_populates="deployment")
    flow_to_deployment = relationship("FlowToDeployments", back_populates="deployment")

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
                url={self.url!r} \
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
    flow_to_deployment = relationship("FlowToDeployments", back_populates="flow")

    def __repr__(self):
        return f"Flow( \
                flow_id={self.flow_id!r}, \
                deploy_date={self.deploy_date!r}, \
                flow_name={self.flow_name!r}, \
                project_name={self.project_name!r} \
                )"

    
class FlowToDeployments(Base):
    __tablename__ = "flow_to_deployments"
    id = Column('_id', Integer, primary_key=True, autoincrement=True)
    flow_id = Column("flow_id", ForeignKey("flows.flow_id"), nullable=False)
    deployment_id = Column("deployment_id", ForeignKey("deployments.deployment_id"), nullable=False)

    flow = relationship("Flow")
    deployment = relationship("Deployment")

    def __repr__(self):
        return f"FlowToDeployments( \
                flow_id={self.flow_id!r}, \
                deployment_id={self.deployment_id!r} \
                )"
