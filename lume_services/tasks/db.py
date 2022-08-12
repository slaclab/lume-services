import logging
from typing import List, Optional, Any
from dependency_injector.wiring import Provide, inject

from lume_services.config import Context
from lume_services.services.results import ResultsDB
from prefect.engine.results import PrefectResult
from prefect import Task, Parameter

from lume_services.results import get_result_from_string
from lume_services.utils import fingerprint_dict

logger = logging.getLogger(__name__)


def _unique_db_location(result_rep):
    hash = fingerprint_dict(result_rep)
    return f"{hash}.prefect"


class SaveDBResult(Task):
    """Save a result from the results database. All database results generate a
    [minimally representative identifier][lume_model.results.generic.Result] that can
    be used to query the database and load the result. This idenifier is jsonable and
    therefore accessable outside of the workflow's scope. This task uses either a
    passed or injected results database service to save the unique representation
    of the result to the database. Custom result sublasses may impose additional
    uniqueness constraints. In order to use this task with the backend, your
    flow must be registered with the backend as the result's `flow_id` is inferred from
    the Prefect Context. Alternatively, for development purposes, `flow_id` can be
    passed directly.

    This task is defined as a subclass of the Prefect [Task](https://docs-v1.prefect.io/api/latest/core/task.html#task-2)
    object and accepts all Task arguments during initialization.

    Examples:
        ```python
        from prefect import Flow, task
        from lume_services.results import Result
        from lume_services.tasks import configure_lume_services, SaveDBResult

        # construct_task
        save_db_result_task = SaveDBResult(timeout=20)

        @task
        def format_result_entry():
            inputs = {
                "input1": 1.0,
                "input2": 2.0,
            }

            outputs = {
                "output1" : 1.0,
                "output2": 2.0
            }

            return Result(
                inputs=inputs,
                outputs=outputs,
                flow_id="local-test"
            )

        with Flow(
            "my_flow"
        ) as flow:
            # must first configure services because using injected results
            # database service
            configure_lume_services()

            result = format_result_entry()

            my_result = save_db_result_task(
                result
            )

        ```

    """  # noqa

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
            name = "save_db_result"
        else:
            name = kwargs.pop("name")

        if not kwargs.get("result"):
            result = PrefectResult(location=_unique_db_location)
        else:
            result = kwargs.pop("result")

        super().__init__(log_stdout=log_stdout, name=name, result=result, **kwargs)

    @inject
    def run(
        self,
        result,
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ) -> dict:
        """Insert result into the results database service. Creates a PrefectResult that
        contains minimal representative information for reconstruction.

        Args:
            result (Result): Result object to save
            results_db_service (ResultsDB): Results database service


        Returns:
            dict: Unique representation for collecting results.

        """

        result.insert(results_db_service=results_db_service)
        return result.unique_rep()


class LoadDBResult(Task):
    """Load a result from the results database. All database results generate a
    [minimally representative identifier][lume_model.results.generic.Result] that can
    be used to query the database and load the result. This idenifier is jsonable and
    therefore accessable outside of the workflow's scope. This task uses the identifier
    to load the database query and performs data selection via the `attribute_index`
    parameters.

    The `attribute_index` parameter provides selection instructions from query. For
    example, selecting the first `toyota` from a dictionary of form: `{"outputs":
    {"vehicle": {"car":  ["toyota", "mini"], "boat": ["sail", "motor"]}}}`would be
    accomplished by passing `attribute_index=["outputs", "vehicle", "car", 0].

    This task is defined as a subclass of the Prefect [Task](https://docs-v1.prefect.io/api/latest/core/task.html#task-2)
    object and accepts all Task arguments during initialization.

    Examples:
        ```python
        from prefect import Flow, task
        from lume_services.tasks import configure_lume_services, LoadDBResult


        load_db_result_task = LoadDBResult(timeout=20)

        @task
        def print_result(value):
            print(value)


        with Flow(
            "my_flow"
        ) as flow:
            # must first configure services because using injected results
            # database service
            configure_lume_services()

            # assume some other flow has saved a Result object to the database with the
            # resulting unique representation (Result.unique_rep):
            unique_rep = {
                "result_type_string": "lume_model.results.generic:Result",
                "query": {
                       "inputs": {
                           "input1": 1.0,
                           "input2": 2.0
                        },
                        "outputs": {
                            "output1": 1.0,
                            "output2": 2.0
                        },
                       "flow_id": 1
                }
            }

            my_result = load_db_result_task(
                result_rep = unique_rep,
                attribute_index=["outputs", "output1"]
            )

            print_result(my_result) # Will print 1.0
        ```

    """  # noqa

    parameters = [
        Parameter("attribute_index"),
        Parameter("result_rep"),
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
            name = "load_db_result"
        else:
            name = kwargs.pop("name")

        super().__init__(log_stdout=log_stdout, name=name, **kwargs)

    def run(
        self,
        result_rep: dict,
        attribute_index: Optional[List[str, int]],
        results_db_service: ResultsDB = Provide[Context.results_db_service],
    ) -> Any:
        """Load a result from the database using a lume_services.Result represention.

        Args:
            result_rep (dict): Result representation containing result_type_string and
                query for selection.
            attribute_index (List[str, int]]): Selection instructions from query.
                For example, selecting the first `toyota` from a dictionary of form:
                `{"vehicle": {"car":  ["toyota", "mini"], "boat": ["sail", "motor"]}}`
                would be accomplished by passing `attribute_index=["car", 0].
            results_db_service (ResultsDB): Results database service. This is injected
                when using the LUME-service configuration toolset.

        Returns:
            Any: Returns selection of value from result if attibute_index is passed,
                otherwise returns Result object.

        """
        result_type = get_result_from_string(result_rep["result_type_string"])
        result = result_type.load_from_query(
            result_rep["query"], results_db_service=results_db_service
        )

        # select first attribute
        attr_value = getattr(result, attribute_index[0], None)
        if attr_value is None:
            return result

        else:
            for index in attribute_index[1:]:
                attr_value = attr_value[index]

            return attr_value
