from scheduler.models import Assignment, Result
from scheduler.dashboard_utils import busy_minutes, schedule_csv, schedule_rows
from scheduler.io import load_sessions


def test_export_csv_and_metrics():
    result = Result('OPTIMAL', (Assignment('Alice', 'Mon', 960, 1020),), 0, 1, 60)
    assert busy_minutes(result) == 60
    assert schedule_rows(result)[0]['start'] == '16:00'
    assert 'Mon,16:00,17:00,Alice,60' in schedule_csv(result)


def test_empty_csv():
    assert len(schedule_csv(Result('OPTIMAL', (), 0, 0, 0)).splitlines()) == 1


def test_invalid_json_structure():
    try:
        load_sessions({'sessions': 'invalid'})
    except ValueError:
        pass
    else:
        assert False, 'Expected ValueError'


def test_json_parser():
    sessions = load_sessions({'sessions': [{'name': 'A', 'duration': 30, 'windows': [{'day': 'Mon', 'start': '10:00', 'end': '11:00'}]}]})
    assert sessions[0].windows[0].start == 600
