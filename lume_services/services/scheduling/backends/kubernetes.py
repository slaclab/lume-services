from pydantic import validator, Field
from typing import List, Optional, Union, Literal
import logging

from prefect.run_configs import KubernetesRun

from lume_services.services.scheduling.backends.backend import RunConfig
from lume_services.services.scheduling.backends.server import ServerBackend

logger = logging.getLogger(__name__)

KUBERNETES_REQUEST_SUFFIXES = [
    "EB",
    "PB",
    "TB",
    "GB",
    "MB",
    "kB",
    "EiB",
    "PiB",
    "TiB",
    "GiB",
    "MiB",
    "KiB",
]


class KubernetesRunConfig(RunConfig):
    """Pydantic representation of args to:
    https://docs.prefect.io/api/latest/run_configs.html#kubernetesrun
    https://kubernetes.io/docs/concepts/configuration/overview/#container-images

    Attributes:
        image (Optional[str]): The image to use. Can also be specified via job
            template.
        job_template_path (Optional[str]): Path to a job template to use. If a local
            path (no file scheme, or a file/local scheme), the job template will be
            loaded on initialization and stored on the KubernetesRun object as the
            job_template field. Otherwise the job template will be loaded at runtime
            on the agent. Supported runtime file schemes include (s3, gcs, and agent
            (for paths local to the runtime agent)).
        job_template (Optional[str]): An in-memory job template to use.
        cpu_limit (Union[float, str]): The CPU limit to use for the job
        cpu_request (Union[float, str]): The CPU request to use for the job
        memory_limit (Optional[str]): The memory limit to use for the job
        memory_request (Optional[str]): The memory request to use for the job
        service_account_name (Optional[str]): A service account name to use for this
            job. If present, overrides any service account configured on the agent or
            in the job template.
        image_pull_secrets (Optional[list]): A list of image pull secrets to use for
            this job. If present, overrides any image pull secrets configured on the
            agent or in the job template.
        image_pull_policy (Optional[str]): The imagePullPolicy to use for the job.

    """

    image: Optional[str]
    image_pull_secrets: Optional[List[str]]
    job_template: Optional[dict]
    job_template_path: Optional[str]
    service_account_name: str
    image_pull_policy: Literal["Always", "IfNotPresent", "Never"] = "IfNotPresent"
    cpu_limit: Union[float, str] = 1.0
    cpu_request: Union[float, str] = 0.5
    memory_limit: Union[str, int] = None
    memory_request: Union[str, int] = None

    @validator("memory_limit", "memory_request")
    def validate_memory(cls, v):
        """Validate w.r.t. Kubernetes resource formats: int, fixed-point number using
        quantity suffixes: E, P, T, G, M, k or power-of-two equivalents: Ei, Pi,
        Ti, Gi, Mi, Ki

        """

        if isinstance(v, (int,)):
            return v

        elif isinstance(v, (str,)):

            acceptable = False

            # check substrings
            inclusions = [
                substring for substring in KUBERNETES_REQUEST_SUFFIXES if substring in v
            ]

            if len(inclusions):

                for inclusion in inclusions:

                    try:
                        stripped = v.replace(inclusion, "")
                        _ = int(stripped)
                        acceptable = True

                    except ValueError:
                        pass

            if not acceptable:
                logger.error("Kubernetes resource request invalid: %s", v)
                raise ValueError(f"Kubernetes resource request invalid: {v}")

        else:
            raise ValueError("Must provide string or int to request")

        return v

    def build(self) -> KubernetesRun:
        """Method for converting to Prefect RunConfig type KubernetesRun.

        Returns:
            KubernetesRun

        """
        return KubernetesRun(self.dict(exclude_none=True))


class KubernetesBackend(ServerBackend):
    """Implementation of Backend used for interacting with Prefect deployed in
    K8 cluster.

    Attributes:
        config (PrefectConfig): Instantiated PrefectConfig object describing connection
            to Prefect server.
        _client (Client): Prefect client connection created on instantiation.
        _run_config_type (type): Type used to compose run configuration.

    """

    _run_config_type: type = Field(KubernetesRunConfig, exclude=True)

    @property
    def run_config_type(self):
        return self._run_config_type
