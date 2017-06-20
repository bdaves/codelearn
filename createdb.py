import pymysql
import travelapp.config as cfg

CREATE_USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS users(
        user_id INT NOT NULL AUTO_INCREMENT,
        guid CHAR(32) NOT NULL,
        username VARCHAR(64) NOT NULL,
        firstname VARCHAR(64) NOT NULL,
        lastname VARCHAR(64) NOT NULL,
        email VARCHAR(128) NOT NULL,
        verified BOOLEAN DEFAULT 0,
        registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hashed_password VARCHAR(64) NOT NULL,
        salt VARCHAR(64) NOT NULL,
        PRIMARY KEY( user_id ));

"""

CREATE_PERMISSION_TABLE = """
    CREATE TABLE IF NOT EXISTS permissions(
            permission_id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(32) NOT NULL,
            can_read BOOLEAN DEFAULT 0,
            can_write BOOLEAN DEFAULT 0,
            can_delete BOOLEAN DEFAULT 0,
            can_modify_group BOOLEAN DEFAULT 0,
            PRIMARY KEY ( permission_id ));

"""

CREATE_GROUP_TABLE = """
    CREATE TABLE IF NOT EXISTS groups(
            group_id INT NOT NULL AUTO_INCREMENT,
            guid CHAR(32) NOT NULL, 
            name VARCHAR(128) NOT NULL,
            PRIMARY KEY ( group_id ));

"""


CREATE_GROUP_MEMBER_TABLE = """
    CREATE TABLE IF NOT EXISTS group_members(
            group_id INT NOT NULL,
            user_id INT NOT NULL,
            permission_id INT NOT NULL,
            PRIMARY KEY ( group_id, user_id ),
            FOREIGN KEY ( permission_id )
                REFERENCES permissions( permission_id )
                ON DELETE RESTRICT,
            FOREIGN KEY ( group_id )
                REFERENCES groups( group_id )
                ON DELETE CASCADE,
            FOREIGN KEY ( user_id )
                REFERENCES users( user_id )
                ON DELETE CASCADE );

"""

CREATE_TRIP_TABLE = """
    CREATE TABLE IF NOT EXISTS trips(
            trip_id INT NOT NULL AUTO_INCREMENT,
            group_id INT NOT NULL,
            guid CHAR(32) NOT NULL,
            title VARCHAR(128) NOT NULL,
            PRIMARY KEY ( trip_id ),
            FOREIGN KEY ( group_id )
                REFERENCES groups( group_id )
                ON DELETE CASCADE );

"""

CREATE_LOCATION_TABLE = """
    CREATE TABLE IF NOT EXISTS locations( 
            location_id INT NOT NULL AUTO_INCREMENT,
            trip_id INT NOT NULL,
            guid CHAR(32) NOT NULL,
            title VARCHAR(128) NOT NULL, 
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            arrivalDate DATE,
            departureDate DATE,
            url VARCHAR(256), 
            PRIMARY KEY ( location_id ),
            FOREIGN KEY ( trip_id )
                REFERENCES trips( trip_id )
                ON DELETE CASCADE );
"""



CREATE_TRIP_LOCATION_TABLE = """
    CREATE TABLE IF NOT EXISTS trip_locations(
            trip_id INT NOT NULL PRIMARY KEY,
            location_order TEXT NOT NULL,
            FOREIGN KEY ( trip_id )
                REFERENCES trips( trip_id )
                ON DELETE CASCADE );
"""

def insert_permission(cursor, name, read, write, delete, modify):
    sql = """
        INSERT INTO permissions (name, can_read, can_write, can_delete, can_modify_group)
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (name, read, write, delete, modify))

    cursor.connection.commit()




cfg.printconfig()
conn = pymysql.connect(host=cfg.DB_HOST, user=cfg.DB_USERNAME, passwd=cfg.DB_PASSWORD, db=cfg.DB_DATABASE)

cur = conn.cursor()

cur.execute(CREATE_USERS_TABLE)
cur.execute(CREATE_PERMISSION_TABLE)
cur.execute(CREATE_GROUP_TABLE)
cur.execute(CREATE_GROUP_MEMBER_TABLE)
cur.execute(CREATE_TRIP_TABLE)
cur.execute(CREATE_LOCATION_TABLE)
cur.execute(CREATE_TRIP_LOCATION_TABLE)

conn.commit()

insert_permission(cur, "OWNER", 1, 1, 1, 1)
insert_permission(cur, "MODERATOR", 1, 1, 0, 1)
insert_permission(cur, "MEMBER", 1, 1, 0, 0)
insert_permission(cur, "READER", 1, 0, 0, 0)

cur.close()

conn.close()
