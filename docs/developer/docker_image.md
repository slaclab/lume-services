# Docker Image

The lume-services repository is packaged with a Dockerfile for composing the image used to execute individual workflows. The file was modeled after that packaged with [Prefect](https://github.com/PrefectHQ/prefect/blob/1.x/Dockerfile) with the addition of conda for environment resolution and already-installed `lume-services`.

When a job is submitted to the scheduling service, the agent creates a container using this image and executes a workflow using a module path (all flows are required to use [module storage](https://docs-v1.prefect.io/api/latest/storage.html#module)).

The image allows for environment specification via two environment variables, `EXTRA_CONDA_PACKAGES` and `EXTRA_PIP_PACKAGES`, provided as comma-separated strings (see [environment.sh](https://github.com/slaclab/lume-services/blob/main/entrypoint.sh)).


## Isolation

Because jobs may be submitted for execution in isolated environments without access to the standard conda channels, `LUME-services` provides an additional environment resolution tool that allows users to prepare a mounted channel with resolved dependencies. Channels can be configured as either a server-based resource or as a mounted filesystem.


* Insert diagram of requirement flow here


## Notes:

This project might be helpful for future development: https://github.com/conda-forge/conda-docker-feedstock

