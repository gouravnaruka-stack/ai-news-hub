"""
send_email.py
Sends the daily AI news digest to your inbox using Gmail SMTP.

Requires two secrets:
  GMAIL_ADDRESS       - the Gmail account sending the digest (e.g. you@gmail.com)
  GMAIL_APP_PASSWORD  - a 16-character Gmail "app password" (NOT your normal password)

How to get an app password:
  1. Turn on 2-Step Verification on the Google account: https://myaccount.google.com/security
  2. Go to https://myaccount.google.com/apppasswords
  3. Create an app password for "Mail" and copy the 16-character code
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
# Who receives the digest - defaults to sending it to yourself
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def build_html_email(articles):
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    if not articles:
        rows = "<p style='color:#666;'>No AI news found today.</p>"
    else:
        rows = ""
        for a in articles:
            rows += f"""
            <div style="padding:14px 0; border-bottom:1px solid #e5e5e5;">
              <p style="font-size:15px; font-weight:600; margin:0 0 4px; color:#111;">
                <a href="{a['url']}" style="color:#111; text-decoration:none;">{a['title']}</a>
              </p>
              <p style="font-size:12px; color:#888; margin:0 0 6px;">{a['source']}</p>
              <p style="font-size:13px; color:#444; margin:0; line-height:1.5;">{a.get('summary', '')}</p>
            </div>
            """

    return f"""
    <html>
    <body style="font-family: -apple-system, Helvetica, Arial, sans-serif; background:#f5f5f5; padding:20px;">
      <div style="max-width:600px; margin:0 auto; background:#fff; border-radius:10px; overflow:hidden; border:1px solid #e5e5e5;">
        <div style="padding:18px 24px; border-bottom:1px solid #e5e5e5;">
          <h2 style="margin:0; font-size:18px;">🧠 Your AI News Digest — {date_str}</h2>
        </div>
        <div style="padding:0 24px;">
          {rows}
        </div>
        <div style="padding:14px 24px; text-align:center;">
          <p style="font-size:11px; color:#999; margin:0;">Sent automatically by AI News Hub · {len(articles)} stories today</p>
        </div>
      </div>
    </body>
    </html>
    """


def send_digest_email(articles):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set — skipping email send.")
        return False

    date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your AI News Digest — {date_str}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL

    html_content = build_html_email(articles)
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        print(f"Digest email sent to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    test_articles = [{
        "title": "Test story",
        "url": "https://example.com",
        "source": "Example",
        "summary": "This is a test summary to confirm email sending works.",
    }]
    send_digest_email(test_articles)
