


## Results database service




## Model documents

Model documents define the schema for a model's stored results




### mongoengine

LUME-services is packaged with seveal pre-configured mongoengine model results: `Impact`, `Generic`


The model categories


Upon initialization, the `ResultsService` accepts an optional kwarg `model_docs`, which may be used to pass a custom enum to the service with altered document representations or to add new models. In the latter case, it may be useful to subclass the predefined enum, `lume_services.data.results.db.models.ModelDocs`.

### Development 

In the event that a different result storage scheme would like to be used the steps are as followed:
1. Creation of Document-like representations
    - Implementation of `DocumentBase` class defined in `lume_services.data.results.db.document` with `get_pk_id` and static method `get_validation_error`.
    - All fields should be available as attributes on the representation class
2. Creation of database service
    - Implementation of `DBService` class in `lume_services.data.results.db.db_service`. 
    - Methods should manage connections (multiprocessing and thread-safe) & translate above custom document representations to database
3. Implement `ResultsService` using instances of new services. This codebase has been structured using [Inversion of Control](https://en.wikipedia.org/wiki/Inversion_of_control) principles and an effort has been made to modularize and decouple components. 

```python
from lume_services.data.results.db.db_service import DBService, BServiceConfig
from lume_services.data.results.results_service import ResultsService

class MyCustomDBService(DBService):
    ...

class CustomDBServiceConfig(BServiceConfig):
    url: str

custom_db_service_config = CustomDBServiceConfig(
    url="blah://my-connection-url",
)

my_db_service = MyCustomDBService(
    custom_db_service_config
)
results_db_service = ResultsService(my_db_service)

```


## Result documents

Results are organized into artifacts called documents

### Custom indices

It may be useful to overwrite the indices given in the base class...
