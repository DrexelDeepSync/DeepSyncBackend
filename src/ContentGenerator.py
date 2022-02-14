from abc import ABC, abstractmethod
import string

class ContentGenerator(ABC):
    _outputPath: string

    @abstractmethod
    def generateContent(self) -> None:
        pass