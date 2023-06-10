"""Flask Environment configuration"""
import os
import logging
from urllib.parse import quote  # for quoting MySQL password

# -----------------------------------------------------
# Configuration Variables
# ------------------------------------------------------
#
# DEBUG: Extremely useful when developing! DEBUG mode triggers several things.
# Exceptions thrown by the app will print to console automatically, app crashes will result in a helpful error screen,
# and your app will auto-reload when changes are detected.
#
# TESTING: This mode ensures exceptions are propagated rather than handled by the app's error handlers,
# which is useful when running automated tests.
#
# SECRET_KEY: Flask "secret keys" are random strings used to encrypt sensitive user data, such as passwords.
# Encrypting data in Flask depends on the randomness of this string,
# which means decrypting the same data is as simple as getting a hold of this string's value.
# Guard your secret key with your life; ideally, even you shouldn't know the value of this variable.
#
# NOTE:
# If using an HTTPS endpoint, you should use:
# SESSION_COOKIE_SAMESITE = None
# SESSION_COOKIE_SECURE = True
# But when using HTTP, use:
# SESSION_COOKIE_SAMESITE = "lax"
# SESSION_COOKIE_SECURE = False

class Config:
    """Base config."""

    # You run the following to generate a secret key
    # import secrets
    # secrets.token_urlsafe(24)
    SECRET_KEY = "otN5RnxkiBpQ_4bHaJKZCrpgZeIMJ_vI"
    TEMPLATES_FOLDER = "templates"

    # SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_TYPE = "filesystem"
    USE_SESSION_FOR_NEXT = True  # Flask-Login redirect after successful login will be stored in the session
    WTF_CSRF_TIME_LIMIT = None  # Unlimited timeout for CSRF Token in forms
    WTF_CSRF_ENABLED = False  # disable CSRF tokens

    # user database config
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # URL for the graph API backend
    GRAPH_API_URL = "https://graph.scigami.org/build/0.0.2/js/graph.min.js"

    # Email configuration
    EMAIL = False  # enables email sending
    NEVERBOUNCE_KEY = ""  # neverbounce API key
    AWS_REGION = ""  # e.g. "us-east-1"
    EMAIL_ACCESS_KEY = ""  # AWS account access key ID
    EMAIL_SECRET_KEY = ""  # AWS account access key
    EMAIL_ADDRESS = ""  # email to send from

    # Brainworks Database Credentials
    BRAINWORKS_DB_DATABASE = ""
    BRAINWORKS_DB_HOST = ""
    BRAINWORKS_DB_USER = ""
    BRAINWORKS_DB_PORT = 3306
    BRAINWORKS_DB_PASSWORD = ""


# ProdConfig and DevConfig contain values specific to production and development respectively.
# Both of these classes extend a base class Config which contains values intended to be shared by both.


class ProdConfig(Config):
    """Production config"""

    ENV = "production"
    DEBUG = False
    TESTING = False

    LOG_LEVEL = logging.INFO

    # Site domain name
    DOMAIN_NAME = ""
    STATIC_FOLDER = "../react-app/build_production"

    # ENVIRONMENTAL VARIABLES SPECIFIED IN /.ebextensions/python.config
    # Why do we need these ... ?
    APP_VERSION = os.environ.get("APP_VERSION")

    # LIVE RDS database for login info
    user = os.environ.get("RDS_USERNAME")
    password = os.environ.get("RDS_PASSWORD")
    host = os.environ.get("RDS_HOSTNAME")
    port = os.environ.get("RDS_PORT")
    database = os.environ.get("RDS_DB_NAME")

    # escape special characters in password
    if password is not None:
        password = quote(password)

    SQLALCHEMY_DATABASE_URI = (f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}")

    DATABASE_UNAVAILABLE = False
    # Brainworks Database Credentials
    BRAINWORKS_DB_DATABASE = ""
    BRAINWORKS_DB_HOST = ""
    BRAINWORKS_DB_USER = ""
    BRAINWORKS_DB_PORT = 3306
    BRAINWORKS_DB_PASSWORD = ""

class DevConfig(Config):
    """For quick local testing."""

    ENV = "development"
    DEBUG = True

    LOG_LEVEL = logging.DEBUG

    # These settings enable cookies
    SESSION_COOKIE_SECURE = True

    # Allows CORS to use cookies
    SESSION_COOKIE_SAME_SITE = "None"

    # Manually call CSRF protection
    WTF_CSRF_CHECK_DEFAULT = False

    # log alembic to console
    logging.getLogger("alembic").addHandler(logging.StreamHandler())

    # Will send development email verification linking this domain
    DOMAIN_NAME = "https://localhost:3000"
    STATIC_FOLDER = "../react-app/build_development"

    # Bare-bones Sqlite file database
    SQLALCHEMY_DATABASE_URI = "sqlite:///../local/database.db"

    DATABASE_UNAVAILABLE = False

    # APScheduler
    SCHEDULER_API_ENABLED = True  # allow access to /scheduler/jobs

class RedShiftConfig(ProdConfig):
    """ Configuration for using the RedShift Warehouse as the transactional database """
    DOMAIN_NAME = ""
    SESSION_COOKIE_SECURE = "https://" in DOMAIN_NAME  # Use False when using HTTP, and True when using HTTPS
    SESSION_COOKIE_SAMESITE = None if SESSION_COOKIE_SECURE else "lax"  # if using HTTP, samesite should be "lax"

    user = os.environ.get("RDS_USERNAME")
    password = os.environ.get("RDS_PASSWORD")
    host = os.environ.get("RDS_HOSTNAME")
    port = os.environ.get("RDS_PORT")
    database = os.environ.get("RDS_DB_NAME")
    if password is not None: password = quote(password)  # escape special characters in the password
    #SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    SQLALCHEMY_DATABASE_URI = "sqlite:///../local/database.db"

    # Brainworks Database Credentials
    DATA_DATABASE = "REDSHIFT"
    BRAINWORKS_DB_DATABASE = "dev"
    BRAINWORKS_DB_HOST = ""
    BRAINWORKS_DB_USER = ""
    BRAINWORKS_DB_PORT = 5439
    BRAINWORKS_DB_PASSWORD = ''

    # Email configuration
    EMAIL = False  # True: enables email sending
    NEVERBOUNCE_KEY = ""  # neverbounce API key
    AWS_REGION = ""  # e.g. "us-east-1"
    EMAIL_ACCESS_KEY = ""  # AWS account access key ID
    EMAIL_SECRET_KEY = ""  # AWS account access key
    EMAIL_ADDRESS = ""  # email to send from

class TestConfig(DevConfig):
    """Used during Unit Test"""

    TESTING = True  # mail is not sent, NeverBounce is not used.
    WTF_CSRF_ENABLED = False  # disable CSRF checking in WTForms
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory sqlite database
    SCHEDULER_API_ENABLED = (
        False  # don't allow access to /scheduler/jobs like in production
    )
