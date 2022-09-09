import logging

from sqlalchemy import insert
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
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

    # one to many relationship with deployment
    deployments = relationship("Deployment", back_populates="model")

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
    package_import_name = Column("package_import_name", String(255), nullable=False)
    asset_dir = Column("asset_dir", String(255), nullable=True)
    source = Column("source", String(255), nullable=False)
    sha_256 = Column("sha256", String(255), nullable=False)
    image = Column("image", String(255), nullable=True)
    is_live = Column("is_live", Boolean, nullable=False)

    # if model deleted from models table, all deployments will be deleted
    model_id = Column(
        "model_id", ForeignKey("model.model_id"), nullable=False, onupdate="cascade"
    )

    # one to many
    model = relationship("Model", back_populates="deployments", uselist=False)

    # one -> many
    flow = relationship("Flow", back_populates="deployment", uselist=False)

    # one -> many
    dependencies = relationship("DeploymentDependency", back_populates="deployment")

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
                is_live={self.is_live!r} \
                package_import_name={self.package_import_name!r} \
                )"


class Project(Base):
    __tablename__ = "project"

    # columns
    project_name = Column("project_name", String(255), primary_key=True)
    description = Column("description", String(255), nullable=False)

    # relationships
    flows = relationship("Flow", back_populates="project")

    def __repr__(self):
        return f"Project( \
                project_name={self.project_name!r}, \
                description={self.description!r}, \
                )"


class Flow(Base):
    __tablename__ = "flow"

    # columns
    flow_id = Column("flow_id", String(255), primary_key=True, nullable=False)
    flow_name = Column("flow_name", String(255), nullable=False)
    project_name = Column(
        "project_name",
        ForeignKey("project.project_name"),
        nullable=False,
        onupdate="cascade",
    )
    # one to many mapping deployment_id -> flow
    deployment_id = Column(
        "deployment_id",
        ForeignKey("deployment.deployment_id"),
        nullable=False,
        onupdate="cascade",
    )

    deployment = relationship("Deployment", back_populates="flow", uselist=False)
    project = relationship("Project", back_populates="flows", uselist=False)

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

    parent_flow = relationship(
        "Flow", foreign_keys="FlowOfFlows.parent_flow_id", uselist=False
    )
    flow = relationship(
        "Flow",
        foreign_keys="FlowOfFlows.flow_id",
        backref="composing_flows",
        uselist=False,
    )

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


class DependencyType(Base):
    __tablename__ = "dependency_type"

    # columns
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    type = Column("type", String(255), nullable=False)

    def __repr__(self):
        return f"DependencyType( \
                id={self.id!r}, \
                type={self.type!r}, \
                )"


class DeploymentDependency(Base):

    __tablename__ = "deployment_dependencies"

    # columns
    #  _id not necessarily referenced, but need pk for performance
    id = Column("_id", Integer, primary_key=True, autoincrement=True)
    # dependencies
    name = Column("name", String(255), nullable=False)
    source = Column("source", String(255), nullable=False)
    local_source = Column("local_source", String(255), nullable=True)
    version = Column("version", String(255), nullable=False)

    # one to many mapping deployment_id -> flow
    deployment_id = Column(
        "deployment_id",
        ForeignKey("deployment.deployment_id"),
        nullable=False,
        onupdate="cascade",
    )

    dependency_type_id = Column(
        "dependency_type_id",
        ForeignKey("dependency_type.id"),
        nullable=False,
        onupdate="cascade",
    )

    deployment = relationship(
        "Deployment",
        foreign_keys="DeploymentDependency.deployment_id",
        back_populates="dependencies",
        uselist=False,
    )
    dependency_type = relationship(
        "DependencyType",
        foreign_keys="DeploymentDependency.dependency_type_id",
        uselist=False,
    )

    def __repr__(self):
        return f"Dependencies( \
                    id={self.id!r}, \
                    name={self.name!r}, \
                    source={self.source!r}, \
                    local_source={self.local_source!r} \
                    version={self.version!r} \
                )"


# used for auto-generating schema docs
__table_schema__ = [
    Model,
    DeploymentDependency,
    Deployment,
    DependencyType,
    Flow,
    FlowOfFlows,
    Model,
    Project,
]

# Dependency types to store in model on population
CondaDependencyTypeInsert = insert(DependencyType).values(type="conda")

PipDependencyTypeInsert = insert(DependencyType).values(type="pip")
