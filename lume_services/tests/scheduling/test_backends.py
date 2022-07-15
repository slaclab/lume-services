import os
from pydantic import ValidationError
import pytest
from docker.errors import DockerException
from prefect.run_configs import LocalRun, DockerRun, KubernetesRun
from lume_services.services.scheduling.backends.kubernetes import (
    KubernetesRunConfig,
)
from lume_services.services.scheduling.backends.docker import (
    DockerBackend,
    DockerRunConfig,
)

from lume_services.services.scheduling.backends.local import (
    LocalBackend,
    LocalRunConfig,
)

from lume_services.errors import LocalBackendError, TaskNotInFlowError
from lume_services.utils import docker_api_version as docker_api_version_util
from lume_services.tests.files.flows.flow1 import flow as flow
from lume_services.tests.files.flows.failure_flow import flow as failure_flow

from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def docker_api_version():
    return docker_api_version_util()


class TestRunConfigs:
    labels = ["test"]
    env = dict(os.environ)
    image = "placeholder_image_tag"
    docker_api_version_min = "1.35"  # lowest allowed
    docker_api_version_latest = "1.41"  # latest tested

    docker_host_config = {
        "cpu_quota": 2,
        "cpu_period": 1999,
        "blkio_weight": 1999,
        "blkio_weight_device": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_read_bps": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_write_bps": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_read_iops": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_write_iops": [{"Path": "/dev/sda", "Rate": 1000}],
        "shm_size": 67108864,
        "oom_kill_disable": True,
        "userns_mode": "host",
        "oom_score_adj": 100,
        "dns_opt": ["use-vc", "no-tld-query"],
        "mem_reservation": "67108864",
        "kernel_memory": 67108864,
        "pids_limit": 1024,
        "isolation": "hyperv",
        "pid_mode": "host",
        "mem_swappiness": 40,
        "volume_driver": "local",
        "cpu_count": 2,
        "cpu_percent": 15,
        "nano_cpus": 1000,
        "cpu_rt_period": 100,
        "cpu_rt_runtime": 1000,
    }
    # from https://github.com/docker/docker-py/blob/a48a5a9647761406d66e8271f19fab7fa0c5f582/tests/unit/dockertypes_test.py#L15 # noqa
    broken_docker_host_config = {
        "shm_size": ["test"],
        "mem_reservation": ["test"],
        "kernel_memory": ["test"],
        "cpu_count": ["1"],
        "cpu_percent": ["test"],
        "nano_cpus": "0",
        "cpu_rt_period": "1000",
        "cpu_rt_runtime": "1000",
    }
    docker_ports = [3000]

    def test_local_run_config(self):
        # check construction
        run_config = LocalRunConfig(labels=self.labels, env=self.env)

        # check that the working_dir is the same as pytest workdir
        assert run_config.working_dir == str(os.getcwd())
        # check env assignment
        assert run_config.env == self.env
        # check label assignment
        assert all([label in run_config.labels for label in self.labels])
        # check build of prefect run config
        prefect_run_config = run_config.build()
        assert isinstance(prefect_run_config, (LocalRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env
        assert prefect_run_config.working_dir == run_config.working_dir

    def test_docker_run_config(self, docker_api_version):
        self.docker_host_config["version"] = docker_api_version
        # check construction missing image
        with pytest.raises(ValidationError):
            DockerRunConfig(
                labels=self.labels,
                env=self.env,
                ports=self.docker_ports,
                host_config=self.docker_host_config,
            )

        # check w/ auto version
        try:
            run_config = DockerRunConfig(
                labels=self.labels,
                env=self.env,
                image=self.image,
                ports=self.docker_ports,
                host_config=self.docker_host_config,
            )
        except Exception as e:
            logger.error("Error using api version %s", docker_api_version)
            raise e

        prefect_run_config = run_config.build()

        assert isinstance(prefect_run_config, (DockerRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env

    def test_docker_run_config_latest_api(self):

        # check failure on faulty values
        for key, values in self.broken_docker_host_config.items():
            for value in values:
                with pytest.raises((ValidationError, DockerException)):
                    try:
                        # test latest version
                        DockerRunConfig(
                            labels=self.labels,
                            image=self.image,
                            env=self.env,
                            ports=self.docker_ports,
                            host_config={
                                "version": self.docker_api_version_latest,
                                key: value,
                            },
                        )
                        logger.error(
                            "Error Testing docker run config w/ latest version for %s = %s",
                            key,
                            value,
                        )
                    except ValidationError as err:
                        logger.error(
                            "Error Testing docker run config w/ latest version for %s = %s",
                            key,
                            value,
                        )
                        raise err

    def test_docker_run_config_min_api(self):
        # check failure on faulty values
        for key, values in self.broken_docker_host_config.items():
            for value in values:
                with pytest.raises((ValidationError, DockerException)):
                    # test min version
                    try:
                        # test latest version
                        DockerRunConfig(
                            labels=self.labels,
                            image=self.image,
                            env=self.env,
                            ports=self.docker_ports,
                            host_config={
                                "version": self.docker_api_version_min,
                                key: value,
                            },
                        )
                    except ValidationError as err:
                        logger.error(
                            "Error Testing docker run config w/ min version for %s = %s",
                            key,
                            value,
                        )
                        raise err

    @pytest.mark.skip()
    def test_kubernetes_run_config(self):

        # test construction w/o job template
        run_config = KubernetesRunConfig(
            labels=self.labels,
            env=self.env,
        )
        prefect_run_config = run_config.build()

        assert isinstance(prefect_run_config, (KubernetesRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env

        # packaged yaml should be applied in case of missing job template and path
        assert run_config.job_template is not None


class TestLocalBackend:
    run_config = LocalRunConfig(labels=["test"], env=dict(os.environ))

    @pytest.fixture()
    def backend(self):
        return LocalBackend(run_config=self.run_config)

    @pytest.fixture()
    def data(self, tmp_path):
        return {
            "text1": "hey",
            "text2": " you",
            "filename": f"{tmp_path}/test_local_backend.txt",
            "filesystem_identifier": "local",
        }

    def test_load_flow_error(self, backend):
        with pytest.raises(LocalBackendError):
            backend.load_flow("placeholder_flow_name", "placeholder_project_name")

    def test_create_project_error(self, backend):
        with pytest.raises(LocalBackendError):
            backend.create_project("placeholder_project_name")

    def test_register_flow_error(self, backend):
        with pytest.raises(LocalBackendError):
            backend.register_flow(flow, "placeholder_project_name")

    def test_run_flow(self, backend, data):
        backend.run(data, self.run_config, flow=flow)

    def test_run_flow_and_return(self, backend, data):
        # get all results
        res = backend.run_and_return(data, self.run_config, flow=flow)
        assert isinstance(res, (dict,))

        res = backend.run_and_return(
            data, self.run_config, flow=flow, task_name="save_text_file"
        )
        assert isinstance(res, (dict,))
        logger.debug(str(res))

        res = backend.run_and_return(
            data, self.run_config, flow=flow, task_name="append_text"
        )
        assert isinstance(res, (str,))
        assert res == f"{data['text1']}{data['text2']}"

    def test_failure_check(self, backend):
        res = backend.run_and_return(None, self.run_config, flow=failure_flow)


class TestDockerBackend:
    @pytest.fixture()
    def run_config(self, docker_api_version, prefect_docker_tag, prefect_docker_agent):
        docker_host_config = {
            "version": docker_api_version,
            "cpu_quota": 2,
            "cpu_period": 1999,
            "blkio_weight": 1999,
            "blkio_weight_device": [{"Path": "/dev/sda", "Rate": 1000}],
            "device_read_bps": [{"Path": "/dev/sda", "Rate": 1000}],
            "device_write_bps": [{"Path": "/dev/sda", "Rate": 1000}],
            "device_read_iops": [{"Path": "/dev/sda", "Rate": 1000}],
            "device_write_iops": [{"Path": "/dev/sda", "Rate": 1000}],
            "shm_size": 67108864,
            "oom_kill_disable": True,
            "userns_mode": "host",
            "oom_score_adj": 100,
            "dns_opt": ["use-vc", "no-tld-query"],
            "mem_reservation": "67108864",
            "kernel_memory": 67108864,
            "pids_limit": 1024,
            "isolation": "hyperv",
            "pid_mode": "host",
            "mem_swappiness": 40,
            "volume_driver": "local",
            "cpu_count": 2,
            "cpu_percent": 15,
            "nano_cpus": 1000,
            "cpu_rt_period": 100,
            "cpu_rt_runtime": 1000,
        }
        return DockerRunConfig(
            host_config=docker_host_config,
            image=prefect_docker_tag,
            labels=["test"],
            ports=[3000],
        )

    @pytest.fixture()
    def backend(self, run_config):
        return DockerBackend(config=run_config)

    @pytest.fixture()
    def project_name(self, prefect_client):
        project_name = "test_docker_backend"
        prefect_client.create_project(project_name=project_name)
        return project_name

    # tests flow registration
    @pytest.fixture()
    def flow_id(self, backend, project_name):
        return backend.register_flow(
            flow, project_name=project_name, image_tag=prefect_docker_tag
        )

    @pytest.fixture()
    def failure_flow_id(self, backend, project_name):
        return backend.register_flow(
            failure_flow, project_name=project_name, image_tag=prefect_docker_tag
        )

    @pytest.fixture()
    def data(self, tmp_path):
        return {
            "text1": "hey",
            "text2": " you",
            "filename": f"{tmp_path}/test_local_backend.txt",
            "filesystem_identifier": "local",
        }

    def test_run_flow_type_error(self, backend, data, run_config):
        with pytest.raises(TypeError):
            backend.run(data, run_config, flow_id=flow)

    def test_run_flow(self, backend, data, run_config, flow_id):
        backend.run(data, run_config, flow_id=flow_id)

    def test_run_flow_and_return(self, backend, data, run_config, flow_id):
        # get all results
        res = backend.run_and_return(data, run_config, flow_id=flow_id)
        assert isinstance(res, (dict,))

        res = backend.run_and_return(
            data, run_config, flow_id=flow_id, task_name="save_text_file"
        )
        assert isinstance(res, (dict,))
        logger.debug(str(res))

        res = backend.run_and_return(
            data, run_config, flow_id=flow_id, task_name="append_text"
        )
        assert isinstance(res, (str,))
        assert res == f"{data['text1']}{data['text2']}"

    def test_task_not_in_flow_error(self, backend, data, flow_id, run_config):
        with pytest.raises(TaskNotInFlowError):
            backend.run_and_return(
                data, run_config, flow_id=flow_id, task_name="missing_task"
            )

    # test task not in flow
    def test_empty_result_error(self, backend, data, flow_id, run_config):
        with pytest.raises(TaskNotInFlowError):
            backend.run_and_return(
                data, run_config, flow_id=flow_id, task_name="configure_services"
            )

    def test_failure_check(self, backend, run_config, failure_flow_id):
        res = backend.run_and_return(None, run_config, flow=failure_flow_id)


@pytest.mark.skip()
class TestKubernetesBackend:
    ...
