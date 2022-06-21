from lume_services.services.data.results import MongodbResultsDBConfig


class TestMongodbResultsDBConfig:
    def test_construction_to_uri(self):
        config = MongodbResultsDBConfig(
            database="results",
            host="localhost",
            user="user",
            port=3030,
            password="test",
        )

        assert not config.user
        assert config.uri is not None
