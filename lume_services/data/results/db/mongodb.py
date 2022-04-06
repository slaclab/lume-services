from pydantic import BaseSettings
from lume_services.data.results.db import DBService, DBServiceConfig
from lume_services.data.results.db.document import ResultDocument

import mongoengine

class MongoResultsDBConfig(DBServiceConfig):
    db: str #name of database
    host: str 
    port: str
    read_preference: str= ""
    username: str
    password: str
  #  authentication_source
  # authentication_mechanism
  # is_mock
  # kwargsfor example maxpoolsize, tz_aware, etc. See the documentation for pymongo’s MongoClient for a full list.


class MongoDBService(DBService):
    # Note: pymongo is threadsafe

    def __init__(self, *, db_config: MongoResultsDBConfig):
        self.config = db_config
        self._client = mongoengine.connect(alias="connected_db")

    def insert_one(self, doc: ResultDocument):

        doc.save(validate=True)

     #   .model_results[model_type].insert_one(model_rep)
        return 


    def find(self):
        ...

    


    """
    def store(self, *, model_type, model_rep) -> bool:

        # check that target field is provided in rep
        insert_result = self._client.model_results[model_type].insert_one(model_rep)
        
        if insert_result.inserted_id:
            return True
        
        else:
            return False

    def find(self, *, model_type, query={}, fields={}) -> pd.DataFrame:
        results = self._db[model_type].find((query, fields))
        
        return list(results)

    def find_all(self, *, model_type):
        results = self._db[model_type].find()
        return list(results)

    def load_dataframe(self, *, model_type, query={}, fields={}):
        # flattens results and returns dataframe
        results = list(self._db[model_type].find((query, fields)))
        flattened = [flatten_dict(res) for res in results]
        df = pd.DataFrame(flattened)

        # Load DataFrame
        df["date"] = pd.to_datetime(df["isotime"])
        df["_id"] = df["_id"].astype(str)

        return df

    """
