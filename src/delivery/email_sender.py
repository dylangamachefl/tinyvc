"""Email delivery via SMTP."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import markdown
import structlog

logger = structlog.get_logger()


class EmailSender:
    """Send reports via SMTP email."""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str
    ):
        """Initialize email sender.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port (usually 587 for TLS)
            smtp_user: SMTP username (email address)
            smtp_password: SMTP password (app password for Gmail)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.logger = logger.bind(service="email_sender")
    
    def send_report(
        self,
        recipient: str,
        subject: str,
        markdown_body: str,
        attachments: list[str] = None
    ) -> bool:
        """Send email with markdown report.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            markdown_body: Report content in markdown
            attachments: List of file paths to attach
            
        Returns:
            True if sent successfully
        """
        self.logger.info("sending_email", recipient=recipient)
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Convert markdown to HTML
            html_body = markdown.markdown(
                markdown_body,
                extensions=['tables', 'fenced_code']
            )
            
            # Add CSS styling to HTML
            html_with_style = self._add_email_styles(html_body)
            
            # Attach both plain text and HTML versions
            text_part = MIMEText(markdown_body, 'plain')
            html_part = MIMEText(html_with_style, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Attach files
            if attachments:
                for filepath in attachments:
                    self._attach_file(msg, filepath)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info("email_sent_successfully")
            return True
            
        except Exception as e:
            self.logger.error("email_send_failed", error=str(e))
            return False
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str) -> None:
        """Attach a file to email message.
        
        Args:
            msg: Email message object
            filepath: Path to file to attach
        """
        path = Path(filepath)
        
        if not path.exists():
            self.logger.warning("attachment_not_found", file=filepath)
            return
        
        # Read file
        with open(path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        # Encode
        encoders.encode_base64(part)
        
        # Add header
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {path.name}'
        )
        
        msg.attach(part)
        self.logger.debug("file_attached", filename=path.name)
    
    def _add_email_styles(self, html_body: str) -> str:
        """Add CSS styles to HTML email.
        
        Args:
            html_body: Raw HTML content
            
        Returns:
            HTML with embedded styles
        """
        styles = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #2c3e50;
                margin-top: 30px;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 8px;
            }
            h3 {
                color: #34495e;
                margin-top: 20px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            strong {
                color: #2c3e50;
            }
            hr {
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }
            .disclaimer {
                font-size: 0.85em;
                color: #7f8c8d;
                font-style: italic;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ecf0f1;
            }
        </style>
        """
        
        return f"<html><head>{styles}</head><body>{html_body}</body></html>"
