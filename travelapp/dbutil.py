import pymysql
import uuid
import hashlib
import string
import random
from . import config as cfg

CHAR_SET = string.ascii_letters + string.digits

def connect():
    return pymysql.connect(host=cfg.DB_HOST, user=cfg.DB_USERNAME, 
                           passwd=cfg.DB_PASSWORD, db=cfg.DB_DATABASE)



def insert_location(cursor, userid, title, latitude, longitude, arrivalDate, departureDate, website):
    sql = """
        INSERT INTO locations (user_id, guid, title, latitude, longitude, arrivalDate, departureDate, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    guid = uuid.uuid1().hex

    cursor.execute(sql, (userid, guid, title, latitude, longitude, arrivalDate, departureDate, website))

    cursor.connection.commit()


def insert_user(cursor, username, firstname, lastname, email, password):
    sql = """
        INSERT INTO users (guid, username, firstname, lastname, email, hashed_password, salt)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    salt = ''.join(random.sample(CHAR_SET*64, 64))

    hashed_password = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    guid = uuid.uuid1().hex

    cursor.execute(sql, (guid, username, firstname, lastname, email, hashed_password, salt))

    cursor.connection.commit()

def get_user(cursor, username):
    sql = """
        SELECT user_id, guid, username, firstname, lastname, email, verified, registered, hashed_password, salt
        FROM users
        where username=%s
    """

    count = cursor.execute(sql, username)
    if (count != 1):
        return None

    user = cursor.fetchone()

    return {
        "user_id": user[0],
        "guid": user[1],
        "username": user[2],
        "firstname": user[3],
        "lastname": user[4],
        "email": user[5],
        "verified": user[6],
        "registered": user[7],
        "hashed_password": user[8],
        "salt": user[9]
    }


def get_locations(cursor, username):
    user_id = get_user(cursor, username)['user_id']

    sql = """
        SELECT location_id, user_id, guid, title, latitude, longitude, arrivalDate, departureDate, url
        FROM locations
        where user_id=%s
    """

    cursor.execute(sql, user_id)

    location_list = []
    location = cursor.fetchone()
    while (location != None):
        location_list.append({
            "location_id": location[0],
            "user_id": location[1],
            "guid": location[2],
            "title": location[3],
            "latitude": location[4],
            "longitude": location[5],
            "arrivalDate": location[6],
            "departureDate": location[7],
            "url": location[8]
        })
        location = cursor.fetchone()

    return location_list



