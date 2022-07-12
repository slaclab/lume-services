

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
