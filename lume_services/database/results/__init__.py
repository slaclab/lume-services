

class ResultsDB(ABC):

    @abstractmethod
    def __init__(self):
        ...
    
    @abstractmethod
    def find(self):
        ...

    @abstractmethod
    def store(self):
        ...

