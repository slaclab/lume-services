import logging

from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Integer, String, DateTime, Boolean

logger = logging.getLogger(__name__)

Base = declarative_base()

##############################################################
# Define schema objecs using sqlalchemy ORM                  #
# https://docs.sqlalchemy.org/en/14/orm/quickstart.html      #
##############################################################


class Model(Base):
    __tablename__ = "model"
    model_id = Column("model_id", Integer, primary_key=True, autoincrement=True)
    created = Column("created", DateTime(timezone=True), server_default=func.now())
    author = Column("author", String(255), nullable=False)
    laboratory = Column("laboratory", String(255), nullable=False)
    facility = Column("facility", String(255), nullable=False)
    beampath = Column("beampath", String(255), nullable=False)
    description = Column("description", String(255), nullable=False)

    deployment = relationship("Deployment", backref="model")

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
    __tablename__ = "deployment"

    # columns
    deployment_id = Column(
        "deployment_id", Integer, primary_key=True, autoincrement=True
    )
    version = Column("version", String(255), nullable=False)
    deploy_date = Column(
        "deploy_date", DateTime(timezone=True), server_default=func.now()
    )
    asset_dir = Column("asset_dir", String(255), nullable=True)
    source = Column("source", String(255), nullable=True)
    sha_256 = Column("sha256", String(255), nullable=False)
    image = Column("image", String(255), nullable=True)
    is_live = Column("is_live", Boolean, nullable=False)

    # if model deleted from models table, all deployments will be deleted
    model_id = Column(
        "model_id", ForeignKey("model.model_id"), nullable=False, onupdate="cascade"
    )

    # relationshipts
    flow_to_deployment = relationship("DeploymentFlow", backref="deployment")

    # unique constraints
    __table_args__ = (UniqueConstraint("sha256", name="_sha256_unique"),)

    def __repr__(self):
        return f"Deployment( \
                deployment_id={self.deployment_id!r}, \
                model_id={self.model_id}, \
                version={self.version!r}, \
                deploy_date={self.deploy_date!r}), \
                asset_dir={self.asset_dir!r}, \
                source={self.source!r}, \
                sha256={self.sha_256!r}, \
                image={self.image!r}, \
                url={self.url!r}, \
                is_live={self.is_live!r} \
                )"


class Project(Base):
    __tablename__ = "project"

    # columns
    project_name = Column("project_name", String(255), primary_key=True)
    description = Column("description", String(255), nullable=False)
    create_date = Column(
        "create_date", DateTime(timezone=True), server_default=func.now()
    )

    # relationships
    children = relationship("Flow", backref="project")

    def __repr__(self):
        return f"Project( \
                project_name={self.project_name!r}, \
                description={self.description!r}, \
                create_date={self.create_date!r}, \
                )"


class Flow(Base):
    __tablename__ = "flow"

    # columns
    flow_id = Column("flow_id", String(255), primary_key=True)
    flow_name = Column("flow_name", String(255), nullable=False)
    project_name = Column(
        "project_name",
        ForeignKey("project.project_name"),
        nullable=False,
        onupdate="cascade",
    )

    # relationships
    flow_to_deployment = relationship("DeploymentFlow", backref="flow")

    def __repr__(self):
        return f"Flow( \
                flow_id={self.flow_id!r}, \
                flow_name={self.flow_name!r}, \
                project_name={self.project_name!r} \
                )"


class FlowOfFlows(Base):
    __tablename__ = "flow_of_flows"

    # columns
    #  _id not necessarily referenced, but need pk for performance
    id = Column("_id", Integer, primary_key=True, autoincrement=True)
    parent_flow_id = Column(
        "parent_flow_id", ForeignKey("flow.flow_id"), nullable=False, onupdate="cascade"
    )
    flow_id = Column(
        "flow_id", ForeignKey("flow.flow_id"), nullable=False, onupdate="cascade"
    )
    # position in execution order
    position = Column("position", Integer, nullable=False)

    # relationships
    parent = relationship("Flow", foreign_keys=[parent_flow_id])
    flow = relationship("Flow", foreign_keys=[flow_id])

    # constraints
    __table_args__ = (
        UniqueConstraint("parent_flow_id", "flow_id", name="_flow_of_flow_entry"),
    )

    def __repr__(self):
        return f"FlowOfFlows( \
                id={self.id!r}, \
                flow_id={self.flow_id!r}, \
                parent_flow_id={self.parent_flow_id!r}, \
                position={self.position!r} \
                )"


class DeploymentFlow(Base):
    __tablename__ = "deployment_flow"

    # columns
    #  _id not necessarily referenced, but need pk for performance
    id = Column("_id", Integer, primary_key=True, autoincrement=True)
    flow_id = Column(
        "flow_id", ForeignKey("flow.flow_id"), nullable=False, onupdate="cascade"
    )
    deployment_id = Column(
        "deployment_id",
        ForeignKey("deployment.deployment_id"),
        nullable=False,
        onupdate="cascade",
    )

    __table_args__ = (
        UniqueConstraint("flow_id", "deployment_id", name="_unique_flow_deployment"),
    )

    def __repr__(self):
        return f"DeploymentFlow( \
                flow_id={self.flow_id!r}, \
                deployment_id={self.deployment_id!r} \
                )"
