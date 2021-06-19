import os

VERSION = "0.0.0"

class Config():
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = 'redis://localhost'
    LOGLEVEL = 'debug'


