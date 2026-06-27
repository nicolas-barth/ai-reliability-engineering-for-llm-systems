from abc import ABC, abstractmethod


class LLMServiceInterface(ABC):

    @abstractmethod
    async def classify(self, message: str, run_profile: int = 0) -> dict:
        ...
