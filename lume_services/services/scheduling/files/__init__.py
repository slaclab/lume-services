from pkg_resources import resource_filename

# from lume_services.files import YAMLFile

KUBERNETES_JOB_TEMPLATE_FILE = resource_filename(
    "lume_services.services.scheduling.files", "kubernetes_job.yaml"
)

# KUBERNETES_JOB_TEMPLATE_FILE = YAMLFile(
#    filename=_kubernetes_job_template_filename,
#    filesystem_identifier="local"
# )
