"""Email OAuth routes for Gmail API authorization."""

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from src.services.email_service import get_gmail_auth_url, exchange_code_for_tokens

router = APIRouter(prefix="/email", tags=["email"])


@router.get("/oauth/authorize")
async def gmail_authorize():
    """
    Get Gmail OAuth authorization URL.
    
    Visit this URL to authorize the application to send emails.
    After authorization, you'll be redirected to the callback endpoint.
    """
    auth_url = get_gmail_auth_url()
    
    if not auth_url:
        return {
            "error": "Gmail API not configured",
            "message": "Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env"
        }
    
    return {
        "auth_url": auth_url,
        "instructions": "Visit this URL to authorize Gmail access. After authorization, copy the refresh_token from the callback and add it to your .env file as GMAIL_REFRESH_TOKEN"
    }


@router.get("/oauth/callback", response_class=HTMLResponse)
async def gmail_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None),
    error: str = Query(None),
):
    """
    OAuth callback endpoint for Gmail authorization.
    
    Google redirects here after user authorizes the app.
    Displays the refresh token to copy to .env file.
    """
    if error:
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #ef4444;">❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please try again.</p>
            </body>
        </html>
        """
    
    tokens = exchange_code_for_tokens(code)
    
    # If tokens is a string, it's an error message
    if isinstance(tokens, str):
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #ef4444;">❌ Token Exchange Failed</h1>
                <p>Could not exchange authorization code for tokens.</p>
                <div style="background: #fef2f2; border: 1px solid #ef4444; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <strong>Error:</strong> {tokens}
                </div>
                <p>Please check:</p>
                <ul>
                    <li>GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct</li>
                    <li>gmail.send scope is added in OAuth consent screen</li>
                    <li>Redirect URI matches exactly in GCP Console</li>
                </ul>
            </body>
        </html>
        """
    
    refresh_token = tokens.get("refresh_token", "")

    
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto;">
            <h1 style="color: #22c55e;">✅ Gmail Authorization Successful!</h1>
            
            <p>Add the following to your <code>.env</code> file:</p>
            
            <div style="background: #1f2937; color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; overflow-x: auto;">
                <code style="font-size: 14px;">
                    GMAIL_REFRESH_TOKEN={refresh_token}
                </code>
            </div>
            
            <p style="color: #6b7280;">
                <strong>Note:</strong> The refresh token allows the app to send emails on your behalf.
                Keep it secure and never share it publicly.
            </p>
            
            <p>After adding the token, restart the backend server.</p>
            
            <h2>Test Email</h2>
            <p>You can test by visiting: <a href="/api/email/test">/api/email/test</a></p>
        </body>
    </html>
    """


@router.get("/test")
async def test_email(to: str = Query(None, description="Recipient email address")):
    """
    Test endpoint to verify email configuration.
    
    Args:
        to: Optional recipient email. Defaults to configured GMAIL_USER_EMAIL.
    """
    from src.core.config import get_settings
    from src.services.email_service import send_price_alert_email
    
    settings = get_settings()
    
    target_email = to or settings.gmail_user_email
    
    if not target_email:
        return {
            "success": False,
            "error": "No recipient email specified and GMAIL_USER_EMAIL not configured"
        }
    
    result = await send_price_alert_email(
        to_email=target_email,
        symbol="TEST",
        target_price=100.00,
        current_price=105.00,
    )
    
    return {
        "success": result,
        "to_email": target_email,
        "message": f"Test email sent to {target_email}!" if result else "Failed to send email. Check configuration."
    }
