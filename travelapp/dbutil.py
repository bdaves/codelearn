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
    if isinstance(value, str):
        return value.encode('utf-8')

    return value


def insert_location(cursor, trip_guid, title, latitude, longitude, arrival_date, departure_date, website):
    sql = """
        INSERT INTO locations (trip_id, guid, title, latitude, longitude, arrivalDate, departureDate, url)
        VALUES ((SELECT trip_id FROM trips where trips.guid=%s), %s, %s, %s, %s, %s, %s, %s)
    """

    location_guid = get_guid()
    cursor.execute(sql, (trip_guid, location_guid, title, latitude, longitude, arrival_date, departure_date, website))
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


def delete_group(cursor, group_guid):
    sql = """
        DELETE FROM groups
        WHERE guid=%s
    """

    cursor.execute(sql, group_guid)

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


def validate_user(cursor, username, password, token=None):
    """
    Overloaded function which helps to validate new users, makes sure they have already
    been validated, or they are validating and have a valid validation token

    :param cursor: Database cursor
    :param username: Username requested validation
    :param password: Password supplied by user
    :param token: Only required if verifying new user
    :return: None - not yet validated, and no validation token provided,
            True if username and password match
    """
    user = get_user(cursor, username)
    if not user:
        return False, None

    salt = user['salt']
    expected_hash = user['hashed_password']

    hashed_pw = hash_password(salt, password)

    valid_pw = expected_hash == hashed_pw
    if not valid_pw:
        # User didn't authenticate, so don't allow any further actions
        return False, None

    user_verified = user['verified'] == 1
    if user_verified:
        return True, None

    valid_token = (token is not None) and (token == user['verification_token'])
    if valid_token:
        return True, None

    # User still needs to verify
    return None, user.get('guid', None)


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


def make_user_dict(columns):
    return {
        "user_id": columns[0],
        "guid": columns[1],
        "username": columns[2],
        "firstname": columns[3],
        "lastname": columns[4],
        "email": columns[5],
        "verified": columns[6],
        "registered": columns[7],
        "hashed_password": columns[8],
        "salt": columns[9],
        "verification_token": columns[10],
        "verified_date": columns[11],
        "password_reset_open": columns[12],
        "password_change_count": columns[13],
        "last_password_change": columns[14]
    }


def get_user(cursor, username):
    sql = """
        SELECT user_id, guid, username, firstname, lastname, email, verified, registered,
               hashed_password, salt, verification_token, verified_date, password_reset_open,
               password_change_count, last_password_change
        FROM users
        WHERE username=%s
    """

    count = cursor.execute(sql, username)
    if count != 1:
        return None

    user = cursor.fetchone()

    if not user:
        return None

    return make_user_dict(user)


def get_user_by_guid(cursor, user_guid):
    sql = """
        SELECT user_id, guid, username, firstname, lastname, email, verified, registered,
               hashed_password, salt, verification_token, verified_date, password_reset_open,
               password_change_count, last_password_change
        FROM users
        WHERE guid=%s
    """

    count = cursor.execute(sql, user_guid)
    if count != 1:
        return None

    user = cursor.fetchone()

    if not user:
        return None

    return make_user_dict(user)


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

    while location is not None:
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
    while trip is not None:
        trips.append({
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


def is_valid_username(cursor, username):
    sql = """
        SELECT username
        from users
        WHERE username=%s
    """
    username = utf_encode(username)

    cursor.execute(sql, username)

    user = cursor.fetchone()
    if not user:
        return False
    return True


def is_valid_email(cursor, email):
    sql = """
        SELECT email
        from users
        WHERE email=%s
    """
    email = utf_encode(email)

    cursor.execute(sql, email)

    user = cursor.fetchone()
    if not user:
        return False
    return True


def insert_member_by_email(cursor, group_guid, email, permission_id):
    sql = """
        REPLACE INTO group_members(group_id, user_id, permission_id)
        SELECT groups.group_id, users.user_id, %s
        FROM groups JOIN users
        WHERE groups.guid = %s
            AND users.email = %s
    """

    group_guid = utf_encode(group_guid)
    email = utf_encode(email)
    permission_id = utf_encode(permission_id)

    cursor.execute(sql, (permission_id, group_guid, email))

    cursor.connection.commit()


def insert_member_by_username(cursor, group_guid, username, permission_id):
    sql = """
        REPLACE INTO group_members(group_id, user_id, permission_id)
        SELECT groups.group_id, users.user_id, %s
        FROM groups JOIN users
        WHERE groups.guid = %s
            AND users.username = %s
    """

    group_guid = utf_encode(group_guid)
    username = utf_encode(username)
    permission_id = utf_encode(permission_id)

    cursor.execute(sql, (permission_id, group_guid, username))

    cursor.connection.commit()


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


def add_to_group(cursor, group_guid, emails, usernames, permission_id):
    for email in emails:
        if is_valid_email(cursor, email):
            insert_member_by_email(cursor, group_guid, email, permission_id)
    for username in usernames:
        if is_valid_username(cursor, username):
            insert_member_by_username(cursor, group_guid, username, permission_id)


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
    while group is not None:
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
       FROM trips WHERE trips.guid=%s
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


def get_permissions(cursor):
    sql = """
        SELECT permission_id, name
        FROM permissions
    """

    cursor.execute(sql)

    permissions = []

    permission = cursor.fetchone()
    while permission is not None:
        permissions.append({
            "permission_id": permission[0],
            "name": permission[1]
        })
        permission = cursor.fetchone()

    return permissions


def has_permissions(cursor, username, group_guid, permissions):
    sql = """
        SELECT permissions.name
        FROM users
        JOIN groups
        JOIN group_members using (group_id, user_id)
        JOIN permissions using (permission_id)
        WHERE users.username = %s
            AND groups.guid = %s
    """

    username = utf_encode(username)
    group_guid = utf_encode(group_guid)

    cursor.execute(sql, (username, group_guid))

    permission = cursor.fetchone()[0]

    return permission in permissions


def get_permissions_list(cursor, column_name):
    sql = """
        SELECT name
        FROM permissions
        WHERE {0} = 1
    """.format(column_name)

    cursor.execute(sql)

    permission_list = cursor.fetchall()

    permission_names = []
    for permission in permission_list:
        permission_names.append(permission[0])

    return permission_names


def get_members(cursor, guid):
    sql = """
        SELECT users.username, permissions.name
        FROM groups
        JOIN group_members USING (group_id)
        JOIN permissions USING (permission_id)
        JOIN users USING (user_id)
        WHERE groups.guid = %s
    """

    cursor.execute(sql, guid)

    members = cursor.fetchall()

    member_list = []
    for member in members:
        member_list.append({
            "name": member[0],
            "permission": member[1]
        })
    return member_list


def user_logged_in(cursor, username):
    """Update statistics about user logging in"""

    sql = """
    UPDATE users SET last_login=NOW(), login_count=login_count + 1
    WHERE users.username = %s
    """

    username = utf_encode(username)
    cursor.execute(sql, username)
    cursor.connection.commit()


def user_is_verified(cursor, username):
    """Mark that a user has been verified"""

    sql = """
    UPDATE users SET verified=1, verification_token=NULL, verified_date=NOW(),
                     last_login=NOW(), login_count=login_count+1
    WHERE users.username = %s
    """

    username = utf_encode(username)

    cursor.execute(sql, username)
    cursor.connection.commit()


def set_verification_token(cursor, user_guid, token):
    """Record a new verification token for the user"""

    sql = """
    UPDATE users SET verification_token=%s
    WHERE users.guid=%s
    """

    cursor.execute(sql, (token, user_guid))
    cursor.connection.commit()
