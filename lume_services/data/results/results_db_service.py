



# assume nosql

class ResultsDBConfig:
    model_types = [
        "distgen",
        "impact",
        "surrogate",
        "bmad",
        "misc"
    ]



class ResultsDB(ABC):

    target_field = "fingerprint"

    @abstractmethod
    def __init__(self):
        ...
    
    @abstractmethod
    def find(self):
        ...

    @abstractmethod
    def store(self):
        ...