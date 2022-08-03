# LUME-services

LUME-services provides a set of common services for use in the orchestrations of models (here defined as a self-contained workflow) and simulations:

- Contextualized [file service](services/files.md) (local/mounted/remote)
- [Model database service](services/models.md) for tracking model deployments
- [Results database service](services/results.md) for storing model output
- [Scheduling service](services/scheduling.md) for deploying model runs with [Prefect](https://docs.prefect.io/)
- Abstracted [HPC service] for integration with scientific computing infrastructure.

The intent of these tools are to streamline the packaging of modeling/simulation code by providing contextual flexibility with respect to service clusters. The framework uses runtime configurations for initializing backend implementation of all services, facilitating portability from local, to distributed dev, or production environments.

<br>

Services can be deployed in clusters of containers or on remote resources subject to user constraints.
- Docker
* INSERT DIAGRAM OF DOCKER SYSTEM
- Kubernetes
![kubernetes](./files/kubernetes_architecture.png)
- Local development
* DIAGRAM OF PROCESS-BASED EXECUTION



Features:
* Standard schema for managing model metadata
* Differentiated local and remote execution environments suitable for fast/slow executing models, respectively
* Supports deployment of models into a standardized container by exposing pip and conda commands to container
* Versioning at model and workflow levels
* Simple reversion and execution of prior model versions
* Configurable result persistence
* Visualization tools for model results

Microservice-based components rather than monolithic allowing for scalability, maintainability, and parallelized development/maintenance.


## Installation


## Development environment
