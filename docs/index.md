# LUME-services

LUME-services provides a set of common services for use in the orchestrations of models (here defined as a self-contained workflow) and simulations:

- Contextualized [file service](services/files.md) (local/mounted/remote)
- [Model database service](services/models.md) for tracking model deployments
- [Results database service](services/results.md) for storing model output
- [Scheduling service](services/scheduling.md) for deploying model runs with [Prefect](https://docs.prefect.io/)
- Abstracted [HPC service](services/hpc.md) for integration with scientific computing infrastructure.

The intent of these tools are to streamline the packaging of modeling/simulation code by providing contextual flexibility with respect to service clusters. The framework uses runtime configurations for initializing backend implementation of all services, facilitating portability from local, to distributed dev, or production environments.

<br>

The service interfaces developed for `LUME-services` are isolated, which allows for abstraction and modularized update points, and consistent with a microservice-based application architecture, prioritizing scalability, maintainability, and parallelized development and maintenance. Services can be deployed in clusters of containers or on remote resources subject to user constraints. Example configurations of Docker and Kubernetes clusters shown below.
- Docker
![docker](./files/docker_architecture.png)
- Kubernetes
![kubernetes](./files/kubernetes_architecture.png)

<br>

Alternatively, users can execute run workflows directly in their process by configuring a local backend.

Features:
* Standard schema for managing model metadata
* Differentiated local and remote execution environments suitable for fast/slow executing models, respectively
* Supports deployment of models into a standardized container by exposing pip and conda commands to container
* Versioning at model and workflow levels
* Simple reversion and execution of prior model versions
* Configurable result persistence
* Visualization tools for model results


## Installation

This package can be installed from GitHub using:
```
pip install git+https://github.com/slaclab/lume-services.git
```

or from conda using ... (once configured with conda-forge)
