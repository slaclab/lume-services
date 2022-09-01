import pytest
import logging
from lume_services.environment.solver import _GITHUB_TARBALL_TEMPLATE
from lume_services.environment.solver import (
    EnvironmentResolver,
    EnvironmentResolverConfig,
)


logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.github.com/repos/jacquelinegarrahan/my-model/tarball/v0.0",
        pytest.param(
            "api.github.com/repos/jacquelinegarrahan/my-model/tarball/v0.0",
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            "https://api.github.com/repos/jacquelinegarrahan/my-model/zip/v0.0",
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            "https://api.github.com/repos/tarball/v0.0", marks=pytest.mark.xfail
        ),
    ],
)  # TODO CHANGE TO SLACLAB
def test_tarball_template(url):
    assert _GITHUB_TARBALL_TEMPLATE.match(url)


class TestModelDB:

    # model
    author = "Jackie Garrahan"
    laboratory = "slac"
    facility = "lcls"
    beampath = "cu_hxr"
    description = "test_model"

    # deployment
    version = "v0.0"
    sha256 = "placeholder"
    asset_dir = (None,)  # opt
    source = "my source"
    is_live = 1
    image = "placeholder"

    # project
    project = "my_project"
    project_description = "placeholder"

    # flow
    flow_id_placeholder = "test"
    flow_name = "my_test_flow"
    dependencies = [
        {
            "name": "matplotlib",
            "type": "conda",
            "version": "3.5.3",
            "source": "/Users/jgarra/sandbox/lume-services/dev/matplotlib-3.5.3.tar.gz",
        }
    ]

    @pytest.fixture(scope="class")
    def model_id(self, model_db_service):
        model_id = model_db_service.store_model(
            author=self.author,
            laboratory=self.laboratory,
            facility=self.facility,
            beampath=self.beampath,
            description=self.description,
        )
        assert model_id is not None

        return model_id

    def test_missing_author(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_model(
                laboratory=self.laboratory,
                facility=self.facility,
                beampath=self.beampath,
                description=self.description,
            )

    def test_missing_laboratory(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_model(
                author=self.author,
                facility=self.facility,
                beampath=self.beampath,
                description=self.description,
            )

    def test_missing_facility(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_model(
                author=self.author,
                laboratory=self.laboratory,
                beampath=self.beampath,
                description=self.description,
            )

    def test_missing_beampath(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_model(
                author=self.author,
                laboratory=self.laboratory,
                facility=self.facility,
                description=self.description,
            )

    def test_missing_description(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_model(
                author=self.author,
                laboratory=self.laboratory,
                facility=self.facility,
                beampath=self.beampath,
            )

    def test_get_model(self, model_db_service, model_id):

        model = model_db_service.get_model(model_id=model_id)

        assert model.model_id == model_id

    @pytest.fixture(scope="class")
    def deployment_id(self, model_db_service, model_id):

        deployment_id = model_db_service.store_deployment(
            model_id=model_id,
            version=self.version,
            asset_dir=self.asset_dir,
            sha256=self.sha256,
            source=self.source,
            is_live=self.is_live,
            image=self.image,
        )

        assert deployment_id is not None

        return deployment_id

    # test missing deployment info

    def test_get_deployment(self, model_db_service, deployment_id):

        deployment = model_db_service.get_deployment(deployment_id=deployment_id)

        assert deployment.deployment_id == deployment_id

    def test_get_model_from_deployment(self, model_db_service, deployment_id):

        deployment = model_db_service.get_deployment(deployment_id=deployment_id)

        deployment.model

    @pytest.fixture(scope="class")
    def project_name(self, model_db_service):
        project_name = model_db_service.store_project(
            project_name=self.project, description=self.project_description
        )

        assert project_name is not None

        return project_name

    def test_missing_project_name(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_project(description=self.project_description)

    def test_missing_project_description(self, model_db_service):
        with pytest.raises(TypeError):
            model_db_service.store_project(project_name=self.project)

    @pytest.fixture(scope="class")
    def flow_id(self, model_db_service, deployment_id, project_name):
        logger.info(deployment_id)
        flow_id = model_db_service.store_flow(
            project_name=project_name,
            deployment_id=deployment_id,
            flow_id=self.flow_id_placeholder,
            flow_name=self.flow_name,
        )

        assert flow_id is not None

        return flow_id

    @pytest.fixture(scope="class")
    def dependencies(self, model_db_service, deployment_id):
        model_db_service.store_dependencies(
            self.dependencies, deployment_id=deployment_id
        )

    # test missing flow info
    def test_missing_flow_project_name(self, model_db_service, deployment_id, flow_id):
        with pytest.raises(TypeError):
            model_db_service.store_flow(
                deployment_id=deployment_id, flow_id=flow_id, flow_name=self.flow_name
            )

    def test_missing_flow_deployment_id(self, model_db_service, project_name, flow_id):
        with pytest.raises(TypeError):
            model_db_service.store_flow(
                project_name=project_name, flow_id=flow_id, flow_name=self.flow_name
            )

    def test_missing_flow_flow_id(self, model_db_service, project_name, deployment_id):
        with pytest.raises(TypeError):
            model_db_service.store_flow(
                project_name=project_name,
                deployment_id=deployment_id,
                flow_name=self.flow_name,
            )

    def test_missing_flow_flow_name(
        self, model_db_service, project_name, deployment_id, flow_id
    ):
        with pytest.raises(TypeError):
            model_db_service.store_flow(
                project_name=project_name, deployment_id=deployment_id, flow_id=flow_id
            )

    def test_get_latest_deployment(self, model_db_service, model_id, deployment_id):
        deployment = model_db_service.get_latest_deployment(model_id=model_id)

        assert deployment.deployment_id == deployment_id

    def test_get_latest_deployment_bad_sig(self, model_db_service, model_id):
        with pytest.raises(ValueError):
            model_db_service.get_latest_deployment(model_name=model_id)

    def test_get_project(self, model_db_service, project_name):
        project = model_db_service.get_project(project_name=project_name)

        assert project.project_name == project_name

    def test_get_project_bad_sig(self, model_db_service, project_name):
        with pytest.raises(ValueError):
            model_db_service.get_project(project_id=project_name)

    def test_get_flow(self, model_db_service, flow_id):
        flow = model_db_service.get_flow(flow_id=flow_id)

        assert flow.flow_id == flow_id

    def test_get_flow_bad_sig(self, model_db_service, flow_id):
        with pytest.raises(ValueError):
            model_db_service.get_flow(flow_identifier=flow_id)


class TestEnvironmentResolution:
    @pytest.fixture(scope="class")
    def local_pip_repo(self, tmp_path_factory):
        return str(tmp_path_factory.mktemp("mounted_dir"))

    @pytest.fixture(scope="class")
    def local_conda_channel_directory(self, tmp_path_factory):
        return str(tmp_path_factory.mktemp("mounted_dir"))

    def test_resolution_dry_run(self, local_pip_repo, local_conda_channel_directory):
        config = EnvironmentResolverConfig(
            local_pip_repository=local_pip_repo,
            local_conda_channel_directory=local_conda_channel_directory,
        )

        resolver = EnvironmentResolver(config)
        resolver.solve(
            "https://github.com/jacquelinegarrahan/my-model/releases/download/v0.0.6/my_model-0.0.6.tar.gz",  # noqa
            dry_run=True,
        )

    def test_resolution(self, local_pip_repo, local_conda_channel_directory):
        config = EnvironmentResolverConfig(
            local_pip_repository=local_pip_repo,
            local_conda_channel_directory=local_conda_channel_directory,
        )

        resolver = EnvironmentResolver(config)
        resolver.solve(
            "https://github.com/jacquelinegarrahan/my-model/releases/download/v0.0.6/my_model-0.0.6.tar.gz"  # noqa
        )
