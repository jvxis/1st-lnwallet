#
# Fill out the configuration variables below with your own values and save as config.py
#
import os

class Config:
    # Choose a secret key for the app. Keep it secret!
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_super_secret_key')
    # Set to True for development, False for production
    DEBUG = True
    # Set the port for the Flask app
    PORT = 37421
    # Database name
    DB_NAME = 'database.db'
    # LN Bits API configuration
    LN_BITS_API_URL = "https://your_domain/api/v1"
    LN_BITS_BASE_URL = "https://your_domain"
    # Same as LN BITS DOMAIN
    LN_ADDRESS_DOMAIN = "your_domain"
    # LNBITS WALLET ADMIN KEY
    LN_BITS_API_KEY = "LNBITS_ADMIN_KEY"
    # Google Recaptcha configuration
    # https://www.google.com/recaptcha/admin/create
    RECAPTCHA_SITE_KEY = "RECAPTCHA_SITE_KEY"
    RECAPTCHA_SECRET_KEY = "RECAPTCHA_SECRET_KEY"
    # LNBITS FEEs WALLET ADMIN KEY
    SATSBACK_WALLET_ADMIN_KEY = "LNBITS_FEE_WALLET_ADMIN_KEY"
    # Setup ENV variable to 'production' in your server environment
    # Example: export FLASK_ENV=production
    ENV = os.getenv('FLASK_ENV', 'development')  # 'production' para produção

    # Setup cookies
    SESSION_COOKIE_SECURE = ENV == 'production'  # True em produção, False no dev
    SESSION_COOKIE_HTTPONLY = True  # Protege contra ataques XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protege contra CSRF sem quebrar funcionalidade
    SESSION_PERMANENT = False

    # General settings
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'