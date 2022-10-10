


## Results database service


Queries using pymongo



## Model documents

Model documents define the schema for a model's stored results


## Files


## Results Database Entries

Results objects provide an easy interface with ...


PrefectResults stored in Prefect Core's server


### Generic

### Impact

### Custom

Custom results must subcalss the generic Result object.

```python
class CustomResult(Result):
    """Extends Result base and implements model specific attributes"""

```





###

LUME-services is packaged with seveal pre-configured model results: `Impact`, `Generic`


The model categories


### Development

In the event that a different result storage scheme would like to be used the steps are as followed:
1. Subclass result
    -
2. Creation of database service
    - Implementation of `ResultsDB` class in `lume_services.services.results.db`.
    - Methods should manage connections (multiprocessing and thread-safe) & translate above custom document representations to database



```python
from lume_services.services.results.db import ResultsDB, ResultsDBConfig
from lume_services.services.results.results_service import ResultsDBService

class MyCustomDB(ResultsDB):
    ...

class CustomDBServiceConfig(ResultsDBConfig):
    url: str

custom_db_service_config = CustomDBServiceConfig(
    url="blah://my-connection-url",
)

my_db_service = MyCustomDBService(
    custom_db_service_config
)
results_db_service = ResultsDBService(my_db_service)

```


## Result documents

Results are organized into artifacts called documents

### Custom indices

It may be useful to overwrite the indices given in the base class...


### User roles

https://www.mongodb.com/docs/manual/core/collection-level-access-control/
