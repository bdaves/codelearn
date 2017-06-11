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

def get_guid():
    return uuid.uuid1().hex


def generate_salt():
    return ''.join(random.sample(CHAR_SET * 64, 64))


def hash_password(salt, password):
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


def utf_encode(value):
    if (isinstance(value, str)):
        return value.encode('utf-8')

    return value


def insert_location(cursor, tripid, title, latitude, longitude, arrivalDate, departureDate, website):
    sql = """
        INSERT INTO locations (trip_id, guid, title, latitude, longitude, arrivalDate, departureDate, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    guid = get_guid()
    cursor.execute(sql, (tripid, guid, title, latitude, longitude, arrivalDate, departureDate, website))
    cursor.connection.commit()

    return guid

def insert_trip(cursor, group_id, title):
    sql = """
        INSERT INTO trips (group_id, guid, title)
        VALUES (%s, %s, %s)
    """

    guid = get_guid()
    cursor.execute(sql, (group_id, guid, title))
    cursor.connection.commit()

    return guid


def validate_user(cursor, username, password):
    user = get_user(cursor, username)
    if not user:
        return False

    salt = user['salt']
    expected_hash = user['hashed_password']

    hashed_pw = hash_password(salt, password)

    return expected_hash == hashed_pw


def insert_user(cursor, username, firstname, lastname, email, password):
    sql = """
        INSERT INTO users (guid, username, firstname, lastname, email, hashed_password, salt)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    salt = generate_salt()

    hashed_password = hash_password(salt, password)

    guid = get_guid()

    cursor.execute(sql, (guid, username, firstname, lastname, email, hashed_password, salt))
    cursor.connection.commit()

    return guid


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
    sql = """
        SELECT locations.location_id, locations.trip_id, locations.guid, locations.title,
               locations.latitude, locations.longitude, locations.arrivalDate, 
               locations.departureDate, locations.url
        FROM locations
        JOIN users USING (user_id)
        where users.username = %s
    """

    cursor.execute(sql, username.encode("utf-8"))

    location_list = []
    location = cursor.fetchone()
    while (location != None):
        location_list.append({
            "location_id": location[0],
            "trip_id": location[1],
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



def get_trips(cursor, username):
    sql = """
        SELECT trips.trip_id, trips.group_id, trips.guid, trips.title
        FROM trips
        JOIN groups USING (group_id)
        JOIN users USING (user_id)
        WHERE users.username = %s
    """

    username = utf_encode(username)
    cursor.execute(sql, username)

    trips = []

    trip = cursor.fetchone()
    while (trip != None):
        trips.append( {
            "trip_id": trip[0],
            "group_id": trip[1],
            "guid": trip[2],
            "title": trip[3]
        })
        trip = cursor.fetchone()

    return trips


def get_groups(cursor, username, permission_name):
    sql = """
        SELECT groups.group_id, groups.guid, groups.name
        FROM groups
        FROM users USING (user_id)
        FROM permissions USING (permission_id)
        WHERE users.username = %s
            AND permission.name = %s
    """

    username = utf_encode(username)
    permission_name = utf_encode(permission_name)

    cursor.execute(sql, (username, permission_name))

    groups = []

    group = cursor.fetchone()
    while (group != None):
        groups.append({
            "group_id": group[0],
            "guid": group[1],
            "name": group[2]
        })
        group = cursor.fetchone()

    return groups