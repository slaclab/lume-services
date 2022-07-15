import logging
from dependency_injector.wiring import Provide, inject
from prefect import Task
from typing import Any

from lume_services.config import Context
from lume_services.services.files import FileService
from prefect.engine.results import PrefectResult

from lume_services.files import get_file_from_serializer_string
from lume_services.utils import fingerprint_dict


logger = logging.getLogger(__name__)


def _unique_file_location(file_rep):
    hash = fingerprint_dict(file_rep)
    return f"{hash}.prefect"


class SaveFile(Task):
    def __init__(self, **kwargs):

        # apply some defaults but allow overrides
        log_stdout = kwargs.get("log_stdout")
        if not kwargs.get("log_stdout"):
            log_stdout = True
        else:
            log_stdout = kwargs.pop("log_stdout")

        if not kwargs.get("name"):
            name = "save_file"
        else:
            name = kwargs.pop("name")

        if not kwargs.get("result"):
            result = PrefectResult(location=_unique_file_location)
        else:
            result = kwargs.pop("result")

        super().__init__(log_stdout=log_stdout, name=name, result=result, **kwargs)

    @inject
    def run(
        self,
        obj: Any,
        filename: str,
        filesystem_identifier: str,
        file_type: type,
        file_service: FileService = Provide[Context.file_service],
    ):
        """Save a file

        Args:
            obj (Any): Object to be saved
            filename (str): File path to save
            filesystem_identifier (str): String identifier for filesystem configured
                with File Service
            file_type (type): Type of file to save as
            file_service (FileService): File service for interacting w/ filesystems

        Returns:
            dict: Loaded file type

        """
        file = file_type(
            obj=obj, filesystem_identifier=filesystem_identifier, filename=filename
        )
        file.write(file_service=file_service)
        return file.jsonable_dict()


class LoadFile(Task):
    def __init__(self, **kwargs):

        # apply some defaults but allow overrides
        log_stdout = kwargs.get("log_stdout")
        if not kwargs.get("log_stdout"):
            log_stdout = True
        else:
            log_stdout = kwargs.pop("log_stdout")

        if not kwargs.get("name"):
            name = "load_file"
        else:
            name = kwargs.pop("name")

        super().__init__(log_stdout=log_stdout, name=name, **kwargs)

    @inject
    def run(
        self, file_rep: dict, file_service: FileService = Provide[Context.file_service]
    ) -> Any:
        """Load a file

        Args:
            file_rep (dict): File data representation
            file_service (FileService): File service for interacting w/ filesystems

        Returns:
            Any: Unserialize file object

        """

        file_type = get_file_from_serializer_string(file_rep["file_type_string"])
        file_result = file_type(**file_rep)

        return file_result.read(file_service=file_service)
