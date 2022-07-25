from pkg_resources import resource_filename
import yaml

_KUBERNETES_JOB_TEMPLATE_FILE = resource_filename(
    "lume_services.services.scheduling.files", "kubernetes_job.yaml"
)

KUBERNETES_JOB_TEMPLATE = None


def _initialize_job_template():
    global KUBERNETES_JOB_TEMPLATE, _KUBERNETES_JOB_TEMPLATE_FILE
    if KUBERNETES_JOB_TEMPLATE is None:
        with open(_KUBERNETES_JOB_TEMPLATE_FILE, "r") as f:
            KUBERNETES_JOB_TEMPLATE = yaml.safe_load(f)


if not KUBERNETES_JOB_TEMPLATE:
    _initialize_job_template()
