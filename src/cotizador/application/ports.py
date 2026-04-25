from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from cotizador.domain.entities import Email, ProcessedEmail


class EmailRepository(ABC):
    @abstractmethod
    def list_inbox(self) -> Iterable[Email]:
        raise NotImplementedError


class IntegrationPublisher(ABC):
    @abstractmethod
    def publish(self, processed_email: ProcessedEmail) -> None:
        raise NotImplementedError


class EmailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError
