"""Email service for sending notifications via Gmail API OAuth 2.0."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.core.config import get_settings

# Gmail API scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_auth_url() -> str | None:
    """
    Get Gmail OAuth authorization URL for initial setup.
    
    Returns:
        Authorization URL or None if not configured
    """
    settings = get_settings()
    
    if not settings.google_client_id:
        return None
    
    from google_auth_oauthlib.flow import Flow
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_redirect_uri],
            }
        },
        scopes=GMAIL_SCOPES,
    )
    flow.redirect_uri = settings.gmail_redirect_uri
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    
    return auth_url


def exchange_code_for_tokens(code: str) -> dict | str:
    """
    Exchange authorization code for access/refresh tokens.
    
    Args:
        code: Authorization code from OAuth callback
        
    Returns:
        Token data dict or error string
    """
    settings = get_settings()
    
    if not settings.google_client_id:
        return "GOOGLE_CLIENT_ID not configured"
    
    from google_auth_oauthlib.flow import Flow
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_redirect_uri],
            }
        },
        scopes=GMAIL_SCOPES,
    )
    flow.redirect_uri = settings.gmail_redirect_uri
    
    # Allow scope to change (Google adds basic profile scopes automatically)
    import os
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        }
    except Exception as e:
        print(f"Token exchange error: {e}")
        return str(e)


async def send_via_gmail_api(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """
    Send email using Gmail API with OAuth 2.0 refresh token.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML body content
        
    Returns:
        True if sent, False otherwise
    """
    settings = get_settings()
    
    if not settings.gmail_refresh_token or not settings.google_client_id:
        return False
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Create credentials from refresh token
        credentials = Credentials(
            token=None,
            refresh_token=settings.gmail_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=GMAIL_SCOPES,
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials, cache_discovery=False)
        
        # Create message
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        
        from_name = settings.mail_from_name or "StockValuator"
        from_email = settings.gmail_user_email or to_email
        message['from'] = f"{from_name} <{from_email}>"
        
        # Adding Sender header can help delivery issues
        if settings.gmail_user_email:
             message['sender'] = settings.gmail_user_email
             
        message['subject'] = subject
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True
        
    except Exception as e:
        print(f"Gmail API error: {e}")
        return False


async def send_via_smtp(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """
    Send email using SMTP (fallback method).
    """
    from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
    
    settings = get_settings()
    
    if not settings.mail_server or not settings.mail_from:
        return False
    
    config = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=bool(settings.mail_username),
        VALIDATE_CERTS=True,
    )
    
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    try:
        fm = FastMail(config)
        await fm.send_message(message)
        return True
    except Exception:
        return False


async def send_price_alert_email(
    to_email: str,
    symbol: str,
    target_price: float,
    current_price: float,
) -> bool:
    """
    Send price alert notification email.
    
    Tries Gmail API first, falls back to SMTP if not configured.
    """
    direction = "reached" if current_price >= target_price else "dropped to"
    
    subject = f"🚨 Price Alert: {symbol} {direction} ${target_price:.2f}"
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">Price Alert Triggered</h2>
            <p style="font-size: 16px;">
                Your price alert for <strong>{symbol}</strong> has been triggered!
            </p>
            <div style="background: #f3f4f6; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <p><strong>Stock:</strong> {symbol}</p>
                <p><strong>Target Price:</strong> ${target_price:.2f}</p>
                <p><strong>Current Price:</strong> ${current_price:.2f}</p>
                <p><strong>Status:</strong> Price {direction} your target</p>
            </div>
            <p style="color: #6b7280; font-size: 14px;">
                This is an automated notification from StockValuator.
            </p>
        </body>
    </html>
    """
    
    # Try Gmail API first
    if await send_via_gmail_api(to_email, subject, html):
        return True
    
    # Fall back to SMTP
    return await send_via_smtp(to_email, subject, html)
