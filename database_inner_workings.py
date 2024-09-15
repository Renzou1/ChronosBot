import psycopg2
from psycopg2 import sql
import os
import database_info
from dotenv import load_dotenv

load_dotenv()

def _create_default_connection():
    connection = psycopg2.connect(
        host = os.getenv("DB_HOST"),
        dbname = 'postgres',
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        port = os.getenv("DB_PORT")
    )

    connection.autocommit = True

    return connection

_connections = {
    'default': _create_default_connection()
}

__all__ = ['get_connection', 'restart_connection']

def get_connection(guild_id: str):
    if guild_id not in _connections.keys():
        _connections[guild_id] = _create_or_connect_to_database(guild_id)

    return _connections[guild_id]

def restart_connection(guild_id: str):
    _connections[guild_id].close()
    _connections[guild_id] = _connect_to_database(guild_id)

def _create_or_connect_to_database(guild_id):
    default_connection = _connections['default']
    default_cursor = default_connection.cursor()

    exists = _database_exists(guild_id, default_cursor)

    if not exists:
        return _create_database(guild_id, default_cursor)
    
    default_cursor.close()
    return _connect_to_database(guild_id)

def _connect_to_database(guild_id):
    connection = psycopg2.connect(
    host = os.getenv("DB_HOST"),
    dbname = database_info.name(guild_id),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    port = os.getenv("DB_PORT")
    )

    connection.autocommit = True
    return connection

def _database_exists(guild_id, default_cursor):
    
    #check if private db exists
    default_cursor.execute(
        """
        select exists(
        SELECT datname FROM pg_database WHERE lower(datname) = lower(%s)
        );
        """, (database_info.name(guild_id),)
)
    
    exists = default_cursor.fetchone()
    return exists[0]

def _create_database(guild_id, default_cursor):

    default_cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_info.name(guild_id))))

    default_cursor.close()

    connection = _connect_to_database(guild_id)
    cursor = connection.cursor()

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

    cursor.close()
    return connection