from abc import ABC,abstractmethod

class QInterface(ABC):
    

    @abstractmethod
    def Quiz_start(self):
        pass

    @abstractmethod
    def Quiz_submit(self):
        pass

class LoginInterface(ABC):
    @abstractmethod
    def Login(self):
        pass