import logging
from dependency_injector.wiring import Provide, inject
from prefect import Task, Parameter
from typing import Any

from lume_services.config import Context
from lume_services.services.files import FileService
from prefect.engine.results import PrefectResult

from lume_services.files import get_file_from_serializer_string
from lume_services.utils import fingerprint_dict


logger = logging.getLogger(__name__)


def _unique_file_location(file_rep):
    hash = fingerprint_dict(file_rep)
    return f"{hash}.prefect"


class SaveFile(Task):
    """This task is used to save a workflow file to a filesystem for subsequent
    retrieval. File saving supports all File objects described in
    [LUME-services](https://slaclab.github.io/lume-services/api/files/files/).
    Additional file types can be created by subclassing the base in
    `lume_services.files.file`. The `SaveFile` task relies on a ...
    EXPOUND ON FILESYSTEM IDENTIFIER

    Examples:
        ```python
        from prefect import Flow, task, Parameter
        from lume_services.results import Result
        from lume_services.tasks import configure_lume_services, SaveFile
        from lume_services.files import TextFile

        # construct task with prefect Task options
        save_file_task = SaveFile(timeout=20)

        @task
        def concatenate_text(text1, text2):
            text = text1 + text2
            return TextFile(
                        text,
                        filesystem_identifier="local",
                        filename="concatenated_text.txt"
                    )


        with Flow(
            "my_flow"
        ) as flow:
            # must first configure services because using injected results
            # database service
            configure_lume_services()

            text1 = Parameter("text1")
            text2 = Parameter("text2")

            my_file_obj = concatenate_text(text1, text2)

            file_parameters = save_file_task.parameters

            my_result = save_file_task(
                my_file_obj,
                filename = file_parameters["filename"],
                filesystem_identifier = file_parameters["filesystem_identifier"],
                file_type = TextFile # THIS MUST BE PASSED IN THE TASK CALL
            )

        ```

    """

    parameters = [
        Parameter("filename"),
        Parameter("filesystem_identifier"),
    ]

    def __init__(self, **kwargs):
        """This task is defined as a subclass of the Prefect [Task](https://docs-v1.prefect.io/api/latest/core/task.html#task-2)
        object and accepts all Task arguments during initialization.

        Args:
            name (Optional[str]): The name of this task.
            slug (Optional[str]):  The slug for this task. Slugs provide a stable ID
                for tasks so that the Prefect API can identify task run states. If a
                slug is not provided, one will be generated automatically once the
                task is added to a Flow.
            tags (Optional[List[str]]): A list of tags for this task.
            max_retries (Optional[int]): The maximum amount of times this task can be
                retried
            retry_delay (Optional[datetime.timedelta]): The amount of time to wait
                until task is retried
            retry_on (Optional[Union[Exception, Iterable[Type[Exception]]]]): Exception
                types that will allow retry behavior to occur. If not set, all
                exceptions will allow retries. If set, retries will only occur if the
                exception is a subtype of the exception types provided.
            timeout (Optional[Union[int, timedelta]]): The amount of time (in seconds)
                to wait while running this task before a timeout occurs; note that
                sub-second resolution is not supported, even when passing in a
                timedelta.
            trigger (Optional[callable]):  a function that determines whether the task
                should run, based on the states of any upstream tasks.
            skip_on_upstream_skip (Optional[bool]): if True, if any immediately upstream
                tasks are skipped, this task will automatically be skipped as well,
                regardless of trigger. By default, this prevents tasks from attempting
                to use either state or data from tasks that didn't run. If False, the
                task's trigger will be called as normal, with skips considered
                successes. Defaults to True.
            cache_for (Optional[timedelta]): The amount of time to maintain a cache
            of the outputs of this task.  Useful for situations where the containing
            Flow will be rerun multiple times, but this task doesn't need to be.
            cache_validator (Optional[Callable]): Validator that will determine
                whether the cache for this task is still valid (only required if
                `cache_for` is provided; defaults to
                `prefect.engine.cache_validators.duration_only`)
            cache_key (Optional[str]): if provided, a `cache_key`
                serves as a unique identifier for this Task's cache, and can be shared
                across both Tasks _and_ Flows; if not provided, the Task's _name_ will
                be used if running locally, or the Task's database ID if running in
                Cloud
            checkpoint (Optional[bool]): if this Task is successful, whether to
                store its result using the configured result available during the run;
                Also note that checkpointing will only occur locally if
                `prefect.config.flows.checkpointing` is set to `True`
            result (Optional[Result]): the result instance used to retrieve and
                store task results during execution
            target (Optional[Union[str, Callable]]): location to check for task Result.
                If a result exists at that location then the task run will enter a
                cached state. `target` strings can be templated formatting strings
                which will be formatted at runtime with values from `prefect.context`.
                If a callable function is provided, it should have signature
                `callable(**kwargs) -> str` and at write time all formatting kwargs
                will be passed and a fully formatted location is expected as the return
                value. The callable can be used for string formatting logic that
                `.format(**kwargs)` doesn't support.
            state_handlers (Optional[Iterable[Callable]]): A list of state change
                handlers that will be called whenever the task changes state,
                providing an opportunity to inspect or modify the new state. The
                handler will be passed the task instance, the old (prior) state,
                and the new
                (current) state, with the following signature:
                    `state_handler(task: Task, old_state: State, new_state: State) ->
                    Optional[State]`
                If multiple functions are passed, then the `new_state` argument will
                be the result of the previous handler.
            on_failure (Optional[Callable]): A function with signature
                `fn(task: Task, state: State) -> None` that will be called anytime this
                Task enters a failure state
            log_stdout (Optional[bool]): Toggle whether or not to send stdout messages
                to the Prefect logger. Defaults to `False`.
            task_run_name (Optional[Union[str, Callable]]): a name to set for this task
                at runtime. `task_run_name` strings can be templated formatting strings
                which will be formatted at runtime with values from task arguments,
                `prefect.context`, and flow parameters (in the case of a name conflict
                between these, earlier values take precedence). If a callable function
                is provided, it should have signature `callable(**kwargs) -> str` and
                at write time all formatting kwargs will be passed and a fully
                formatted location is expected as the return value. The callable can
                be used for string formatting logic that `.format(**kwargs)` doesn't
                support. **Note**: this only works for tasks running against a
                backend API.
            nout (Optional[int]): for tasks that return multiple results, the number of
                outputs to expect. If not provided, will be inferred from the task
                return annotation, if possible.  Note that `nout=1` implies the task
                returns a tuple of one value (leave as `None` for non-tuple return
                types).

        """  # noqa

        # apply some defaults but allow overrides
        log_stdout = kwargs.get("log_stdout")
        if not kwargs.get("log_stdout"):
            log_stdout = True
        else:
            log_stdout = kwargs.pop("log_stdout")

        if not kwargs.get("name"):
            name = "save_file"
        else:
            name = kwargs.pop("name")

        if not kwargs.get("result"):
            result = PrefectResult(location=_unique_file_location)
        else:
            result = kwargs.pop("result")

        super().__init__(log_stdout=log_stdout, name=name, result=result, **kwargs)

    @inject
    def run(
        self,
        obj: Any,
        filename: str,
        filesystem_identifier: str,
        file_type: type,
        file_service: FileService = Provide[Context.file_service],
    ):
        """Save a file.

        Args:
            obj (Any): Object to be saved
            filename (str): File path to save
            filesystem_identifier (str): String identifier for filesystem configured
                with File Service
            file_type (type): Type of file to save as. This is not exposed as a
                task parameter and should be passed explicitely during task run call.
                See examples.
            file_service (FileService): File service for interacting w/ filesystems

        Returns:
            dict: Loaded file type

        """
        file = file_type(
            obj=obj, filesystem_identifier=filesystem_identifier, filename=filename
        )
        file.write(file_service=file_service)
        return file.jsonable_dict()


class LoadFile(Task):
    parameters = [
        Parameter("file_rep"),
    ]

    def __init__(self, **kwargs):
        """This task is defined as a subclass of the Prefect [Task](https://docs-v1.prefect.io/api/latest/core/task.html#task-2)
        object and accepts all Task arguments during initialization.

        Args:
            name (Optional[str]): The name of this task.
            slug (Optional[str]):  The slug for this task. Slugs provide a stable ID
                for tasks so that the Prefect API can identify task run states. If a
                slug is not provided, one will be generated automatically once the
                task is added to a Flow.
            tags (Optional[List[str]]): A list of tags for this task.
            max_retries (Optional[int]): The maximum amount of times this task can be
                retried
            retry_delay (Optional[datetime.timedelta]): The amount of time to wait
                until task is retried
            retry_on (Optional[Union[Exception, Iterable[Type[Exception]]]]): Exception
                types that will allow retry behavior to occur. If not set, all
                exceptions will allow retries. If set, retries will only occur if the
                exception is a subtype of the exception types provided.
            timeout (Optional[Union[int, timedelta]]): The amount of time (in seconds)
                to wait while running this task before a timeout occurs; note that
                sub-second resolution is not supported, even when passing in a
                timedelta.
            trigger (Optional[callable]):  a function that determines whether the task
                should run, based on the states of any upstream tasks.
            skip_on_upstream_skip (Optional[bool]): if True, if any immediately upstream
                tasks are skipped, this task will automatically be skipped as well,
                regardless of trigger. By default, this prevents tasks from attempting
                to use either state or data from tasks that didn't run. If False, the
                task's trigger will be called as normal, with skips considered
                successes. Defaults to True.
            cache_for (Optional[timedelta]): The amount of time to maintain a cache
            of the outputs of this task.  Useful for situations where the containing
            Flow will be rerun multiple times, but this task doesn't need to be.
            cache_validator (Optional[Callable]): Validator that will determine
                whether the cache for this task is still valid (only required if
                `cache_for` is provided; defaults to
                `prefect.engine.cache_validators.duration_only`)
            cache_key (Optional[str]): if provided, a `cache_key`
                serves as a unique identifier for this Task's cache, and can be shared
                across both Tasks _and_ Flows; if not provided, the Task's _name_ will
                be used if running locally, or the Task's database ID if running in
                Cloud
            checkpoint (Optional[bool]): if this Task is successful, whether to
                store its result using the configured result available during the run;
                Also note that checkpointing will only occur locally if
                `prefect.config.flows.checkpointing` is set to `True`
            result (Optional[Result]): the result instance used to retrieve and
                store task results during execution
            target (Optional[Union[str, Callable]]): location to check for task Result.
                If a result exists at that location then the task run will enter a
                cached state. `target` strings can be templated formatting strings
                which will be formatted at runtime with values from `prefect.context`.
                If a callable function is provided, it should have signature
                `callable(**kwargs) -> str` and at write time all formatting kwargs
                will be passed and a fully formatted location is expected as the return
                value. The callable can be used for string formatting logic that
                `.format(**kwargs)` doesn't support.
            state_handlers (Optional[Iterable[Callable]]): A list of state change
                handlers that will be called whenever the task changes state,
                providing an opportunity to inspect or modify the new state. The
                handler will be passed the task instance, the old (prior) state,
                and the new
                (current) state, with the following signature:
                    `state_handler(task: Task, old_state: State, new_state: State) ->
                    Optional[State]`
                If multiple functions are passed, then the `new_state` argument will
                be the result of the previous handler.
            on_failure (Optional[Callable]): A function with signature
                `fn(task: Task, state: State) -> None` that will be called anytime this
                Task enters a failure state
            log_stdout (Optional[bool]): Toggle whether or not to send stdout messages
                to the Prefect logger. Defaults to `False`.
            task_run_name (Optional[Union[str, Callable]]): a name to set for this task
                at runtime. `task_run_name` strings can be templated formatting strings
                which will be formatted at runtime with values from task arguments,
                `prefect.context`, and flow parameters (in the case of a name conflict
                between these, earlier values take precedence). If a callable function
                is provided, it should have signature `callable(**kwargs) -> str` and
                at write time all formatting kwargs will be passed and a fully
                formatted location is expected as the return value. The callable can
                be used for string formatting logic that `.format(**kwargs)` doesn't
                support. **Note**: this only works for tasks running against a
                backend API.
            nout (Optional[int]): for tasks that return multiple results, the number of
                outputs to expect. If not provided, will be inferred from the task
                return annotation, if possible.  Note that `nout=1` implies the task
                returns a tuple of one value (leave as `None` for non-tuple return
                types).

        """  # noqa

        # apply some defaults but allow overrides
        log_stdout = kwargs.get("log_stdout")
        if not kwargs.get("log_stdout"):
            log_stdout = True
        else:
            log_stdout = kwargs.pop("log_stdout")

        if not kwargs.get("name"):
            name = "load_file"
        else:
            name = kwargs.pop("name")

        super().__init__(log_stdout=log_stdout, name=name, **kwargs)

    @inject
    def run(
        self, file_rep: dict, file_service: FileService = Provide[Context.file_service]
    ) -> Any:
        """Load a file

        Args:
            file_rep (dict): File data representation
            file_service (FileService): File service for interacting w/ filesystems

        Returns:
            Any: Unserialize file object

        """

        file_type = get_file_from_serializer_string(file_rep["file_type_string"])
        file_result = file_type(**file_rep)

        return file_result.read(file_service=file_service)
