import pytest
from scheduler.editor import flatten_sessions, rows_to_data


def test_roundtrip():
    original = {'sessions': [{'name': 'A', 'duration': 30, 'windows': [
        {'day': 'Mon', 'start': '09:00', 'end': '10:00'},
        {'day': 'Tue', 'start': '11:00', 'end': '12:00'}]}]}
    assert rows_to_data(flatten_sessions(original)) == original


def test_multiple_sessions():
    rows = [dict(session=n, duration=30, day='Mon', start='09:00', end='10:00') for n in ['A', 'B']]
    assert len(rows_to_data(rows)['sessions']) == 2


@pytest.mark.parametrize('changes', [
    {'session': ''}, {'duration': -1}, {'day': 'XYZ'},
    {'start': '25:00'}, {'end': '08:00'}, {'duration': 0},
])
def test_invalid_editor_row(changes):
    row = dict(session='A', duration=30, day='Mon', start='09:00', end='10:00')
    row.update(changes)
    with pytest.raises(ValueError):
        rows_to_data([row])


def test_inconsistent_duration():
    a = dict(session='A', duration=30, day='Mon', start='09:00', end='10:00')
    with pytest.raises(ValueError, match='Inconsistent duration'):
        rows_to_data([a, {**a, 'duration': 60}])


def test_empty_editor():
    assert rows_to_data([]) == {'sessions': []}
