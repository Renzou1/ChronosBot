import psycopg2
from psycopg2 import sql
import os
import database_info
from dotenv import load_dotenv

load_dotenv()

def default_cursor():
    connection = psycopg2.connect(
        host = os.getenv("DB_HOST"),
        dbname = 'postgres',
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        port = os.getenv("DB_PORT")
    )

    connection.autocommit = True

    return connection.cursor(), connection

def connect_to_database():
    connection = psycopg2.connect(
    host = os.getenv("DB_HOST"),
    dbname = database_info.name(),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    port = os.getenv("DB_PORT")
    )

    connection.autocommit = True
    cursor = connection.cursor()

    return cursor, connection

def create_or_connect_to_database():
    temp_cursor, temp_connection = default_cursor()

    exists = database_exists(temp_cursor)
    
    if not exists:
        return create_database(temp_cursor, temp_connection)
    
    temp_cursor.close()
    temp_connection.close() 
    return connect_to_database()


def database_exists(temp_cursor):
    
    #check if private db exists
    temp_cursor.execute(
        """
        select exists(
        SELECT datname FROM pg_database WHERE lower(datname) = lower(%s)
        );
        """, (database_info.name(),)
)
    
    exists = temp_cursor.fetchone()

    return exists[0]

def create_database(temp_cursor, temp_connection):

    temp_cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_info.name())))

    temp_cursor.close()
    temp_connection.close()

    cursor, connection = connect_to_database()

    cursor.execute(
        """
        CREATE TABLE HOURS(
        WORKER_ID VARCHAR(18) NOT NULL,
        GUILD_ID VARCHAR(20) NOT NULL,
        START_TIME TIMESTAMPTZ,
        END_TIME TIMESTAMPTZ DEFAULT NULL,

        PRIMARY KEY (WORKER_ID, START_TIME, GUILD_ID)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE TIMEZONES(
        GUILD_ID VARCHAR(20) NOT NULL,
        TIMEZONE INT DEFAULT 0,

        PRIMARY KEY (GUILD_ID)
        );
        """
    )

    return cursor, connection