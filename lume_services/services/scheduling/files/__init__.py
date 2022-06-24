from pkg_resources import resource_filename


KUBERNETES_JOB_TEMPLATE_FILE = resource_filename(
    "lume_services.services.scheduling.files", "kubernetes_job.yaml"
)
