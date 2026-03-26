# utils/otp.py
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# store OTPs temporarily in memory
# {email: {"otp": "123456", "expires": timestamp}}
otp_store = {}

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(email: str) -> bool:
    """Sends OTP to email, returns True if successful"""
    try:
        otp = generate_otp()
        
        # store OTP with 10 minute expiry
        import time
        otp_store[email.lower()] = {
            "otp": otp,
            "expires": time.time() + 600  # 10 minutes
        }

        # compose email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp} is your ET ContentFlow login code"
        msg["From"] = os.getenv("GMAIL_EMAIL")
        msg["To"] = email

        html = f"""
        <html>
        <body style="background:#0a0a0a; padding:40px; font-family:'Georgia',serif;">
            <div style="max-width:480px; margin:0 auto;">
                <div style="font-size:20px; font-weight:700; color:#f0ece4; margin-bottom:8px;">
                    ET <span style="color:#d4a855;">ContentFlow</span>
                </div>
                <div style="height:1px; background:rgba(255,255,255,0.1); margin:24px 0;"></div>
                <div style="font-size:14px; color:rgba(240,236,228,0.6); margin-bottom:32px; line-height:1.6;">
                    Your one-time login code is:
                </div>
                <div style="font-size:48px; font-weight:700; color:#d4a855; letter-spacing:8px; margin-bottom:32px;">
                    {otp}
                </div>
                <div style="font-size:12px; color:rgba(240,236,228,0.3); line-height:1.6;">
                    This code expires in 10 minutes.<br>
                    If you did not request this, ignore this email.
                </div>
                <div style="height:1px; background:rgba(255,255,255,0.1); margin:24px 0;"></div>
                <div style="font-size:11px; color:rgba(240,236,228,0.2);">
                    Powered by Economic Times
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        # send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                os.getenv("GMAIL_EMAIL"),
                os.getenv("GMAIL_APP_PASSWORD")
            )
            server.sendmail(
                os.getenv("GMAIL_EMAIL"),
                email,
                msg.as_string()
            )

        print(f"OTP sent to {email}: {otp}")
        return True

    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False


def verify_otp(email: str, otp: str) -> bool:
    """Verifies OTP, returns True if valid"""
    import time
    email = email.lower()
    
    if email not in otp_store:
        return False
    
    stored = otp_store[email]
    
    # check expiry
    if time.time() > stored["expires"]:
        del otp_store[email]
        return False
    
    # check OTP
    if stored["otp"] == otp.strip():
        del otp_store[email]  # one time use
        return True
    
    return False