import sys
import os

CONFIG_DIR = ".codelearn"
home = os.getenv("HOME")

sys.path.append(os.path.join(home, CONFIG_DIR))
import _config as cfg

GOOGLE_MAPS_API = cfg.GOOGLE_MAPS_API
GOOGLE_PLACE_API = cfg.GOOGLE_PLACE_API
DB_HOST = cfg.db_host
DB_USERNAME = cfg.db_username
DB_PASSWORD = cfg.db_password
DB_DATABASE = cfg.db_database

GMAIL_USER = cfg.gmail_user
GMAIL_PW = cfg.gmail_pwd

DREAMHOST_HOST = cfg.dreamhost_host

APPLICATION_EMAIL = cfg.application_email

del home 
del CONFIG_DIR
del os 
del sys
del cfg
    

def printconfig():
    print(DB_HOST)
    print(DB_USERNAME)
    print(DB_PASSWORD)
    print(DB_DATABASE)
    