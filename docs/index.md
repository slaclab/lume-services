# LUME-services



LUME-services provides a set of common services for use in the orchestrations of models (here defined as a self-contained workflow) and simulations:
- File service for reading/writing to different filesystems (local/mounted/remote)
- Model registration service for tracking model deployments
- Results database for storing model output
- Scheduling service for deploying model runs with [Prefect](https://docs.prefect.io/)

Models packaged with respect to the LUME-services standard may be executed locally (for development) or deployed to a set of disributed services. LUME-services configures

Distributed services for deployment of models over service clusters

Self-describing development environment



Common interfaces designed to interact with portable services
- Docker
* INSERT DIAGRAM OF DOCKER SYSTEM
- Kubernetes
* INSERT DIAGRAM OF KUBERNETES CLUSTER
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



## Definitions
### model:
A model refers to the packaging of an execution unit   ?

## Installation


## Development environment
