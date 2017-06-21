import pymysql
import uuid
import hashlib
import string
import random
import json
import sqlalchemy.pool as pool

from . import config as cfg

CHAR_SET = string.ascii_letters + string.digits


def new_connection():
    print("Created a new MySQL connection")
    return pymysql.connect(host=cfg.DB_HOST, user=cfg.DB_USERNAME, 
                           passwd=cfg.DB_PASSWORD, db=cfg.DB_DATABASE)


conn_pool = pool.QueuePool(new_connection, max_overflow=10, pool_size=30)


def connect():
    return conn_pool.connect()


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


def insert_location(cursor, trip_guid, title, latitude, longitude, arrivalDate, departureDate, website):
    sql = """
        INSERT INTO locations (trip_id, guid, title, latitude, longitude, arrivalDate, departureDate, url)
        VALUES ((SELECT trip_id FROM trips where trips.guid=%s), %s, %s, %s, %s, %s, %s, %s)
    """

    location_guid = get_guid()
    cursor.execute(sql, (trip_guid, location_guid, title, latitude, longitude, arrivalDate, departureDate, website))
    cursor.connection.commit()

    return location_guid

def insert_short_location(cursor, trip_guid, title, latitude, longitude):
    sql = """
        INSERT INTO locations (trip_id, guid, title, latitude, longitude)
        VALUES ((SELECT trip_id FROM trips where trips.guid=%s), %s, %s, %s, %s)
    """

    location_guid = get_guid()

    cursor.execute(sql, (trip_guid, location_guid, title, latitude, longitude))
    cursor.connection.commit()

    return location_guid

def delete_location(cursor, trip_guid, location_guid):
    sql = """
        DELETE locations.* FROM locations
        JOIN trips USING (trip_id)
        WHERE trips.guid = %s AND locations.guid = %s
    """

    cursor.execute(sql, (trip_guid, location_guid))

    cursor.connection.commit()


def insert_trip(cursor, group_guid, title):
    sql = """
        INSERT INTO trips (group_id, guid, title)
        VALUES ((SELECT group_id from groups where groups.guid = %s), %s, %s)
    """

    trip_guid = get_guid()
    cursor.execute(sql, (group_guid, trip_guid, utf_encode(title)))
    cursor.connection.commit()

    return trip_guid

def delete_trip(cursor, trip_guid):
    sql = """
        DELETE FROM trips
        WHERE guid=%s
    """

    cursor.execute(sql, trip_guid)

    cursor.connection.commit()



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

    if not user:
        return None

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


def get_locations(cursor, trip_guid):
    sql = """
        SELECT locations.location_id, locations.trip_id, locations.guid, locations.title,
               locations.latitude, locations.longitude, locations.arrivalDate, 
               locations.departureDate, locations.url
        FROM locations 
        JOIN trips USING (trip_id)
        where trips.guid = %s
    """

    cursor.execute(sql, utf_encode(trip_guid))

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
        FROM users
        JOIN group_members USING (user_id)
        JOIN groups USING (group_id)
        JOIN trips USING (group_id)
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

def get_trip(cursor, trip_guid):

    sql = """
        SELECT trips.trip_id, trips.group_id, trips.guid, trips.title, trip_locations.location_order
        FROM trips 
        LEFT JOIN trip_locations using (trip_id)
        WHERE trips.guid = %s
    """

    cursor.execute(sql, utf_encode(trip_guid))

    trip = cursor.fetchone()

    if not trip: 
        return None

    if trip[4]:
        order = json.loads(trip[4])
    else:
        order = None

    return {
        "trip_id": trip[0],
        "group_id": trip[1],
        "guid": trip[2],
        "title": trip[3],
        "order": order
        }


def insert_group(cursor, name):
    sql = """
        INSERT INTO groups ( guid, name )
        VALUES (%s, %s)
    """

    name = utf_encode(name)
    guid = get_guid()

    cursor.execute(sql, (guid, name))

    cursor.connection.commit()

    return guid


def insert_group_member(cursor, group_guid, username, permission_name):
    sql = """
        INSERT INTO group_members ( group_id, user_id, permission_id )
        SELECT groups.group_id, users.user_id, permissions.permission_id
        FROM groups JOIN users JOIN permissions
        WHERE groups.guid = %s
            AND users.username = %s
            AND permissions.name = %s;
    """ 

    group_guid = utf_encode(group_guid)
    username = utf_encode(username)
    permission_name = utf_encode(permission_name)
    

    cursor.execute(sql, (group_guid, username, permission_name))

    cursor.connection.commit()


def get_groups(cursor, username):
    sql = """
        SELECT groups.group_id, groups.guid, groups.name
        FROM users
        JOIN group_members USING (user_id)
        JOIN groups USING (group_id)
        WHERE users.username = %s
    """

    username = utf_encode(username)

    cursor.execute(sql, username)

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


def insert_order(cursor, trip_guid, location_order):
    sql = """
       REPLACE INTO trip_locations (trip_id, location_order) 
       SELECT trips.trip_id, %s 
       FROM trips WHERE trips.guid=%s;
    """

    location_order = json.dumps(location_order)

    cursor.execute(sql, (location_order, trip_guid))

    cursor.connection.commit()


def get_order(cursor, trip_guid):
    sql = """
        SELECT location_order
        FROM trip_locations
        JOIN trips using (trip_id)
        WHERE trips.guid=%s
    """

    cursor.execute(sql, trip_guid)

    locations = cursor.fetchone()
    if not locations:
        return None

    locations = json.loads(locations[0])

    return locations



