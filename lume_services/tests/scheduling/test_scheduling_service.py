import prefect
from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401


class TestPrefectConfig:
    def test_prefect_config(self, prefect_config):
        # check assignment, has already been applied
        assert prefect.config.backend == prefect_config.backend.backend_type
        assert prefect.config.debug == prefect_config.debug
        assert prefect.config.home_dir == prefect_config.home_dir

        # check server values
        for key, value in prefect_config.server.dict().items():
            attr = getattr(prefect.config.server, key)
            assert attr == value

        # check graphql values
        for key, value in prefect_config.graphql.dict().items():
            attr = getattr(prefect.config.server.graphql, key)
            assert attr == value

        # check hasura values
        for key, value in prefect_config.hasura.dict().items():
            attr = getattr(prefect.config.server.hasura, key)
            assert attr == value

        # check ui values
        for key, value in prefect_config.ui.dict().items():
            attr = getattr(prefect.config.server.ui, key)
            assert attr == value

        # check graphql values
        for key, value in prefect_config.telemetry.dict().items():
            attr = getattr(prefect.config.server.telemetry, key)
            assert attr == value
