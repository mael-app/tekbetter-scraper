import json
import os
from datetime import datetime, timedelta

import requests
from app.logger import log_info, log_error, log_warning
from app.model.Student import Student

def split_dates(start: str, end: str, max_days: int) -> [(str, str)]:
    """
    Split a date range into multiple ranges of a maximum number of days
    :param start:
    :param end:
    :param max_days:
    :return:
    """

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    delta = end_date - start_date
    if delta.days <= max_days:
        return [(start, end)]

    dates = []
    current_start = start_date
    while current_start < end_date:
        current_end = current_start + timedelta(days=max_days)
        if current_end > end_date:
            current_end = end_date
        dates.append((current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d")))
        current_start = current_end + timedelta(days=1)
    return dates