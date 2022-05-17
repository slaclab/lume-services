from __future__ import annotations

from prefect.engine.result.base import Result
from typing import Any
from dependency_injector.wiring import Provide

from lume_services.data.results import ResultsService
from lume_services.context import Context


class DBResult(Result):
    def __init__(
        self,
        *,
        model_type: str,
        results_service: ResultsService = Provide[Context.results_service],
        **kwargs,
    ):
        """Create a database results.

        Args:
            model_type (str): Must be a key member of the model_docs Enum passed to the
                ResultsService.
            results_service (ResultsService): Results database service.

        """
        self._results_service = results_service
        self._model_type = model_type

        # validate that model type is a member of model_docs enum
        self._results_service.validate_model_type(model_type)
        self._target = self._results_service.get_unique_field(model_type)

        if not self._model_type:
            raise ValueError("model type not provided")

        super().__init__(**kwargs)

    @property
    def results_service(
        self, results_service: ResultsService = Provide[Context.results_service]
    ) -> ResultsService:
        """Handles injection of the results service.

        Args:
            results_service (ResultsService): Injected database service for
                fetching/storing results.

        Returns:
            ResultsService

        """
        if not hasattr(self, "_results_service"):
            self.results_service = results_service

        return self._results_service

    @results_service.setter
    def results_service(self, val: Any) -> None:
        self._results_service = val

    def __getstate__(self) -> dict:
        """Utility function for removing results service from replications of result.

        Returns:
            dict: Representation of state

        """
        state = self.__dict__.copy()
        if "_results_service" in state:
            del state["_results_service"]
        return state

    def exists(self, location: str, **kwargs) -> bool:
        """Checks whether the target result exists using the db service.

        Args:
            location (str): Location of result by unique index field.
            **kwargs (Any): string format arguments for `location`

        Returns:
            bool: whether or not the target result exists
        """
        # check whether target result exists

        # get index fields
        result = self._results_service.find_by_unique_field(location)

        if len(result):
            return True

        else:
            return False

    def read(self, location: str) -> DBResult:
        """Reads result from file service and return the corresponding result.

        Args:
            location (str): the location to read from
        Returns:
            DBResult: New result instantiated from location

        """

        new = self.copy()
        new.location = location
        new.value = self._results_service.find_by_unique_field(location)

        return new

    def write(self, model_rep: dict, **kwargs) -> DBResult:
        """Write model result representation to database.

        Args:
            model_rep (dict): Dictionary representation of model

        Returns:
            DBResult

        """

        self.logger.debug("Writing result to results database...")

        insert_result = self._results_service.store(
            model_type=self._model_type, **model_rep
        )

        run_fingerprint = getattr(insert_result, self._target)
        new = self.copy()
        new.value = model_rep
        new.location = run_fingerprint

        return new
