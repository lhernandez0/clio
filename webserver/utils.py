from datetime import datetime, timedelta


def get_default_dates() -> tuple[str, str]:
    """
    Returns the default date range (start and end datetime strings) for the past 30 days.
    The end date is set to the current day at 23:59:59, and the start date is 30 days before at 00:00:00.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)  # 30 days including today

    start_of_range = datetime.combine(start_date, datetime.min.time()).isoformat()
    end_of_range = (
        datetime.combine(end_date, datetime.min.time())
        + timedelta(hours=23, minutes=59, seconds=59)
    ).isoformat()

    return start_of_range, end_of_range
