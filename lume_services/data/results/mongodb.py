from pydantic import BaseSettings
from lume_serices.database.results.db import ResultsDB

class MongoResultsDBConfig(BaseSettings):
    db_uri_template: str = "mongodb://${user}:${password}@${host}:${port}"
    password: str
    user: str
    host: str
    port: int


class MongoResultsDB(ResultsDB):
    # Note: pymongo is threadsafe

    def __init__(self, *, db_config):

        # need to transition off of plaintext templating
        self._db_uri = Template(db_uri_template).substitute(user=user, password=password, host=host, port=str(port))
        self._client = MongoClient(self._db_uri)
        self._db = self._client.model_results

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

