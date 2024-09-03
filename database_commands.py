import database_inner_workings
import database_info
import psycopg2
import format
from psycopg2 import sql

def database_init():
    global cursor
    global connection
    cursor, connection = database_inner_workings.create_or_connect_to_database()

def is_working(guild_id, worker_id):
    cursor.execute(
                    """
                    SELECT EXISTS(
                    SELECT * FROM HOURS
                    WHERE END_TIME is NULL AND WORKER_ID = %s AND GUILD_ID = %s
                    )
                    """, (worker_id, guild_id)
    )
    result = cursor.fetchall()[0][0]

    return result

    
def get_seconds_worked(guild_id, worker_id, datetime):
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM %s::timestamp - HOURS.START_TIME) FROM HOURS
                    WHERE END_TIME is NULL AND WORKER_ID = %s AND GUILD_ID = %s
                    """, (datetime, worker_id, guild_id)
    ) 
    seconds_worked = cursor.fetchall()[0][0]

    return seconds_worked


def start_working(guild_id, worker_id, datetime):
    if is_working(guild_id, worker_id):
        return "You're already working!"
    
    cursor.execute(
                   """
                   INSERT INTO HOURS (WORKER_ID, START_TIME, GUILD_ID)
                   VALUES (%s, %s::timestamp, %s)
                   """, (worker_id, datetime, guild_id)
                   )
    
    return "Tracking begins. Good work!"

def stop_working(guild_id, worker_id, datetime):
    if not is_working(guild_id, worker_id):
        return "You aren't working yet. Try the 'start working' slash command."

    seconds_worked = get_seconds_worked(guild_id, worker_id, datetime)

    cursor.execute(
                   """
                   UPDATE HOURS
                   SET END_TIME = %s::timestamp
                   WHERE WORKER_ID = %s AND END_TIME IS NULL AND GUILD_ID = %s
                   """, (datetime, worker_id, guild_id)
                   )
    
    response = "You've worked for "
    time = format.time_worked(seconds_worked) 
    response += time
    response += ", good job! Time for some rest..."

    return response

def status(guild_id, worker_id, datetime):
    if not is_working(guild_id, worker_id):
        return "You are currently not working."

    seconds_worked = get_seconds_worked(guild_id, worker_id, datetime)    

    response = "You have been working for "
    time = format.time_worked(seconds_worked) 
    response += time
    response += "."

    return response

def calculate_work_hours(guild_id, worker_id, month, year):
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM SUM(HOURS.END_TIME - HOURS.START_TIME)) FROM HOURS
                    WHERE EXTRACT(month FROM HOURS.END_TIME) = %s
                    AND EXTRACT(year FROM HOURS.END_TIME) = %s
                    AND HOURS.WORKER_ID = %s
                    AND GUILD_ID = %s
                    """, (month, year, worker_id, guild_id)
    )
                # this returns a list of tuples, but we only have one value
    response = cursor.fetchall()[0][0]

    if response == None:
        return 0
    
    return float(response) / 60 / 60

def get_sessions(guild_id, worker_id, month, year):
    UTC = get_timezone(guild_id)
    cursor.execute(
                    """
                    SELECT START_TIME AT TIME ZONE %s, END_TIME AT TIME ZONE %s FROM HOURS
                    WHERE EXTRACT(month FROM HOURS.START_TIME) = %s 
                    AND EXTRACT(year FROM HOURS.START_TIME) = %s
                    AND HOURS.WORKER_ID = %s
                    AND HOURS.GUILD_ID = %s
                    ORDER BY HOURS.START_TIME
                    """, (UTC, UTC, month, year, worker_id, guild_id)
    )
    data = cursor.fetchall()
    start = []
    end = []
    diffs = []

    for i in range(len(data)):
        start.append(data[i][0])
        end.append(data[i][1])
        diffs.append(get_diff(data[i][1], data[i][0]))

    return start, end, diffs

def get_diff(date1, date2):
    if date1 == None:
        return None
    
    cursor.execute(
                        """
                        SELECT EXTRACT(EPOCH FROM %s::timestamp - %s::timestamp)
                        """, (date1, date2))
    seconds = cursor.fetchall()[0][0]

    hours = seconds // (60 * 60)
    seconds -= hours * 60 * 60
    
    minutes = seconds // 60
    seconds -= minutes * 60
    
    return hours, minutes, seconds

def delete_session(guild_id, worker_id, session_id, month, year):
    start, end, diffs = get_sessions(guild_id, worker_id, month, year)
    if session_id > len(start) or session_id < 0:
        return "Session not found."
    
    cursor.execute("""
                        DELETE FROM HOURS
                        WHERE WORKER_ID = %s
                        AND START_TIME = %s::timestamp
                        AND GUILD_ID = %s       
                        """, (worker_id, start[session_id], guild_id)
                        )
    
    return "Done."

def timezone(guild_id, UTC):
    if exists_timezone(guild_id):
        cursor.execute(
                        """
                        UPDATE TIMEZONES
                        SET TIMEZONE = %s
                        WHERE GUILD_ID = %s
                        """, (UTC, guild_id)
        )
    else:
        cursor.execute(
                """
                INSERT INTO TIMEZONES (GUILD_ID, TIMEZONE)
                VALUES (%s, %s)
                """, (guild_id, UTC)
                )

def exists_timezone(guild_id):
    cursor.execute(
                    """
                    SELECT EXISTS(
                    SELECT * FROM TIMEZONES
                    WHERE GUILD_ID = %s
                    )
                    """, (guild_id,)
    )
    exists = cursor.fetchall()[0][0]
    return exists

def get_timezone(guild_id):
    if exists_timezone(guild_id):
        cursor.execute(
                        """
                        SELECT TIMEZONE FROM TIMEZONES
                        WHERE GUILD_ID = %s
                        """, (guild_id,)
                        )
        return str(cursor.fetchall()[0][0])
    else:
        return "0"

# use before getting timezone-specific time
def get_guild_timezone(guild_id):

    exists = exists_timezone(guild_id)
    if exists:
        cursor.execute(
                        """
                        SELECT TIMEZONE
                        FROM TIMEZONES
                        WHERE GUILD_ID = %s
                        """, (guild_id,)
                    )
        UTC = cursor.fetchall()[0][0]
    else:
        UTC = "0"

    return UTC
    

# assumes valid hours/minutes
def remove_time_from_session(guild_id, worker_id, month, year, session_id, hours, minutes):
    minutes += hours * 60
    seconds_to_remove = minutes * 60
    minutes,hours = 0,0

    start, end, diffs = get_sessions(guild_id, worker_id, month, year)
    if session_id > len(start) or session_id < 0:
        return "Session not found."
   
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM HOURS.END_TIME - HOURS.START_TIME) FROM HOURS
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s AND GUILD_ID = %s
                    """, (start[session_id], worker_id, guild_id)
                    )
    seconds_worked = cursor.fetchall()[0][0]
    if seconds_worked < seconds_to_remove:
        cursor.execute(
                    """
                    DELETE FROM HOURS
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s AND GUILD_ID = %s
                    """, (start[session_id], worker_id, guild_id)
                    )
        return "Time to remove exceeded the session's time, session removed."
    else:
        cursor.execute(
                    """
                    UPDATE HOURS
                    SET END_TIME = END_TIME - INTERVAL %s
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s AND GUILD_ID = %s
                    """, (str(seconds_to_remove) + " seconds", start[session_id], worker_id, guild_id)
        )    
        return "Removed %s from session." % format.time_worked(seconds_to_remove)
