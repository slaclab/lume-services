from lume_services import config
from prefect import task
import logging
import os
import json


logger = logging.getLogger(__name__)


@task
def configure_services():
    """Configure services from environment."""
    logger.debug(json.dumps(dict(os.environ)))
    config.configure()
