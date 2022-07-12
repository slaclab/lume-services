# Scheduling Service

Prefect 1.0 does not support running of subflows directly within a flow so we can't construct flows like:
```python
with Flow("flow-a") as flow_a:
    a()
    b()

with Flow("parent-flow") as flow:
    c()
    flow_a.run(executor=LocalDaskExecutor())

flow.run(executor=LocalDaskExecutor())
```

Instead and unfortunately, flow-of-flow composition requires registration of the flow with a project on the Prefect server and query of tasks by result. Prefect 2.0 will support subflow registration.

```python
with Flow("local-results1") as flow:
    x = Parameter("x")
    y = check(x)
    downstream_task(y)

flow.register(project_name="test-res")

with Flow("parent") as flow2:
    three = return_3()
    flow_run = create_flow_run(flow_name="local-results1", parameters={"x": three})
    flow_wait = wait_for_flow_run(flow_run, raise_final_state=True)

    root_task_res = get_task_run_result(flow_run, "downstream_task-1")
    downstream_res = get_task_run_result(flow_run, "test-slug")
```


The schema in `lume_services.services.scheduling.schema.flow_of_flows_schema.py` defines the flow of flow configuration

`compose` method on the FlowOfFlows object organizes flows

New parameters are created using the scheme `{flow_name}-{param_name}`


## Tasks
load_db_result vs LoadDBResult


Db results assumes one save per flow
Allows multiple file results
