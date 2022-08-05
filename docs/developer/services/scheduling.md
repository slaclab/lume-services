# Scheduling Service


## Prefect

using Prefect version 1.2.X

The Prefect server is composed of sub-services ...


Agents run externally to the Prefect server and manage job submissions in different contexts. In order to register an agent with Prefect, you must first create a tenant...



![prefect-server](https://docs.prefect.io/orchestration/server/server-diagram.svg)





### serialization...
`Flow` level parameters must be json serializable





## Flows
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



## Docker Image

The docker image packaged with this repository is designed to provide a base image with ...

```
docker build --build-arg LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY --build-arg PREFECT_VERSION=$PREFECT_VERSION --build-arg LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION --target dev -t test-agent-dev -f prefect-agent-docker/Dockerfile .
```


docker build --build-arg LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY --build-arg PREFECT_VERSION=$PREFECT_VERSION --build-arg LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION --target dev -t test-dev-prefect -f prefect-agent-docker/Dockerfile .

docker run -v /var/run/docker.sock:/var/run/docker.sock -it test-agent-dev

At runtime, the container accepts two additional environment variables: `EXTRA_CONDA_PACKAGES` and `EXTRA_PIP_PACKAGES`. These environment variables may be used to

```
ENV EXTRA_CONDA_PACKAGES
ENV EXTRA_PIP_PACKAGES=""
```
