import re
from datetime import datetime, timedelta, time
from dateutil import parser
from dateutil.relativedelta import relativedelta

def parse_datetime(time_string):
    if re.search("Just now", time_string, re.IGNORECASE):
        return datetime.now()

    if re.search("mins", time_string, re.IGNORECASE) or re.search("min", time_string, re.IGNORECASE):
        digits = re.findall('\\d+', time_string)[0]
        return datetime.now() - timedelta(minutes=int(digits))

    if re.search("hrs", time_string, re.IGNORECASE) or re.search("hr", time_string, re.IGNORECASE):
        digits = re.findall('\\d+', time_string)[0]
        return datetime.now() - timedelta(hours=int(digits))

    #if re.search("yesterday", time_string, re.IGNORECASE):
       # return datetime.now() - timedelta(days=1)
    
    if re.search("Yesterday at", time_string, re.IGNORECASE):
        digits = re.findall('\\d+', time_string)[0]
        digits_s = re.findall('\\d+', time_string)[1]
        midnight = datetime.combine(datetime.today(), time.min)
        yesterday_midnight = midnight - timedelta(days=1)
        return yesterday_midnight + timedelta(hours=int(digits)) + timedelta(minutes=int(digits_s))
    
    if re.search("at",time_string,re.IGNORECASE):
        return parser.parse(time_string)        
    
    if re.search("mths", time_string, re.IGNORECASE) or re.search("mth", time_string, re.IGNORECASE):
        digits = re.findall('\\d+', time_string)[0]
        return datetime.now() - relativedelta(months=int(digits))
    
    if re.search("yrs", time_string, re.IGNORECASE) or re.search("yr", time_string, re.IGNORECASE):
        digits = re.findall('\\d+', time_string)[0]
        return datetime.now() - relativedelta(years=int(digits))

    return False