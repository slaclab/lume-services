from abc import ABC, ABCMeta, abstractmethod



class DocumentBase(ABC, metaclass=ABCMeta):
    """Fields should be stored as attributes and able to be initialized with passed kwargs
    
    """

    @staticmethod
    @abstractmethod
    def get_validation_error():
        """Return validation error
        """
        ...

    def get_pk_id(self):
        """Get pk id from initialized doc.

        """