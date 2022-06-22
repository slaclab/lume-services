# Results



## Custom results

Subclasses of the Generic result document must define the model_type as a pydantic field with the alias `collection`.

```python
class CustomResult(GenericResult):
    """Extends GenericResult base and implements model specific attributes"""

    model_type: str = Field("MyCustomModel", alias="collection")
```
