from pydantic import BaseSettings, BaseModel, Field
from prefect.run_configs import KubernetesRun
from typing import List
import yaml

from lume_services.data.file import FileService
from lume_services.context import Context
from dependency_injector.wiring import Provide

from lume_services.data.file.serializers.yaml import YAMLSerializer
from lume_services.scheduling.prefect.files import KUBERNETES_JOB_TEMPLATE_FILE

from lume_services.scheduling.prefect.config import BackendConfig, BackendConfig


class KubernetesCPURequest(BaseModel):
    limit: float = 1.0
    request: float = 0.5


class KubernetesMemoryRequest(BaseModel):
    limit: str = None
    request: str = None


class KubernetesResourceRequest(BaseModel):
    # for implementing device resources check https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
    cpu: KubernetesCPURequest = KubernetesCPURequest()
    memory: KubernetesMemoryRequest = KubernetesMemoryRequest()


class KubernetesJobTemplate(BaseModel):
    filepath: str = KUBERNETES_JOB_TEMPLATE_FILE
    filesystem_identifier: str


class KubernetesJobConfig(BackendConfig):
    job_template: KubernetesJobTemplate = None
    image_pull_policy: str = "IfNotPresent"  # Always, IfNotPresent, Never
    resource_request: KubernetesResourceRequest = KubernetesResourceRequest()
    image: str = None

    def load_job_config(
        self, file_service: FileService = Provide[Context.file_service]
    ):

        job_template = file_service.read(
            self.config.job_template.filesystem_identifier,
            self.config.job_template.filepath,
            YAMLSerializer,
        )

        if self.resource_request is not None:
            job_template["spec"]["template"]["spec"]["containers"][0][
                "resources"
            ] = self.resource_request.dict(exclude_none=True)

        return KubernetesRun(
            image_pull_policy=self.image_pull_policy,
            image=self.image,
            cpu_limit=self.resource_request.cpu.limit,
            cpu_request=self.resource_request.cpu.request,
            memory_limit=self.resource_request.memory.limit,
            memory_request=self.resource_request.memory.request,
            # service_account_name
            # image_pull_secrets
            # labels
            # env
            job_template=job_template,
        )
