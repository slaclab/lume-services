# File service

The file service is intented to provide an abstraction to filesystem read/writes allowing for the the implementation of interfaces to remote or mounted resources. The file service can be configured to interface with multiple `Filesystem` resources.

LUME-serices is packaged with `LocalFilesystem` and `MountedFilesystem` implementations, however, the `Filesystem` interface defined in `lume_services.services.files.filesystems.filesystem` can be used to implement any number of custom interfaces including remote cloud services.

![Screenshot](files/services/filesystem.drawio.png)


## Filesystems

Filesystems may be defined in a `.ini` file and provided at runtime

```ini
[local]
identifier=local

[mounted]
identifier=workdir
mount_alias="/workdir"
mount_path="%(workdir)s"
```


Mount types:

    # types associated with mounting host filesystem to kubernetes
    # https://kubernetes.io/docs/concepts/storage/volumes/#hostpath
    directory = "Directory"  # directory must exist at given path
    directory_or_create = (
        "DirectoryOrCreate"  # if directory does not exist, directory created
    )
    file = "File"  # file must exist at path
    file_or_create = "FileOrCreate"  # will create file if does not exist
    # socket = "Socket" # Unix socket must exist at given path
    # char_device = "CharDevice" # Character device must exist at given path
    # block_device = "BlockDevice" # block device must exist at given path
