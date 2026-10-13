"""Pure presentation helpers, independently testable without Streamlit."""
import csv
import io
from .models import DAYS, Result
from .cli import format_time


def schedule_rows(result: Result) -> list[dict]:
    return [dict(day=a.day, start=format_time(a.start), end=format_time(a.end),
                 session=a.name, duration_minutes=a.end-a.start)
            for a in result.assignments]


def schedule_csv(result: Result) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['day', 'start', 'end', 'session', 'duration_minutes'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(schedule_rows(result))
    return output.getvalue()


def busy_minutes(result: Result) -> int:
    return sum(a.end - a.start for a in result.assignments)


def day_order(day: str) -> int:
    return DAYS.index(day)
