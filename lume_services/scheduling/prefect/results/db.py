from prefect.engine.result.base import Result
from typing import Callable, Type, Any
from dependency_injector.wiring import Provide

from lume_services.data.results import ResultsService


class DBResult(Result):

    def __init__(self, *, model_type: str, results_service: ResultsService, **kwargs):
        """
        
        Note: model_type string must be a key member of the model_docs Enum passed to the ResultsService.

        Location is the unique result hash
        """
        self._results_service = results_service
        self._model_type = model_type

        super().__init__(**kwargs)

        # validate that model type is a member of model_docs enum
        self._results_service.validate_model_type(model_type)
        self._target = self._results_service.get_unique_field(model_type)

        if not self._model_type:
            raise ValueError("model type not provided")


    @property
    def results_service(self, results_service: Provide[ResultsService]) -> ResultsService:
        if not hasattr(self, "_results_service"):
            self.results_service = results_service

        return self._results_service

    @results_service.setter
    def results_service(self, val: Any) -> None:
        self._results_service = val

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        if "_results_service" in state:
            del state["_results_service"]
        return state


    def exists(self, location: str, **kwargs) -> bool:
        # check whether target result exists

        # get index fields
        result = self._results_service.find_by_unique_field(location)

        if len(result):
            return True

        else:
            return False


    def read(self, location: str):
        new = self.copy()
        new.location = location
        new.value = self._results_service.find_by_unique_field(location)

        return new
            

    def write(self, model_rep: dict, **kwargs):

        self.logger.debug("Writing result to results database...")

        insert_result = self._results_service.store(model_type=self._model_type, model_rep=model_rep)

        run_fingerprint = getattr(insert_result, self._target)
        new = self.copy()
        new.value = model_rep
        new.location = run_fingerprint

        return new

