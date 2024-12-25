import json
import smtplib
from loghive.main.settings import internal_logger, settings
from email.message import EmailMessage


def create_email_body(subject, message, information):
    """
    Generate an HTML body for the email based on the type of message and information.
    """
    # Your existing create_email_body function remains the same
    if isinstance(message, dict) and isinstance(information, dict):
        message_content = json.dumps(message, indent=4)
        information_content = json.dumps(information, indent=4)
    elif isinstance(message, dict) and isinstance(information, str):
        message_content = json.dumps(message, indent=4)
        information_content = information
    elif isinstance(message, str) and isinstance(information, dict):
        message_content = message
        information_content = json.dumps(information, indent=4)
    else:
        message_content = message
        information_content = information

    # Your existing HTML template remains the same
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                border: 1px solid #e0e0e0;
            }}
            .header {{
                background-color: #FF0000;
                color: white;
                text-align: center;
                padding: 10px 20px;
                font-size: 18px;
                font-weight: bold;
            }}
            .content {{
                padding: 20px;
            }}
            .section {{
                margin-bottom: 20px;
            }}
            .section h2 {{
                color: #FF0000;
                font-size: 16px;
                margin-bottom: 10px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .footer {{
                text-align: center;
                padding: 10px;
                font-size: 12px;
                color: #777;
                border-top: 1px solid #ddd;
                background: #f5f5f5;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                {subject}
            </div>
            <div class="content">
                <div class="section">
                    <h2>Message</h2>
                    <pre>{message_content}</pre>
                </div>
                <div class="section">
                    <h2>Additional Information</h2>
                    <pre>{information_content}</pre>
                </div>
            </div>
            <div class="footer">
                This is an automated email. Please do not reply.
            </div>
        </div>
    </body>
    </html>
    """
    return html_body


def send_email(recipient_emails, subject, message, information):
    """
    Send an HTML email using Gmail's SMTP server
    """
    body = create_email_body(subject, message, information)

    server = None
    try:
        server = smtplib.SMTP(settings.email_host, settings.email_port)
        server.starttls()
        server.login(settings.email_sender_email, settings.email_sender_password)

        for recipient in recipient_emails:
            msg = EmailMessage()
            # Set HTML content with the proper subtype
            msg.add_alternative(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = settings.email_sender_email
            msg["To"] = recipient
            server.send_message(msg)
        internal_logger.info("Emails sent successfully!")

    except Exception as e:
        internal_logger.error(f"Error sending email: {e}")
    finally:
        if server:
            server.quit()
