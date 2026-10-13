"""Pure helpers for a flat, editable availability table."""
from .io import load_sessions
from .cli import format_time

COLUMNS = ('session', 'duration', 'day', 'start', 'end')


def flatten_sessions(data: dict) -> list[dict]:
    sessions = load_sessions(data)
    return [dict(session=s.name, duration=s.duration, day=w.day,
                 start=format_time(w.start), end=format_time(w.end))
            for s in sessions for w in s.windows]


def rows_to_data(rows: list[dict]) -> dict:
    """Validate table and rebuild the original JSON input format.

    Repeated session names are allowed only when their durations match;
    each row represents one availability window.
    """
    if not isinstance(rows, list):
        raise ValueError('Editor input must be a list of rows')
    grouped = {}
    for i, row in enumerate(rows, 1):
        try:
            name = row['session']
            duration = row['duration']
            day, start, end = row['day'], row['start'], row['end']
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Session name is required')
            name = name.strip()
            if isinstance(duration, bool) or not isinstance(duration, int):
                raise ValueError('Duration must be a whole number')
            if not all(isinstance(v, str) for v in (day, start, end)):
                raise ValueError('Day and times must be text')
            if name not in grouped:
                grouped[name] = {'name': name, 'duration': duration, 'windows': []}
            elif grouped[name]['duration'] != duration:
                raise ValueError(f'Inconsistent duration for {name}')
            grouped[name]['windows'].append({'day': day, 'start': start, 'end': end})
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f'Row {i}: {exc}') from exc
    data = {'sessions': list(grouped.values())}
    load_sessions(data)
    return data
