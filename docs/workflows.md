# Flows

Variable names inside the flow context are used to compose the workflow

configure_services task uses environment variable names to configure the lume-services api endpoints

must be set as upstream taks to any tasks using those services using `my_task.set_upstream(configure_task)` within the flow context.



```python
from prefect import task, Flow, Parameter
from prefect.storage import Module
from lume_services.services.scheduling.tasks import configure_services, SaveFile
from lume_services.data.files import TextFile
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
