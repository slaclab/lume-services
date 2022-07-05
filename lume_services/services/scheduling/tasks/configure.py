from lume_services import config
from prefect import task


@task
def configure_services():
    config.configure()
