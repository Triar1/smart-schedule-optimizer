"""Shared JSON input validation for CLI and dashboard."""
from .models import Session, Window
from .cli import parse_time


def load_sessions(data: dict) -> list[Session]:
    if not isinstance(data, dict) or not isinstance(data.get('sessions'), list):
        raise ValueError("Input must be an object containing a 'sessions' list")
    sessions = []
    for idx, item in enumerate(data['sessions'], start=1):
        try:
            sessions.append(Session(
                item['name'], item['duration'],
                tuple(Window(w['day'], parse_time(w['start']), parse_time(w['end']))
                      for w in item['windows'])
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Invalid session #{idx}: {exc}') from exc
    return sessions
