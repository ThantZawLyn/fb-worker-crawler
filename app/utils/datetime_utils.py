import re
from datetime import datetime, timedelta, time
from dateutil import parser
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU



def parse_datetime(time_string):
    try:
        time_string = time_string.strip()

        if re.search(r"\bJust now\b", time_string, re.IGNORECASE):
            return datetime.now()
        
        if re.search(r"\bmins\b|\bmin\b|\bm\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - timedelta(minutes=int(digits[0]))
        
        if re.search(r"\bhrs\b|\bhr\b|\bh\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - timedelta(hours=int(digits[0]))
        
        if re.search(r"\ban hour ago\b", time_string, re.IGNORECASE):
            return datetime.now() - timedelta(hours=1)
        
        if re.search(r"\bhours ago\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - timedelta(hours=int(digits[0]))
        
        if re.search(r"\ba day ago\b", time_string, re.IGNORECASE):
            return datetime.now() - timedelta(days=1)
        
        if re.search(r"\bdays ago\b|\bd\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - timedelta(days=int(digits[0]))
        
        if re.search(r"\bYesterday at\b", time_string, re.IGNORECASE):
            time_part = time_string.split("at")[-1].strip()
            yesterday = datetime.now() - timedelta(days=1)
            return datetime.combine(yesterday.date(), parser.parse(time_part).time())
        
        if re.search(r"\bwks\b|\bwk\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - timedelta(weeks=int(digits[0]))
        
        if re.search(r"\bmths\b|\bmth\b|\bmos\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - relativedelta(months=int(digits[0]))
        
        if re.search(r"\byrs\b|\byr\b", time_string, re.IGNORECASE):
            digits = re.findall(r'\d+', time_string)
            if digits:
                return datetime.now() - relativedelta(years=int(digits[0]))

        if re.search(r"\bon\b", time_string, re.IGNORECASE):
            if re.search(r"\bon Mon\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=MO(-1))
            if re.search(r"\bon Tue\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=TU(-1))
            if re.search(r"\bon Wed\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=WE(-1))
            if re.search(r"\bon Thu\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=TH(-1))
            if re.search(r"\bon Fri\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=FR(-1))
            if re.search(r"\bon Sat\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=SA(-1))
            if re.search(r"\bon Sun\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=SU(-1))
        
        if re.search(r"\blast\b", time_string, re.IGNORECASE):
            if re.search(r"\blast Mon\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=MO(-1))
            if re.search(r"\blast Tue\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=TU(-1))
            if re.search(r"\blast Wed\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=WE(-1))
            if re.search(r"\blast Thu\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=TH(-1))
            if re.search(r"\blast Fri\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=FR(-1))
            if re.search(r"\blast Sat\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=SA(-1))
            if re.search(r"\blast Sun\b", time_string, re.IGNORECASE):
                return datetime.now() + relativedelta(weekday=SU(-1))
        
        # Handle month-day format without year by adding the current year
        if re.search(r'^\d{1,2} \w+$', time_string, re.IGNORECASE):
            date_str = f"{time_string} {datetime.now().year}"
            parsed_date = parser.parse(date_str)
            if parsed_date > datetime.now():
                parsed_date = parsed_date - relativedelta(years=1)
            return parsed_date
        
        if re.search(r'^\w+ \d{1,2}$', time_string, re.IGNORECASE):
            date_str = f"{time_string} {datetime.now().year}"
            parsed_date = parser.parse(date_str)
            if parsed_date > datetime.now():
                parsed_date = parsed_date - relativedelta(years=1)
            return parsed_date
        
        if re.search(r'^Added Today at \d{1,2}:\d{2}$', time_string, re.IGNORECASE):
            time_part = time_string.split("at")[-1].strip()
            today = datetime.now().date()
            return datetime.combine(today, parser.parse(time_part).time())

        # Generic date parsing fallback
        return parser.parse(time_string)
    
    except Exception as e:
        print(f"Error parsing date time string '{time_string}': {e}")
        return None