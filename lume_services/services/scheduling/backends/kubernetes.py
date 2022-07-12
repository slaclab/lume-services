from pydantic import BaseModel, validator
from prefect.run_configs import KubernetesRun
from typing import List, Optional, Dict, Union
import logging

from lume_services.services.scheduling.files import KUBERNETES_JOB_TEMPLATE_FILE

from lume_services.services.scheduling.backends import Backend

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


class KubernetesCPURequest(BaseModel):
    limit: float = 1.0
    request: float = 0.5


class KubernetesMemoryRequest(BaseModel):
    limit: Union[str, int] = None
    request: Union[str, int] = None

    @validator("limit", "request")
    def validate_request(cls, v):
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


class KubernetesResourceRequest(BaseModel):
    # for implementing device resources check
    # https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
    cpu: KubernetesCPURequest = KubernetesCPURequest()
    memory: KubernetesMemoryRequest = KubernetesMemoryRequest()


class KubernetesJobTemplate(BaseModel):
    filepath: str = KUBERNETES_JOB_TEMPLATE_FILE
    filesystem_identifier: str
    job_template: dict

    # VALIDATE JOB TEMPLATE
    # job_template = file_service.read(
    #        self.config.job_template.filesystem_identifier,
    #        self.config.job_template.filepath,
    #        YAMLSerializer,
    #    )


class KubernetesRunConfig(BaseModel):
    resource_request: Optional[KubernetesResourceRequest]
    env: Optional[Dict[str, str]]
    image: Optional[str]
    image_pull_secrets: Optional[List[str]]


#   labels: Optional[List[str]]
#   service_account_name = Optional[str]


class KubernetesBackend(Backend):
    job_template: KubernetesJobTemplate = None
    image_pull_policy: str = "IfNotPresent"  # Always, IfNotPresent, Never

    # default image
    default_image: str = None

    def get_run_config(
        self,
        run_config: KubernetesRunConfig,
    ):

        return KubernetesRun(
            image_pull_policy=self.image_pull_policy,
            image=self.image,
            cpu_limit=run_config.resource_request.cpu.limit,
            cpu_request=run_config.resource_request.cpu.request,
            memory_limit=run_config.resource_request.memory.limit,
            memory_request=run_config.resource_request.memory.request,
            image_pull_secrets=run_config.image_pull_secrets,
            env=run_config.env,
            job_template=run_config.job_template,
            # labels = run_config.labels,
            # service_account_name = run_config.service_account_name
        )
