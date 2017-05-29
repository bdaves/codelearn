import pymysql

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

CREATE_LOCATION_TABLE = """
    CREATE TABLE IF NOT EXISTS locations( 
            location_id INT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            guid CHAR(32) NOT NULL,
            title VARCHAR(128) NOT NULL, 
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            arrivalDate DATE,
            departureDate DATE,
            url VARCHAR(256), 
            PRIMARY KEY ( location_id ),
            FOREIGN KEY ( user_id )
                REFERENCES users( user_id )
                ON DELETE RESTRICT );
"""

CREATE_TRIP_TABLE = """
    CREATE TABLE IF NOT EXISTS trips(
            trip_id INT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            guid CHAR(32) NOT NULL,
            title VARCHAR(128) NOT NULL,
            PRIMARY KEY ( trip_id ),
            FOREIGN KEY ( user_id )
                REFERENCES users( user_id )
                ON DELETE RESTRICT );

"""

CREATE_TRIP_LOCATION_TABLE = """
    CREATE TABLE IF NOT EXISTS trip_locations(
            trip_id INT NOT NULL,
            location_id INT NOT NULL,
            trip_order INT NOT NULL,
            FOREIGN KEY ( trip_id )
                REFERENCES trips( trip_id )
                ON DELETE RESTRICT,
            FOREIGN KEY ( location_id )
                REFERENCES locations( location_id )
                ON DELETE RESTRICT );
"""

CREATE_USER = """
    DELETE FROM users where username='dummy';
    INSERT INTO users (guid, username, firstname, lastname, email, hashed_password, 
    salt) VALUES ('d853add444a911e7bb72acbc32871233', 'dummy', 'Dum', 'My', 
    'dummy@parityerror.com',
    '438a858f29e03aa31aecc8b97d425769a0aaf5c09f44b8aa439b8615a795805a',
    'hE5cRD7Z0sO86KYrpacy9NMIrqySH61j5cYcCziD4c6vD4T883iJdA3mdOM9iJdf' );
"""
conn = pymysql.connect(host='localhost', user='codelearn', passwd='codelearn', db='codelearn')

cur = conn.cursor()

cur.execute(CREATE_USERS_TABLE)
cur.execute(CREATE_LOCATION_TABLE)
cur.execute(CREATE_TRIP_TABLE)
cur.execute(CREATE_TRIP_LOCATION_TABLE)
#cur.execute(CREATE_USER)
conn.commit()

cur.close()

conn.close()
