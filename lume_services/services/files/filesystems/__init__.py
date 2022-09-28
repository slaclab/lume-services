from .filesystem import Filesystem
from .local import LocalFilesystem
from .mounted import MountedFilesystem


# create map of type import path to type
_FilestemTypeStringMap = {
    f"{LocalFilesystem.__module__}:{LocalFilesystem.__name__}": LocalFilesystem,
    f"{MountedFilesystem.__module__}:{MountedFilesystem.__name__}": MountedFilesystem,
}


def get_filesystem_from_serializer_string(filesystem_type_string: str):

    if not _FilestemTypeStringMap.get(filesystem_type_string):
        raise ValueError(
            "Filesystem string not in filesystem types. %s, %s",
            filesystem_type_string,
            list(_FilestemTypeStringMap.keys()),
        )

    else:
        return _FilestemTypeStringMap.get(filesystem_type_string)
