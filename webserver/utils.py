from datetime import datetime, timedelta


def get_default_dates() -> tuple[str, str]:
    """
    Returns the default date range (start and end datetime strings).
    For the current date, start at 00:00:00 and end at 23:59:59.
    """
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
    end_of_day = (
        datetime.combine(today, datetime.min.time())
        + timedelta(hours=23, minutes=59, seconds=59)
    ).isoformat()
    return start_of_day, end_of_day
