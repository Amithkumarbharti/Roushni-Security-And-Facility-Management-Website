"""
Configuration for the RSFM (Roushni Security & Facility Management) website.
Keeps environment-specific settings out of application logic, per the
project's documented security standards. Values are loaded from a `.env`
file (if present) so secrets and contact details never need to be
hardcoded or committed to source control.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional at runtime if real environment variables
    # are already set (e.g. by the hosting platform).
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    COMPANY_NAME = "Roushni Security & Facility Management"
    COMPANY_SHORT = "RSFM"
    COMPANY_TAGLINE = "Securing Your Business"
    COMPANY_ADDRESS_LINE1 = "653/2, 1st Floor, Anugraha Nilaya"
    COMPANY_ADDRESS_LINE2 = "Annasandrapalya Main Road, Bengaluru 560037"

    # Contact details — override via environment variables in production.
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "+91 84535 65425")
    COMPANY_PHONE_2 = os.environ.get("COMPANY_PHONE_2", "+91 90197 04534")
    COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "roushnifacility@gmail.com")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "rsfm.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Outgoing email (enquiry notifications) — configure via .env
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    ENQUIRY_NOTIFY_EMAIL = os.environ.get("ENQUIRY_NOTIFY_EMAIL", COMPANY_EMAIL)
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "False") == "True"

    # Admin panel credentials — change these in your .env before deployment
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "rsfm@admin123")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
