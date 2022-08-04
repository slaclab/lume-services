import os
import re
import subprocess
import time
import timeit
from contextlib import contextmanager

import attr

import logging
from lume_services.docker.files import DOCKER_COMPOSE

logger = logging.getLogger(__name__)


_BASE_SETUP_COMMAND = "up -d"
_UI_SETUP_COMMAND = "--profile with_ui up -d"
_CLEANUP_COMMANDS = ["down -v", "rm --stop --force"]


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


@attr.s(frozen=True)
class Services:

    _docker_compose = attr.ib()
    _services = attr.ib(init=False, default=attr.Factory(dict))

    def port_for(self, service, container_port):
        """Return the "host" port for `service` and `container_port`.
        E.g. If the service is defined like this:
            version: '2'
            services:
              httpbin:
                build: .
                ports:
                  - "8000:80"
        this method will return 8000 for container_port=80.
        """

        # Lookup in the cache.
        cache = self._services.get(service, {}).get(container_port, None)
        if cache is not None:
            return cache

        output = self._docker_compose.execute("port %s %d" % (service, container_port))
        endpoint = output.strip().decode("utf-8")
        if not endpoint:
            raise ValueError(
                'Could not detect port for "%s:%d".' % (service, container_port)
            )

        # This handles messy output that might contain warnings or other text
        if len(endpoint.split("\n")) > 1:
            endpoint = endpoint.split("\n")[-1]

        # Usually, the IP address here is 0.0.0.0, so we don't use it.
        match = int(endpoint.split(":", 1)[1])

        # Store it in cache in case we request it multiple times.
        self._services.setdefault(service, {})[container_port] = match

        return match

    def wait_until_responsive(self, check, timeout, pause, clock=timeit.default_timer):
        """Wait until a service is responsive."""

        ref = clock()
        now = ref
        while (now - ref) < timeout:
            if check():
                return
            time.sleep(pause)
            now = clock()

        raise Exception("Timeout reached while waiting on service!")


def str_to_list(arg):
    if isinstance(arg, (list, tuple)):
        return arg
    return [arg]


@attr.s(frozen=True)
class DockerComposeExecutor:

    _compose_files = attr.ib(converter=str_to_list)
    _compose_project_name = attr.ib()

    def execute(self, subcommand):
        command = "docker-compose"
        for compose_file in self._compose_files:
            command += ' -f "{}"'.format(compose_file)
        command += ' -p "{}" {}'.format(self._compose_project_name, subcommand)
        return execute(command)


def get_cleanup_commands():
    return _CLEANUP_COMMANDS


def get_setup_command():
    return _BASE_SETUP_COMMAND


@contextmanager
def run_docker_services(project_name="lume-services", ui=False):
    logger.info(f"Running services in environment: {dict(os.environ)}")
    docker_compose = DockerComposeExecutor(DOCKER_COMPOSE, project_name)

    if ui:
        cmd = _UI_SETUP_COMMAND
    else:
        cmd = _BASE_SETUP_COMMAND

    # setup containers.
    try:
        docker_compose.execute(cmd)
    except Exception as e:
        for cmd in _CLEANUP_COMMANDS:
            try:
                docker_compose.execute(cmd)
            except Exception as cleanup_exception:
                logger.warning(
                    f"Cleanup command exception for {cmd}: {cleanup_exception.message}"
                )
                pass
        raise e

    try:
        # Let tests run.
        yield Services(docker_compose)
    # yield services
    finally:
        # Clean up.
        for cmd in _CLEANUP_COMMANDS:
            docker_compose.execute(cmd)
