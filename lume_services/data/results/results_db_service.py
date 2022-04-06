from lume_services.data.results.db import DBService
from lume_services.utils import flatten_dict
import pandas as pd


# assume nosql

class ResultsDBConfig:
    model_types = [
        "distgen",
        "impact",
        "surrogate",
        "bmad",
        "misc"
    ]

class ResultsDBService:
    """Results database for use with NoSQL database service
    
    """

    target_field = "fingerprint"

    def __init__(self, db_service: DBService):
        self._db_service = db_service

    def store(self, *, model_rep) -> bool:

        # check that target field is provided in rep
        res = self._db_service.insert_one(model_rep)
        
        if res.inserted_id:
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
