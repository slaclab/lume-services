from abc import ABC, abstractmethod



class DocumentBase(ABC):
    """Fields should be stored as attributes and able to be initialized with passed kwargs
    
    """

    @abstractmethod
    @staticmethod
    def get_validation_error():
        """Return validation error
        """
        ...

    def get_pk_id(self):
        """Get pk id from initialized doc.

        """