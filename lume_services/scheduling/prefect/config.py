from pydantic import BaseSettings
import prefect

from lume_services.scheduling.prefect.backends import Backend


class PrefectConfig(BaseSettings):
    api: str = "http://localhost:4200"
    graphql: str = "http://localhost:4200/graphql"
    ui: str = "http://localhost:8080"

    backend: Backend

    def apply(self):
        prefect.config.update(backend = self.backend)
        prefect.config.cloud.update(api = self.api)
        prefect.config.cloud.update(graphql = self.graphql)
        prefect.config.server.ui.update(endpoint = self.ui)

