from pydantic import BaseModel, validator
from prefect.run_configs import KubernetesRun
from typing import List, Optional, Dict, Union, Literal
import logging

from lume_services.services.scheduling.files import KUBERNETES_JOB_TEMPLATE_FILE

from lume_services.services.scheduling.backends import Backend, ServerRunConfig

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


class KubernetesRunConfig(ServerRunConfig):
    image_pull_secrets: Optional[List[str]]
    job_template: ... YAMLFile...
    job_template_path: ...
    service_account_name: ...
    image_pull_policy: Literal["Always", "IfNotPresent", "Never"] = "IfNotPresent"
    cpu_limit: float = 1.0
    cpu_request: float = 0.5
    memory_limit: Union[str, int] = None
    memory_request: Union[str, int] = None


    # VALIDATE JOB TEMPLATE
    # job_template = file_service.read(
    #        self.config.job_template.filesystem_identifier,
    #        self.config.job_template.filepath,
    #        YAMLSerializer,
    #    )


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


class KubernetesBackend(Backend):
    run_config: KubernetesRunConfig
    ...
