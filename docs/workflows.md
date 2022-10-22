# Workflows

LUME-services allows us to build workflows using Prefect's [Flow](https://docs.prefect.io/core/concepts/flows.html) APIs. Flows can be conceptualized of as scoped units of work. Prefect uses a context-management pattern to define flow hierarchy. Parameters are units of data passed into the flow at runtime.


## Configuring flows for use with LUME-services

Inside a flow, you may use the `configure_lume_services` task to configure LUME-services from environment variables. This task must be set as upstream task to any tasks that then use those services `my_task.set_upstream(configure_task)` within the flow context.


## Flow parameters

Flow Parameters have some constraints. To see why those constraints exist, see developer docs [here](developer/services/scheduling.md#serialization).
1. Flow-level parameters must be json serializable, meaning they must be of types:

|  Python          | JSON    |
|----------------------------|
| dict             | object  |
| list, tuple      | array   |
| str              | string  |
| int, long, float | number  |
| True             | true    |
| False            | false   |
| None             |         |

2. In order to access the results of tasks outside a flow, the task-level results must also be JSON serializable. LUME-services packages some utilities for interacting with custom result types using JSON representations of the result that can be used to load at runtime. The method `lume_services.results.generic.get_db_dict()` creates a json serializable result that may then be used to fetch a full model run result form the results database.


## Common tasks

```python
from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.tasks import configure_lume_services, SaveFile
from lume_services.files import TextFile
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


@task
def append_text(text1, text2):
    return text1 + text2

save_file = SaveFile(name="save_text_file")

with Flow("flow1", storage=Module(__name__)) as flow1:
    text1 = Parameter("text1")
    text2 = Parameter("text2")
    filename = Parameter("filename")
    filesystem_identifier = Parameter("filesystem_identifier")
    configure = configure_lume_services()
    new_text = append_text(text1, text2)
    file = save_file(
        obj=new_text,
        file_type=TextFile,
        filename=filename,
        filesystem_identifier=filesystem_identifier,
    )
    file.set_upstream(configure)


```
