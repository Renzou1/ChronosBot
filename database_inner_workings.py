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
        port = 5432
    )

    connection.autocommit = True

    return connection.cursor(), connection

def connect_to_database(guild_id):
    connection = psycopg2.connect(
    host = os.getenv("DB_HOST"),
    dbname = database_info.name(guild_id),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    port = 5432
    )

    connection.autocommit = True
    cursor = connection.cursor()

    return cursor, connection

def database_cursor(guild_id):
    temp_cursor, temp_connection = default_cursor()

    exists = database_exists(guild_id, temp_cursor)
    
    if not exists:
        return create_database(guild_id, temp_cursor, temp_connection)
    
    return connect_to_database(guild_id)


def database_exists(guild_id, temp_cursor):
    
    #check if private db exists
    temp_cursor.execute(
        """
        select exists(
        SELECT datname FROM pg_database WHERE lower(datname) = lower(%s)
        );
        """, (database_info.name(guild_id),)
)
    
    exists = temp_cursor.fetchone()

    return exists[0]

def create_database(guild_id, temp_cursor, temp_connection):

    temp_cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_info.name(guild_id))))

    temp_cursor.close()
    temp_connection.close()

    cursor, connection = connect_to_database(guild_id)

    cursor.execute(
        """
        CREATE TABLE HOURS(
        WORKER_ID VARCHAR(18) NOT NULL,
        START_TIME TIMESTAMPTZ,
        END_TIME TIMESTAMPTZ DEFAULT NULL,

        PRIMARY KEY (WORKER_ID, START_TIME)
        );
        """
    )

    return cursor, connection