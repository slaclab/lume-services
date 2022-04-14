from abc import ABC, ABCMeta, abstractmethod



class DocumentBase(ABC):
    """Fields should be stored as attributes and able to be initialized with passed kwargs.

    At present, this isn't subclassed for implementing docs because of metaclass conflicts
    TODO: Fix metaclass conflict
    
    """

    @staticmethod
    @abstractmethod
    def get_validation_error():
        """Return validation error
        """
        ...

    @abstractmethod
    def get_pk_id(self):
        """Get pk id from initialized doc.

        """

    @abstractmethod
    def get_unique_result_index(self):
        ...

    @abstractmethod
    def get_unique_result_index_fields(self):
        ...