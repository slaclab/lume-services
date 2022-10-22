# Docker Image

The lume-services repository is packaged with a Dockerfile for composing the image used to execute individual workflows. The file was modeled after that packaged with [Prefect](https://github.com/PrefectHQ/prefect/blob/1.x/Dockerfile) with the addition of conda for environment resolution and already-installed `lume-services`.

When a job is submitted to the scheduling service, the agent creates a container using this image and executes a workflow using a module path. Model Python packages that we install into the Docker images generated in the GitHub workflows. 



## Notes:

This project might be helpful for future development: https://github.com/conda-forge/conda-docker-feedstock
