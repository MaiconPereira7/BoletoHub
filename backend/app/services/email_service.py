from __future__ import annotations

import email
import imaplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message

from app.config import settings

SCAN_LOOKBACK_DAYS = 30


@dataclass
class MailboxConfig:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True


@dataclass
class EmailAttachment:
    message_id: str
    subject: str
    from_: str
    filename: str
    content: bytes


def _decode_header_value(raw: str | None) -> str:
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = ""
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def _subject_matches_keywords(subject: str) -> bool:
    subject_lower = subject.lower()
    return any(keyword.lower() in subject_lower for keyword in settings.imap_search_keywords)


def _extract_pdf_attachments(msg: Message) -> list[tuple[str, bytes]]:
    attachments: list[tuple[str, bytes]] = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        if not filename:
            continue
        filename = _decode_header_value(filename)
        if not filename.lower().endswith(".pdf"):
            continue
        payload = part.get_payload(decode=True)
        if payload:
            attachments.append((filename, payload))
    return attachments


def _connect(mailbox: MailboxConfig) -> imaplib.IMAP4:
    if mailbox.use_ssl:
        client = imaplib.IMAP4_SSL(mailbox.host, mailbox.port)
    else:
        client = imaplib.IMAP4(mailbox.host, mailbox.port)

    client.login(mailbox.username, mailbox.password)
    return client


def legacy_mailbox() -> MailboxConfig | None:
    """Caixa configurada via variáveis de ambiente IMAP_* (uso legado, opcional)."""
    if not settings.imap_user or not settings.imap_password:
        return None
    return MailboxConfig(
        host=settings.imap_host,
        port=settings.imap_port,
        username=settings.imap_user,
        password=settings.imap_password,
        use_ssl=settings.imap_use_ssl,
    )


def fetch_boleto_candidates(mailbox: MailboxConfig, since_days: int = SCAN_LOOKBACK_DAYS) -> list[EmailAttachment]:
    client = _connect(mailbox)
    candidates: list[EmailAttachment] = []

    try:
        client.select("INBOX")

        since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        status, data = client.search(None, "SINCE", since_date)
        if status != "OK":
            return []

        message_numbers = data[0].split()
        for num in message_numbers:
            status, msg_data = client.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_header_value(msg.get("Subject"))
            if not _subject_matches_keywords(subject):
                continue

            attachments = _extract_pdf_attachments(msg)
            if not attachments:
                continue

            message_id = msg.get("Message-ID", "") or f"<no-id-{num.decode()}>"
            from_ = _decode_header_value(msg.get("From"))

            for filename, content in attachments:
                candidates.append(
                    EmailAttachment(
                        message_id=message_id,
                        subject=subject,
                        from_=from_,
                        filename=filename,
                        content=content,
                    )
                )
    finally:
        try:
            client.close()
        except imaplib.IMAP4.error:
            pass
        client.logout()

    return candidates
