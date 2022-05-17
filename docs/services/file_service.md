# File service

The file service is intented to provide an abstraction to filesystem read/writes allowing for the the implementation of interfaces to remote or mounted resources. The file service can be configured to interface with multiple `Filesystem` resources.

LUME-serices is packaged with `LocalFilesystem` and `MountedFilesystem` implementations, however, the `Filesystem` interface defined in `lume_services.data.file.systems.filesystem` can be used to implement any number of custom interfaces including remote cloud services.


![Screenshot](files/services/filesystem.drawio.png)