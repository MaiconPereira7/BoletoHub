from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_email(to: str, subject: str, html_body: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        raise RuntimeError("SMTP não configurado (SMTP_USER/SMTP_PASSWORD ausentes)")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as client:
        if settings.smtp_use_tls:
            client.starttls()
        client.login(settings.smtp_user, settings.smtp_password)
        client.sendmail(settings.smtp_from or settings.smtp_user, [to], message.as_string())


def render_password_reset_email(reset_url: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #2563eb;">Redefinir senha — BoletoHub</h2>
      <p>Recebemos um pedido para redefinir a senha da sua conta.</p>
      <p>
        <a href="{reset_url}"
           style="display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff;
                  text-decoration: none; border-radius: 8px; font-weight: bold;">
          Criar nova senha
        </a>
      </p>
      <p>Esse link expira em {settings.password_reset_token_expire_minutes} minutos.</p>
      <p style="color: #64748b; font-size: 13px;">
        Se você não pediu essa redefinição, pode ignorar este e-mail — sua senha continua a mesma.
      </p>
    </div>
    """
