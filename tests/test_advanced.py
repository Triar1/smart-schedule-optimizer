import pytest
from scheduler.models import Session, Window
from scheduler.optimizer import solve


def test_min_break_enforced():
    sessions = [
        Session("A", 30, (Window("Mon", 540, 660),)),
        Session("B", 30, (Window("Mon", 540, 660),)),
    ]
    result = solve(sessions, min_break=15)
    assert result.status == "OPTIMAL"
    a, b = sorted(result.assignments, key=lambda x: x.start)
    assert b.start - a.end >= 15
    assert result.idle_minutes == 15


def test_break_can_make_problem_infeasible():
    sessions = [
        Session("A", 30, (Window("Mon", 540, 600),)),
        Session("B", 30, (Window("Mon", 540, 600),)),
    ]
    assert solve(sessions, min_break=15).status == "INFEASIBLE"


def test_day_weight_consolidates_days():
    sessions = [
        Session("A", 60, (Window("Mon", 540, 600), Window("Tue", 540, 600))),
        Session("B", 60, (Window("Mon", 600, 660), Window("Tue", 600, 660))),
    ]
    result = solve(sessions, day_weight=60)
    assert result.status == "OPTIMAL"
    assert result.active_days == 1
    assert result.idle_minutes == 0
    assert result.objective_score == 60


def test_idle_metric_is_not_weighted_score():
    sessions = [
        Session("A", 30, (Window("Mon", 540, 570),)),
        Session("B", 30, (Window("Mon", 600, 630),)),
    ]
    result = solve(sessions, idle_weight=2, day_weight=50)
    assert result.idle_minutes == 30
    assert result.active_days == 1
    assert result.objective_score == 110


@pytest.mark.parametrize("kwargs", [
    {"min_break": -15}, {"min_break": 10},
    {"idle_weight": -1}, {"day_weight": -1},
    {"idle_weight": 0, "day_weight": 0},
    {"idle_weight": 1.5},
])
def test_invalid_options(kwargs):
    with pytest.raises(ValueError):
        solve([], **kwargs)
