import h5py
from lume_base import Base


class LUMEObjectSerializer():

    @classmethod
    def serialize(cls, filename, object: Base):

        with h5py.File(filename, "w") as f:

            object.archive(f) 


    @classmethod
    def deserialize(cls, filename, object_type):

        with h5py.File(filename, "r") as f:

            object = object_type.from_archive(f) 

        return object
