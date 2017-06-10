import sys
import os

CONFIG_DIR = ".codelearn"
home = os.getenv("HOME")

sys.path.append(os.path.join(home, CONFIG_DIR))
import _config as cfg

GOOGLE_MAPS_API = cfg.GOOGLE_MAPS_API
DB_HOST = cfg.db_host
DB_USERNAME = cfg.db_username
DB_PASSWORD = cfg.db_password
DB_DATABASE = cfg.db_database

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
    