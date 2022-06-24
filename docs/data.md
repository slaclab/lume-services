# Data

## Models

ADD SCHEMA DOC



## Files


## Results Database Entries

Results objects provide an easy interface with ...


PrefectResults stored in Prefect Core's server


### Generic

### Impact

### Custom

Subclasses of the generic Result  must define the model_type as a pydantic field with the alias `collection`.

```python
class CustomResult(Result):
    """Extends Result base and implements model specific attributes"""

    model_type: str = Field("MyCustomModel", alias="collection")
```
