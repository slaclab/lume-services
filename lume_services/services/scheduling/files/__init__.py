from pkg_resources import resource_filename


KUBERNETES_JOB_TEMPLATE_FILE = resource_filename(
    "lume_services.scheduling.prefect.files", "kubernetes_job.yaml"
)
