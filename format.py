def time_worked(seconds_worked):
    response = ""
    hour_in_seconds = 1 * 60 * 60

    if seconds_worked < 60:
        response += "%d seconds" % seconds_worked
    else:
        if seconds_worked > hour_in_seconds:
            hours_worked = seconds_worked // hour_in_seconds
            response += "%d hours" % int(hours_worked)
            seconds_worked -= hours_worked * 60 * 60
            if seconds_worked >= 60:
                response+= " "

        if seconds_worked >= 60:
            minutes_worked = seconds_worked // 60
            response += "%d minutes" % int(minutes_worked)
            seconds_worked -= minutes_worked * 60

    return response