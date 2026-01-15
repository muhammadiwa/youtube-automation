"""Contact form API router."""

from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.modules.notification.channels import EmailChannel

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactFormRequest(BaseModel):
    """Contact form submission request."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactFormResponse(BaseModel):
    """Contact form submission response."""
    success: bool
    message: str


@router.post("/submit", response_model=ContactFormResponse)
async def submit_contact_form(
    data: ContactFormRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit contact form and send email notification."""
    try:
        email_channel = EmailChannel()
        
        # Format email content
        email_body = f"""
New Contact Form Submission

From: {data.first_name} {data.last_name}
Email: {data.email}
Subject: {data.subject}

Message:
{data.message}

---
This message was sent from the YT Automation contact form.
        """.strip()
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">New Contact Form Submission</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>From:</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{data.first_name} {data.last_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><a href="mailto:{data.email}">{data.email}</a></td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Subject:</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{data.subject}</td>
        </tr>
    </table>
    <h3 style="margin-top: 20px;">Message:</h3>
    <div style="background: #f9fafb; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{data.message}</div>
    <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
    <p style="color: #666; font-size: 12px;">This message was sent from the YT Automation contact form.</p>
</body>
</html>
        """.strip()
        
        # Send to support email
        support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@ytautomation.com')
        
        result = await email_channel.deliver(
            recipient=support_email,
            title=f"Contact Form: {data.subject}",
            message=email_body,
            payload={"html_body": html_body, "reply_to": data.email},
        )
        
        if result.success:
            return ContactFormResponse(
                success=True,
                message="Thank you for your message. We'll get back to you within 24 hours.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message. Please try again later.",
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
