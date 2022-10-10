import os
import re
import subprocess
from pymongo import MongoClient
import pymysql
import time
import timeit
from contextlib import contextmanager
from prefect import Client

import logging
from lume_services.docker.files import DOCKER_COMPOSE
from lume_services.config import LUMEServicesSettings

# from lume_services.config import LUMEServicesSettings
logger = logging.getLogger(__name__)


_BASE_SETUP_COMMAND = "up -d"
_UI_SETUP_COMMAND = "--profile with_ui up -d"
_CLEANUP_COMMANDS = ["down -v", "rm --stop --force"]
_PERSIST_CLEANUP_COMMANDS = ["stop"]


def check_mongodb_ready(lume_services_settings: LUMEServicesSettings):
    mongodb_config = lume_services_settings.results_db

    try:
        MongoClient(
            **mongodb_config.dict(by_alias=True, exclude_none=True),
            password=mongodb_config.password.get_secret_value(),
            connectTimeoutMS=20000,
            connect=True,
        )
        return True

    except Exception as e:
        logger.error("Error in mongodb check: %s", e)
        return False


def check_mysql_ready(lume_services_settings: LUMEServicesSettings):
    mysql_config = lume_services_settings.model_db

    try:
        pymysql.connect(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password.get_secret_value(),
        )
        return True
    except Exception as e:
        logger.info("Error in mysql check: %s", e)
        return False


def check_prefect_ready(lume_services_settings: LUMEServicesSettings):
    host = lume_services_settings.prefect.server.host
    port = lume_services_settings.prefect.server.host_port

    try:
        client = Client(api_server=f"{host}:{port}")
        client.graphql("query{hello}", raise_on_error=True)
        return True
    except Exception as e:
        logger.error("Error in prefect check: %s", e)
        return False


_HEALTHCHECKS = {
    "mongodb": check_mongodb_ready,
    "mysql": check_mysql_ready,
    "prefect": check_prefect_ready,
}


def execute(command, success_codes=(0,)):
    """Run a shell command."""
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True, env=os.environ
        )
        status = 0

    except subprocess.CalledProcessError as error:
        output = error.output or b""
        status = error.returncode
        command = error.cmd

    if status not in success_codes:
        logger.info(dict(os.environ))
        logger.error(f"Subrocess {command} failed with output: {output}")
        raise Exception(
            'Command {} returned {}: """{}""".'.format(
                command, status, output.decode("utf-8")
            )
        )
    return output


def get_docker_ip():
    # When talking to the Docker daemon via a UNIX socket, route all TCP
    # traffic to docker containers via the TCP loopback interface.
    docker_host = os.environ.get("DOCKER_HOST", "").strip()
    if not docker_host:
        return "127.0.0.1"

    match = re.match(r"^tcp://(.+?):\d+$", docker_host)
    if not match:
        raise ValueError('Invalid value for DOCKER_HOST: "%s".' % (docker_host,))
    return match.group(1)


class Services:
    def __init__(self, compose_file, project_name, lume_services_settings):
        self._compose_file = compose_file
        self._project_name = project_name
        self._lume_services_settings = lume_services_settings

    def execute(self, subcommand):
        command = "docker-compose"
        command += ' -f "{}"'.format(self._compose_file)
        command += ' -p "{}" {}'.format(self._project_name, subcommand)
        return execute(command)

    def wait_until_responsive(
        self,
        timeout: float,
        pause: float,
        clock=timeit.default_timer,
    ):
        """Wait until services are responsive."""

        ref = clock()
        now = ref
        status = {key: False for key in _HEALTHCHECKS.keys()}
        while (now - ref) < timeout:
            status = {
                key: check(self._lume_services_settings)
                for key, check in _HEALTHCHECKS.items()
            }

            if all(status.values()):
                return

            time.sleep(pause)
            now = clock()

        failed = [service for service, status_ in status.items() if not status_]

        raise Exception("Timeout reached while waiting for: %s", ",".join(failed))


def get_cleanup_commands():
    return _CLEANUP_COMMANDS


def get_setup_command():
    return _BASE_SETUP_COMMAND


@contextmanager
def run_docker_services(
    lume_services_settings: LUMEServicesSettings,
    timeout: float,
    pause: float,
    project_name: str = "lume-services",
    ui: bool = False,
    persist: bool = False,
):
    """Context manager for executing dockerized services.

    Args:
        lume_services_settings (LUMEServicesSettings): LUME-services settings used to
            configure ports, passwords etc. for services.
        timeout (float): Total time for executing checks against services.
            Docker-compose will exit all services if checks do not succeed within this
            time window.
        pause (float): Pause between checks.
        project_name (str): Name of docker project.
        ui (bool): Whether to run UI service.
        persist (bool): Whether to persist resources after shutdown. If you are
            persisting the volumes, you must manage the artifacts using docker tools.

    Yields:
        Services

    """
    logger.info(f"Running services in environment: {dict(os.environ)}")
    services = Services(DOCKER_COMPOSE, project_name, lume_services_settings)

    if ui:
        cmd = _UI_SETUP_COMMAND
    else:
        cmd = _BASE_SETUP_COMMAND

    # setup containers.
    logger.info("Setting up docker-compose containers.")
    try:
        services.execute(cmd)

    except Exception as e:

        cleanup_commands = _CLEANUP_COMMANDS
        if persist:
            cleanup_commands = _PERSIST_CLEANUP_COMMANDS

        for cmd in cleanup_commands:
            logger.debug("Executing cmd %s", cmd)
            try:
                services.execute(cmd)
            except Exception as cleanup_exception:
                logger.warning(
                    f"Cleanup command exception for {cmd}: {cleanup_exception}"
                )
                pass
        raise e

    # now we perform startup checks
    try:
        try:
            services.wait_until_responsive(timeout, pause)
            yield services

        except Exception as e:
            logger.exception("Exception when composing services: %s", e)

            for cmd in _CLEANUP_COMMANDS:
                logger.debug("Executing cmd %s", cmd)
                try:
                    services.execute(cmd)
                except Exception as cleanup_exception:
                    logger.warning(
                        f"Cleanup command exception for {cmd}: \
                            {cleanup_exception}"
                    )
                    pass
            raise e

    # yield services
    finally:
        # Clean up.
        cleanup_commands = _CLEANUP_COMMANDS
        if persist:
            cleanup_commands = _PERSIST_CLEANUP_COMMANDS

        for cmd in cleanup_commands:
            logger.debug("Executing cmd %s", cmd)
            try:
                services.execute(cmd)
            except Exception as cleanup_exception:
                logger.warning(
                    f"Cleanup command exception for {cmd}: {cleanup_exception}"
                )
                pass

        logger.info("Finished executing docker-compose shutdown commands.")
