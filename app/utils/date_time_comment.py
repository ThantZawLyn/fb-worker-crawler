import re
from datetime import datetime, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta

def convert_date_comment(datestring):
    WEEK = {
        "Mon": "Monday",
        "Tue": "Tuesday",
        "Wed": "Wednesday",
        "Thu": "Thursday",
        "Fri": "Friday",
        "Sat": "Saturday",
        "Sun": "Sunday"
    }

    MONTHS = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }
    def parse_datetime_comment(time_string):
        if re.search("Just now", time_string, re.IGNORECASE):
            return datetime.now()

        if re.search("mins", time_string, re.IGNORECASE) or re.search("min", time_string, re.IGNORECASE):
            digits = re.findall('\\d+', time_string)[0]
            return datetime.now() - timedelta(minutes=int(digits))

        if re.search("hrs", time_string, re.IGNORECASE) or re.search("hr", time_string, re.IGNORECASE):
            digits = re.findall('\\d+', time_string)[0]
            return datetime.now() - timedelta(hours=int(digits))

        if re.search("yesterday", time_string, re.IGNORECASE):
            return datetime.now() - timedelta(days=1)
    
        if re.search("at",time_string,re.IGNORECASE):
            return parser.parse(time_string)
    
        if re.search("mths", time_string, re.IGNORECASE) or re.search("mth", time_string, re.IGNORECASE):
            digits = re.findall('\\d+', time_string)[0]
            return datetime.now() - relativedelta(months=int(digits))
    
        if re.search("yrs", time_string, re.IGNORECASE) or re.search("yr", time_string, re.IGNORECASE):
            digits = re.findall('\\d+', time_string)[0]
            return datetime.now() - relativedelta(years=int(digits))
    current_datetime = datetime.now()
    # For "on Tue" of "last Fri" dates
    if datestring.split(" ")[0] == "on" or datestring.split(" ")[0] == "last":
        posted_day = WEEK[datestring.split(" ")[1]]
        posted_datetime = current_datetime
        counter = 0
        while posted_datetime.strftime("%A") != posted_day and counter < 10:
            posted_datetime += timedelta(days=-1)
            counter += 1

    # For "12 hrs" dates
    elif datestring.split(" ")[-1] == "hrs":
        delta_hours = int(datestring.split(" ")[0])
        posted_datetime = current_datetime + timedelta(hours=-delta_hours)
        
        
    # For "1 wk" dates
    elif datestring.split(" ")[-1] == "wk" or datestring.split(" ")[-1] == "wks":
        delta_week = int(datestring.split(" ")[0])
        posted_datetime = current_datetime + timedelta(days=-7 * delta_week)
        
    # For "November 17, 2019 at 15:45 PM", "November 17" etc. dates
    else:
        posted_datetime = parse_datetime_comment(datestring)
        if (posted_datetime == None):
            year = current_datetime.year
            month = current_datetime.month
            day = current_datetime.day
            hour = current_datetime.hour
            minute = current_datetime.minute

            for month_string in MONTHS.keys():
                if month_string + " " in datestring or month_string[:3] + " " in datestring:
                    month = MONTHS[month_string].replace(",", "")
                    day = datestring.split(" ")[1].replace(",", "")

                    if ", " in datestring:
                        year = datestring.split(", ")[1].split(" ")[0]
                    if "at" in datestring:
                        time_string = datestring.split(" ")[-2]
                        hour, minute = time_string.split(":")
                        ampm = datestring.split(" ")[-1]
                        if ampm == "PM":
                            hour = int(hour) + 12
            # To isoformat
            year = int(year)
            month = int(month)
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            posted_datetime = datetime.fromisoformat(f"{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}")        
    return posted_datetime