import database_inner_workings
import database_info
import psycopg2
import format
from psycopg2 import sql


def is_working(cursor, worker_id):
    cursor.execute(
                    """
                    SELECT EXISTS(
                    SELECT * FROM HOURS
                    WHERE END_TIME is NULL AND WORKER_ID = %s
                    )
                    """, (str(worker_id),)
    )
    result = cursor.fetchall()[0][0]

    return result

    
def get_seconds_worked(cursor, worker_id, datetime):
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM %s::timestamp - HOURS.START_TIME) FROM HOURS
                    WHERE END_TIME is NULL AND WORKER_ID = %s
                    """, (datetime, str(worker_id))
    ) 
    seconds_worked = cursor.fetchall()[0][0]

    return seconds_worked


def start_working(guild_id, worker_id, datetime):
    cursor, connection = database_inner_workings.database_cursor(guild_id)

    if is_working(cursor, worker_id):
        return "You're already working!"
    
    cursor.execute(
                   """
                   INSERT INTO HOURS (WORKER_ID, START_TIME)
                   VALUES (%s, %s::timestamp)
                   """, (str(worker_id), datetime))
    
    cursor.close()
    connection.close()
    return "Tracking begins. Good work!"

def stop_working(guild_id, worker_id, datetime):
    cursor, connection = database_inner_workings.database_cursor(guild_id)

    if not is_working(cursor, worker_id):
        cursor.close()
        connection.close()
        return "You aren't working yet. Try the 'start working' slash command."

    seconds_worked = get_seconds_worked(cursor, worker_id, datetime)

    cursor.execute(
                   """
                   UPDATE HOURS
                   SET END_TIME = %s::timestamp
                   WHERE WORKER_ID = %s AND END_TIME IS NULL
                   """, (datetime, str(worker_id)))
    
    response = "You've worked for "
    time = format.time_worked(seconds_worked) 
    response += time
    response += ", good job! Time for some rest..."

    cursor.close()
    connection.close()
    return response

def status(guild_id, worker_id, datetime):
    cursor, connection = database_inner_workings.database_cursor(guild_id)
    if not is_working(cursor, worker_id):
        cursor.close()
        connection.close()
        return "You are currently not working."

    seconds_worked = get_seconds_worked(cursor, worker_id, datetime)    

    response = "You have been working for "
    time = format.time_worked(seconds_worked) 
    response += time
    response += "."

    cursor.close()
    connection.close()
    return response


def calculate_work_hours(guild_id, worker_id, month, year):
    cursor, connection = database_inner_workings.database_cursor(guild_id)
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM SUM(HOURS.END_TIME - HOURS.START_TIME)) FROM HOURS
                    WHERE EXTRACT(month FROM HOURS.END_TIME) = %s
                    AND EXTRACT(year FROM HOURS.END_TIME) = %s
                    AND HOURS.WORKER_ID = %s
                    """, (month, year, str(worker_id))
    )
                # this returns a list of tuples, but we only have one value
    response = cursor.fetchall()[0][0]

    cursor.close()
    connection.close()
    if response == None:
        return 0
    
    return float(response) / 60 / 60

def get_sessions(guild_id, worker_id, month, year):
    cursor, connection = database_inner_workings.database_cursor(guild_id)
    cursor.execute(
                    """
                    SELECT START_TIME, END_TIME FROM HOURS
                    WHERE EXTRACT(month FROM HOURS.START_TIME) = %s 
                    AND EXTRACT(year FROM HOURS.START_TIME) = %s
                    AND HOURS.WORKER_ID = %s
                    ORDER BY HOURS.START_TIME
                    """, (month, year, str(worker_id))
    )
    data = cursor.fetchall()
    start = []
    end = []
    diffs = []

    for i in range(len(data)):
        start.append(data[i][0])
        end.append(data[i][1])
        diffs.append(get_diff(cursor, data[i][1], data[i][0]))

    cursor.close()
    connection.close()
    return start, end, diffs

def get_sessions_from_cursor(cursor, worker_id, month, year):
    cursor.execute(
                    """
                    SELECT START_TIME, END_TIME FROM HOURS
                    WHERE EXTRACT(month FROM HOURS.START_TIME) = %s 
                    AND EXTRACT(year FROM HOURS.START_TIME) = %s
                    AND HOURS.WORKER_ID = %s
                    ORDER BY HOURS.START_TIME
                    """, (month, year, str(worker_id))
    )
    data = cursor.fetchall()
    start = []
    end = []
    diffs = []

    for i in range(len(data)):
        start.append(data[i][0])
        end.append(data[i][1])
        diffs.append(get_diff(cursor, data[i][1], data[i][0]))

    return start, end, diffs

def get_diff(cursor, date1, date2):
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
    cursor, connection = database_inner_workings.database_cursor(guild_id)
    start, end, diffs = get_sessions_from_cursor(cursor, worker_id, month, year)
    if session_id > len(start) or session_id < 0:
        cursor.close()
        connection.close()
        return "Session not found."
    
    cursor.execute("""
                        DELETE FROM HOURS
                        WHERE WORKER_ID = %s
                        AND START_TIME = %s::timestamp       
                        """, (str(worker_id), start[session_id]))
    
    cursor.close()
    connection.close()
    return "Done."

def timezone(guild_id, UTC):
    cursor, connection = database_inner_workings.database_cursor(guild_id)

    cursor.execute(sql.SQL("ALTER DATABASE {} SET TIMEZONE TO %s").format(sql.Identifier(database_info.name(guild_id))), (UTC,))

    cursor.close()
    connection.close()

# assumes valid hours/minutes
def remove_time_from_session(guild_id, worker_id, month, year, session_id, hours, minutes):
    cursor, connection = database_inner_workings.database_cursor(guild_id)
    minutes += hours * 60
    seconds_to_remove = minutes * 60
    minutes,hours = 0,0

    start, end, diffs = get_sessions_from_cursor(cursor, worker_id, month, year)
    if session_id > len(start) or session_id < 0:
        cursor.close()
        connection.close()
        return "Session not found."
   
    cursor.execute(
                    """
                    SELECT EXTRACT (EPOCH FROM HOURS.END_TIME - HOURS.START_TIME) FROM HOURS
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s
                    """, (start[session_id], str(worker_id))
    )
    seconds_worked = cursor.fetchall()[0][0]
    if seconds_worked < seconds_to_remove:
        cursor.execute(
                    """
                    DELETE FROM HOURS
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s
                    """, (start[session_id], str(worker_id))
                    )
        cursor.close()
        connection.close()
        return "Time to remove exceeded the session's time, session removed."
    else:
        cursor.execute(
                    """
                    UPDATE HOURS
                    SET END_TIME = END_TIME - INTERVAL %s
                    WHERE START_TIME = %s::timestamp AND WORKER_ID = %s
                    """, (str(seconds_to_remove) + " seconds", start[session_id], str(worker_id))
        )    
        cursor.close()
        connection.close()
        return "Removed %s from session." % format.time_worked(seconds_to_remove)
