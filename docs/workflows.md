# Workflows

LUME-services allows us to build workflows using Prefect's [Flow](https://docs.prefect.io/core/concepts/flows.html) APIs. Flows can be conceptualized of as scoped units of work.

A flow looks like:
```


```

Parameters are data objects passed into the flow at runtime.

Variable names inside the flow context are used to compose the workflow


## Configuring flows for use with LUME-services


configure_services task uses environment variable names to configure the lume-services api endpoints

must be set as upstream taks to any tasks using those services using `my_task.set_upstream(configure_task)` within the flow context.






## Flow parameters

Flow Parameters have some constraints. To see why those constraints exist, see developer docs [here](developer/prefect.md#serialization).
1. Flow-level parameters must be serializable, meaning they must be of types:

|  Python          | JSON    |
|----------------------------|
| dict             | object  |
| list, tuple      | array   |
| str              | string  |
| int, long, float | number  |
| True             | true    |
| False            | false   |
| None             |         |

2. In order to access the results of tasks outside a flow, the task-level results must be JSON serializable. LUME-services packages some utilities for interacting with custom result types using JSON representations of the result that can be used to load at runtime.


## Common tasks



```python
from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.tasks import configure_services, SaveFile
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
    configure = configure_services()
    new_text = append_text(text1, text2)
    file = save_file(
        obj=new_text,
        file_type=TextFile,
        filename=filename,
        filesystem_identifier=filesystem_identifier,
    )
    file.set_upstream(configure)


```

## Results

name results


### Database results

in order to save multiple results to the database, define a name for the database result


### File results

if saving multiple files in the workflow, task name should be passed when initializing the task


### Result customization

All result tasks are subclasses of the prefect Task object and accept all Task initialization arguments...


## Flow-of-flows

Yaml
* task name must match name
