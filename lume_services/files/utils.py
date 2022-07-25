from .file import TextFile, HDF5File, ImageFile, YAMLFile


# create map of type import path to type
_FileSerializerTypeStringMap = {
    f"{TextFile.__module__}:{TextFile.__name__}": TextFile,
    f"{HDF5File.__module__}:{HDF5File.__name__}": HDF5File,
    f"{ImageFile.__module__}:{ImageFile.__name__}": ImageFile,
    f"{YAMLFile.__module__}:{YAMLFile.__name__}": YAMLFile,
}


def get_file_from_serializer_string(file_type_string: str):

    if not _FileSerializerTypeStringMap.get(file_type_string):
        raise ValueError(
            "File string not in file types. %s, %s",
            file_type_string,
            list(_FileSerializerTypeStringMap.keys()),
        )

    else:
        return _FileSerializerTypeStringMap.get(file_type_string)
