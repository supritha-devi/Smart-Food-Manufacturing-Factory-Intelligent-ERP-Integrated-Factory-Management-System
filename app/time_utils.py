from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


FACTORY_TIMEZONE = ZoneInfo("Asia/Kolkata")


def now():
    return datetime.now(FACTORY_TIMEZONE)


def now_iso():
    return now().replace(microsecond=0).isoformat()


def format_date(value):
    parsed = parse_datetime(value)
    return parsed.strftime("%d-%m-%Y") if parsed else ""


def format_datetime(value):
    parsed = parse_datetime(value)
    return parsed.strftime("%d-%m-%Y %I:%M:%S %p") if parsed else ""


def format_time(value):
    parsed = parse_datetime(value)
    return parsed.strftime("%I:%M %p") if parsed else ""


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            for pattern in ("%d-%m-%Y %I:%M %p", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(text, pattern)
                    break
                except ValueError:
                    continue
            else:
                return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=FACTORY_TIMEZONE)
    return parsed.astimezone(FACTORY_TIMEZONE)


def elapsed_seconds(start, end=None):
    start_dt = parse_datetime(start)
    if not start_dt:
        return 0
    end_dt = parse_datetime(end) if end else now()
    if not end_dt:
        return 0
    return max(0, int((end_dt - start_dt).total_seconds()))


def working_minutes(check_in, check_out, break_minutes=0):
    start = parse_datetime(check_in)
    end = parse_datetime(check_out)
    if not start or not end:
        return 0
    if end <= start:
        end += timedelta(days=1)
    minutes = max(0, int((end - start).total_seconds() // 60) - max(0, break_minutes))
    return minutes


def overtime_minutes(check_in, check_out, standard_minutes=480, break_minutes=30):
    worked = working_minutes(check_in, check_out, break_minutes)
    return max(0, worked - standard_minutes)
