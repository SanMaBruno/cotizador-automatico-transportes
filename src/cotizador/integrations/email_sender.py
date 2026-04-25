from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from cotizador.application.ports import EmailSender


class NoOpEmailSender(EmailSender):
    def send(self, to: str, subject: str, body: str) -> None:
        return


class FileEmailSender(EmailSender):
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, to: str, subject: str, body: str) -> None:
        payload = {"to": to, "subject": subject, "body": body}
        with self._output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")


class SmtpEmailSender(EmailSender):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_starttls: bool = True,
        timeout_seconds: int = 20,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_starttls = use_starttls
        self._timeout_seconds = timeout_seconds

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP(self._host, self._port, timeout=self._timeout_seconds) as server:
            if self._use_starttls:
                server.starttls(context=context)
            server.login(self._username, self._password)
            server.send_message(message)


class SafeEmailSender(EmailSender):
    def __init__(self, sender: EmailSender, fallback: Optional[EmailSender] = None) -> None:
        self._sender = sender
        self._fallback = fallback

    def send(self, to: str, subject: str, body: str) -> None:
        try:
            self._sender.send(to=to, subject=subject, body=body)
        except Exception as exc:  # pragma: no cover - depends on external SMTP failures.
            if self._fallback is not None:
                self._fallback.send(to=to, subject=subject, body=body)
            print(f"WARNING: email delivery failed for {to}: {exc}")


class RecipientOverrideEmailSender(EmailSender):
    def __init__(self, sender: EmailSender, override_to: str) -> None:
        self._sender = sender
        self._override_to = override_to

    def send(self, to: str, subject: str, body: str) -> None:
        self._sender.send(to=self._override_to, subject=f"[DEMO para {to}] {subject}", body=body)


def build_email_sender_from_env() -> EmailSender:
    override_to = os.getenv("COTIZADOR_EMAIL_OVERRIDE_TO")
    if os.getenv("COTIZADOR_EMAIL_DRY_RUN", "").lower() == "true":
        output = Path(os.getenv("COTIZADOR_EMAIL_DRY_RUN_PATH", "out/dry_run_emails.jsonl"))
        sender: EmailSender = FileEmailSender(output)
        if override_to:
            return RecipientOverrideEmailSender(sender, override_to)
        return sender

    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = _normalize_smtp_password(os.getenv("SMTP_PASSWORD"))
    from_email = os.getenv("SMTP_FROM")
    if not all([host, username, password, from_email]):
        return NoOpEmailSender()

    port = int(os.getenv("SMTP_PORT", "587"))
    use_starttls = os.getenv("SMTP_USE_STARTTLS", "true").lower() == "true"
    smtp_sender = SmtpEmailSender(
        host=host or "",
        port=port,
        username=username or "",
        password=password or "",
        from_email=from_email or "",
        use_starttls=use_starttls,
    )
    fallback = FileEmailSender(Path("out/failed_smtp_emails.jsonl"))
    sender = SafeEmailSender(smtp_sender, fallback=fallback)
    if override_to:
        return RecipientOverrideEmailSender(sender, override_to)
    return sender


def _normalize_smtp_password(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return "".join(value.split())
