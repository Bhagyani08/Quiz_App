# config.py
import os

# Always use writable directory on Render
if os.environ.get("RENDER"):
    # Render environment → use /tmp directory
    DB_PATH = "/tmp/quiz.db"
else:
    # Local development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "quiz.db")

# Admin email where reports will be sent
ADMIN_EMAIL = "bhagyani2941@gmail.com"

# SMTP settings for sending report emails (use your SMTP server)
SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "bhagyani2941@gmail.com"
SMTP_PASS = "abcd efgh ijkl mnop"  # your Gmail app password
EMAIL_FROM = "bhagyani2941@gmail.com"

# If you prefer webhook reports instead of email, set WEBHOOK_URL to a POST endpoint (optional)
WEBHOOK_URL = None  # e.g. "https://hooks.example.com/report"
