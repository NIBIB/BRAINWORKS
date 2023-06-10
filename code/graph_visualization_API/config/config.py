"""Flask Environment configuration"""
import os
from json import load


class Config:
    """ Base config """
    # You can run the following to generate a new secret key
    # import secrets
    # secrets.token_urlsafe(24)
    SECRET_KEY = 'otN5RnxkiBpQ_4bHaJKZCrpgZeIMJ_vI'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    # SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')
    #SESSION_COOKIE_SAMESITE = "None"
    #SESSION_COOKIE_SECURE = True

    # Current latest version string
    with open("package.json") as file:
        VERSION = load(file)['version']


# ProdConfig and DevConfig contain values specific to production and development respectively.
# Both of these classes extend a base class Config which contains values intended to be shared by both.
class ProdConfig(Config):
    """ Production config """
    ENV = 'production'
    DEBUG = False
    TESTING = False

    # site domain name
    with open("config/domain_name.json") as file:
        DOMAIN = load(file)


class DevConfig(Config):
    """ For quick local testing. """
    ENV     = 'development'
    DEBUG   = True

    DOMAIN = "http://localhost:5000"



