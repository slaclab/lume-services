from abc import ABC, abstractmethod
from pydantic import BaseSettings
from typing import Optional, List
from lume_services.utils import filter_keys_in_settings

##############################################
# Objects for representing table entries     #
# Consistent with schema                     #
##############################################

class Model(BaseSettings):
    author: str
    laboratory: str
    facility: str
    beampath: str
    description: str
    model_id: Optional[str]

class Deployment(BaseSettings):
    version: str
    sha256: str
    model_id: int
    url: str
    package_name: str
    asset_dir: Optional[str]
    asset_url: Optional[str]
    deployment_id: Optional[str]

class Flow(BaseSettings):
    flow_id: str
    deployment_ids: List[int]
    flow_name: str
    project_name: str

    # drop deployment_ids from flow serialization

class Project(BaseSettings):
    project_name: str 
    description: str

class DBSchema(BaseSettings):
    model_table: str
    deployment_table: str
    flow_table: str
    project_table: str
    flow_to_deployments_table: str


class DBServiceConfig(BaseSettings):
    db_schema: DBSchema

class DBService(ABC):

    def __init__(self, db_config: DBServiceConfig):
        self.schema = db_config.db_schema

    @abstractmethod
    def execute(self, sql, *args, **kwargs):
        ...
        # Raise not implemented


class ModelDBService:

    def __init__(self, db_service: DBService):
        self._db_service = db_service

        self._model_table = self._db_service.schema.model_table
        self._flow_table = self._db_service.schema.flow_table
        self._deployment_table = self._db_service.schema.deployment_table
        self._project_table = self._db_service.schema.project_table
        self._flow_to_deployments_table = self._db_service.schema.flow_to_deployments_table

    def store_model(self, **kwargs) -> Model:
        # check able to instantiate Model with kwargs
        model = Model(**kwargs)

        # store in db
        r = self._insert_one(self._config.model_table, **model.dict())

        # assign model id if successful
        if r.successful:
            model.model_id = r.lastrowid
            return model

        else:
            return None

    def store_deployment(self, **kwargs) -> Deployment:

        # check able to instantiate Deployment with kwargs
        deployment = Deployment(**kwargs)

        # store in db
        r = self._insert_one(self._deployment_table, **deployment.dict())

        # assign deployment id if successful
        if r.successful:
            deployment.deployment_id = r.lastrowid
            return deployment

        else:
            return None

    def store_project(self, **kwargs) -> Project:

        # check able to instantiate Project with kwargs
        project = Project(**kwargs)

        # store in db
        r = self._insert_one(self._project_table, **project.dict())

        # assign deployment id if successful
        if r.successful:
            return project

        else:
            return None

    
    def store_flow(self, **kwargs) -> Flow:
        # check able to instantiate Project with kwargs
        flow = Flow(**kwargs)

        for deployment_id in flow.deployment_ids:

            #drop the pop below once deployment ids removed from flow serialization

            flow_rep = flow.dict().pop("deployment_ids")
            flow_rep["deployment_id"] = deployment_id

            # store in db
            r = self._insert_one(self._flow_table, **flow_rep)

        # assign deployment id if successful
        if r.successful:
            return flow

        else:
            return None

    
    def get_model(self, **kwargs) -> Model: 

        # check kwargs are in Model fields
        allowed_kwargs = filter_keys_in_settings(kwargs, Model)

        # execute query
        r = self._execute_single_table_query(self._model_table, **allowed_kwargs)

        if r.successful:
            # do not throw complaint about extras
            return Model(r.dict)

        else:
            return None


    def get_deployment(self, **kwargs) -> Deployment:
        # check kwargs in Deployment fields
        allowed_kwargs = filter_keys_in_settings(kwargs, Deployment)

        r = self._execute_single_table_query(self._deployment_table, **allowed_kwargs)

        if r.successful:
            # check number returned

            # raise error for too many returned

            # do not throw complaint about extras

            return Deployment(r.first())

        else:
            return None


    def get_latest_deployment(self, **kwargs) -> Deployment:

        # check kwargs in Deployment fields
        allowed_kwargs = filter_keys_in_settings(kwargs, Deployment)

        sql_extra = """
        ORDER BY deploy_date DESC
        LIMIT 1
        """

        r = self._execute_single_table_query(self._deployment_table, sql_extra=sql_extra, **allowed_kwargs)

        if r.successful:
            # do not throw complaint about extras
            return Deployment(r.first())

        else:
            return None


    def get_project(self, **kwargs) -> Project:

        # check kwargs in Project fields
        allowed_kwargs = filter_keys_in_settings(kwargs, Project)

        # execute query
        r = self._execute_single_table_query(self._project_table, **allowed_kwargs)

        if r.successful:
            # check number returned

            # raise error for too many returned

            # do not throw complaint about extras
            return Project(r.dict)

        else:
            return None


    def get_flow(self, **kwargs) -> Flow:

        # check kwargs in Flow fields
        allowed_kwargs = filter_keys_in_settings(kwargs, Flow)

        r = self._execute_single_table_query(self._flow_table, **allowed_kwargs)

        if r.successful:
            # check number, only one should be returned
            res = r.first()

            # raise error for too many returned

            # GET ALL FLOW IDS
            deploy_res = self._execute_single_table_query(self._flow_to_deployments_table, flow_id = r.first().flow_id)

            deployment_ids = [d.deployment_id for d in deploy_res]

            # do not throw complaint about extras
            return Flow(deployment_ids=deployment_ids, **res)

        else:
            return None

    def _execute_single_table_query(self, table: str, fields: List[str] = None, sql_extra: str = None, **kwargs):
        """
        
        Args:
            table (str):
            fields (List[str] = None)
            sql_extra (str = None): extra sql to append to end, helpful in case of limits, ordering
        
        """
        sql = """
        SELECT %s
        FROM %s 
        """

        # format kwargs
        kwarg_strings = []
        if len(kwargs):
            sql += "WHERE "

            for kw, value in kwargs.items():
                kwarg_strings.append(f"{kw} = {value}")

        sql += " AND ".join(kwarg_strings)

        if fields is None:
            self._db_service.execute(sql, "*", table)

        if sql_extra:
            sql += f" {sql_extra}"

        else:
            return self._db_service.execute(sql, ",".join(fields), table)


    def _insert_one(self, table: str, **kwargs):
        sql = """
        INSERT INTO %s 
        """
            
        kwarg_strings = []
        kwarg_values = []

        kwarg_field_string = ", ".join(kwargs.keys())
        kwarg_value_string = ", ".join(kwargs.values())

        sql += f" ({kwarg_field_string}) VALUES ({kwarg_value_string})"

        return self._db_service.execute(sql, table)
