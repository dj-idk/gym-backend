import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from src.config import settings
from .logging import logger


def send_email(
    to_email: str | List[str],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    reply_to: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Send an email using the configured SMTP server.

    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content (fallback for email clients that don't support HTML)
        cc: List of CC recipients
        bcc: List of BCC recipients
        reply_to: Reply-to email address
        attachments: List of attachment dictionaries with 'filename' and 'content' keys

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Convert single email to list
        if isinstance(to_email, str):
            to_email = [to_email]

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM_ADDRESS
        message["To"] = ", ".join(to_email)

        # Add CC if provided
        if cc:
            message["Cc"] = ", ".join(cc)

        # Add Reply-To if provided
        if reply_to:
            message["Reply-To"] = reply_to

        # Add plain text and HTML parts
        if text_content:
            message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEText(attachment["content"])
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment['filename']}",
                )
                message.attach(part)

        # Determine all recipients for sending
        all_recipients = to_email.copy()
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Create secure connection with server and send email
        context = ssl.create_default_context()

        # Use SMTP_SSL for port 465, regular SMTP with STARTTLS for port 587
        if settings.MAIL_PORT == 465:
            with smtplib.SMTP_SSL(
                settings.MAIL_HOST, settings.MAIL_PORT, context=context
            ) as server:
                server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
                server.sendmail(
                    settings.MAIL_FROM_ADDRESS, all_recipients, message.as_string()
                )
        else:
            with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
                server.sendmail(
                    settings.MAIL_FROM_ADDRESS, all_recipients, message.as_string()
                )

        logger.info(f"Email sent successfully to {', '.join(to_email)}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
