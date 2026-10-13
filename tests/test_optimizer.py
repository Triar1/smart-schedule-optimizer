import pytest
from scheduler.models import Session, Window
from scheduler.optimizer import solve


def test_empty():
    assert solve([]).idle_minutes == 0


def test_compact_schedule():
    sessions = [
        Session("A", 60, (Window("Mon", 540, 720),)),
        Session("B", 60, (Window("Mon", 540, 720),)),
    ]
    result = solve(sessions)
    assert result.status == "OPTIMAL"
    assert result.idle_minutes == 0
    assert len(result.assignments) == 2
    a, b = result.assignments
    assert a.end <= b.start or b.end <= a.start


def test_infeasible():
    sessions = [Session("A", 60, (Window("Mon", 540, 600),)),
                Session("B", 60, (Window("Mon", 540, 600),))]
    assert solve(sessions).status == "INFEASIBLE"


def test_short_window():
    result = solve([Session("A", 60, (Window("Mon", 540, 570),))])
    assert result.status == "INFEASIBLE"


def test_bad_duration():
    with pytest.raises(ValueError):
        solve([Session("A", 20, (Window("Mon", 540, 600),))])


def test_duplicate_names():
    s = Session("A", 30, (Window("Mon", 540, 600),))
    with pytest.raises(ValueError):
        solve([s, s])


def test_windows_respected():
    s = Session("A", 45, (Window("Tue", 600, 660),))
    result = solve([s])
    assert result.assignments[0].day == "Tue"
    assert result.assignments[0].start >= 600
    assert result.assignments[0].end <= 660
