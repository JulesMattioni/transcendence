import logging
from abc import ABC


class BaseService(ABC):
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
