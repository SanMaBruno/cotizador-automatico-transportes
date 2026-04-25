from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cotizador.application.ports import EmailRepository
from cotizador.domain.entities import Email


class JsonEmailRepository(EmailRepository):
    def __init__(self, path: Path) -> None:
        self._path = path

    def list_inbox(self) -> Iterable[Email]:
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        for item in payload:
            yield Email(id=item["id"], sender=item["sender"], body=item["body"])
