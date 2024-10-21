import os
import pytest
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

from lume_services.errors import (
    EmptyResultError,
    FlowFailedError,
    LocalBackendError,
    TaskNotInFlowError,
)
from lume_services.utils import docker_api_version as docker_api_version_util
from lume_services.tests.flows.lume_services_test_flows.flow1 import flow
from lume_services.tests.flows.lume_services_test_flows.failure_flow import (
    flow as failure_flow,
)
from lume_services import config

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def docker_api_version():
    return docker_api_version_util()


class TestRunConfigs:
    labels = ["test"]
    image = "placeholder_image_tag"

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
    # from https://github.com/docker/docker-py/blob/a48a5a9647761406d66e8271f19fab7fa0c5f582/tests/ unit/dockertypes_test.py#L15 # noqa
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

    def test_local_run_config(self, lume_env):
        # check construction
        run_config = LocalRunConfig(labels=self.labels, env=lume_env)

        # check that the working_dir is the same as pytest workdir
        assert run_config.working_dir == str(os.getcwd())
        # check env assignment
        assert run_config.env == lume_env
        # check label assignment
        assert all([label in run_config.labels for label in self.labels])
        # check build of prefect run config
        prefect_run_config = run_config.build()
        assert isinstance(prefect_run_config, (LocalRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env
        assert prefect_run_config.working_dir == run_config.working_dir

    def test_docker_run_config(self, docker_api_version, lume_env):
        try:
            run_config = DockerRunConfig(
                labels=self.labels,
                env=lume_env,
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

    def test_kubernetes_run_config(self, lume_env):

        # test construction w/o job template
        run_config = KubernetesRunConfig(
            labels=self.labels,
            env=lume_env,
        )
        prefect_run_config = run_config.build()

        assert isinstance(prefect_run_config, (KubernetesRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env

        # packaged yaml should be applied in case of missing job template and path
        assert run_config.job_template is not None


class TestLocalBackend:
    @pytest.fixture(scope="class")
    def run_config(self, lume_env):
        return LocalRunConfig(labels=["test"], env=lume_env)

    @pytest.fixture(scope="class")
    def backend(self):
        return LocalBackend()

    @pytest.fixture(scope="class")
    def data(self, tmp_path_factory):
        temp_path = tmp_path_factory.mktemp("test_local_backend")
        return {
            "text1": "hey",
            "text2": " you",
            "filename": f"{temp_path}/test_local_backend.txt",
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

    def test_run_flow(self, backend, data, run_config):
        backend.run(data, run_config, flow=flow)

    def test_run_flow_and_return(self, backend, data, run_config):
        # get all results
        res = backend.run_and_return(data, run_config, flow=flow)
        assert isinstance(res, (dict,))

        res = backend.run_and_return(
            data, run_config, flow=flow, task_name="save_text_file"
        )
        assert isinstance(res, (dict,))
        logger.debug(str(res))

        res = backend.run_and_return(
            data, run_config, flow=flow, task_name="append_text"
        )
        assert isinstance(res, (str,))
        assert res == f"{data['text1']}{data['text2']}"

    def test_task_not_in_flow_error(self, backend, data, run_config):
        with pytest.raises(TaskNotInFlowError):
            backend.run_and_return(
                data, run_config, flow=flow, task_name="missing_task"
            )

    def test_empty_result_error(self, backend, data, run_config):
        with pytest.raises(EmptyResultError):
            backend.run_and_return(
                data, run_config, flow=flow, task_name="configure_lume_services"
            )

    def test_failure_check(self, backend, run_config):
        with pytest.raises(FlowFailedError):
            backend.run_and_return(None, run_config, flow=failure_flow)


class TestDockerBackend:
    @pytest.mark.usefixtures("scheduling_service")
    @pytest.fixture(scope="class")
    def backend(self, lume_services_settings):
        config.configure(lume_services_settings)

        return DockerBackend(config=lume_services_settings.prefect)

    @pytest.fixture(scope="class")
    def project_name(self, backend):
        project_name = "test_docker_backend"
        backend.create_project(project_name=project_name)
        return project_name

    # tests flow registration
    @pytest.fixture(scope="class")
    def flow_id(self, backend, project_name, prefect_docker_tag):
        return backend.register_flow(
            flow,
            project_name=project_name,
            image=prefect_docker_tag,
            labels=["lume-services"],
        )

    @pytest.fixture(scope="class")
    def failure_flow_id(self, backend, project_name, prefect_docker_tag):
        return backend.register_flow(
            failure_flow,
            project_name=project_name,
            image=prefect_docker_tag,
            labels=["lume-services"],
        )

    @pytest.fixture(scope="class")
    def parameters(self, mounted_filesystem):
        return {
            "text1": "hey",
            "text2": " you",
            "filename": f"{mounted_filesystem.mount_alias}/test_docker_backend.txt",
            "filesystem_identifier": mounted_filesystem.identifier,
        }

    def test_run_flow_type_error(self, backend, parameters, docker_run_config):
        with pytest.raises(TypeError):
            backend.run(parameters, docker_run_config, flow_id=flow)

    def test_run_flow(self, backend, parameters, docker_run_config, flow_id):
        backend.run(parameters, docker_run_config, flow_id=flow_id)

    @pytest.mark.skip()
    def test_run_flow_and_return(self, backend, parameters, docker_run_config, flow_id):
        # get all results
        res = backend.run_and_return(parameters, docker_run_config, flow_id=flow_id)
        assert isinstance(res, (dict,))

        res = backend.run_and_return(
            parameters, docker_run_config, flow_id=flow_id, task_name="save_text_file"
        )
        assert isinstance(res, (dict,))

    @pytest.mark.skip()
    def test_task_not_in_flow_error(
        self, backend, parameters, flow_id, docker_run_config
    ):
        with pytest.raises(TaskNotInFlowError):
            backend.run_and_return(
                parameters, docker_run_config, flow_id=flow_id, task_name="missing_task"
            )

    @pytest.mark.skip()
    def test_empty_result_error(self, backend, parameters, flow_id, docker_run_config):
        with pytest.raises(EmptyResultError):
            backend.run_and_return(
                parameters,
                docker_run_config,
                flow_id=flow_id,
                task_name="configure_lume_services",
            )

    def test_failure_check(self, backend, docker_run_config, failure_flow_id):
        with pytest.raises(FlowFailedError):
            backend.run_and_return(None, docker_run_config, flow_id=failure_flow_id)


@pytest.mark.skip()
class TestKubernetesBackend:
    ...
