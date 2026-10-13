from collections import defaultdict
from ortools.sat.python import cp_model
from .models import DAYS, Assignment, Result, Session


def solve(
    sessions: list[Session],
    slot_minutes: int = 15,
    max_seconds: float = 15.0,
    min_break: int = 0,
    idle_weight: int = 1,
    day_weight: int = 0,
) -> Result:
    """Optimize idle time and active days, respecting availability and minimum breaks.

    The weights are nonnegative integers. With day_weight=0 and min_break=0,
    this preserves the V1 objective. A break is required between any two
    sessions on the same day, regardless of their order.
    """
    if slot_minutes <= 0 or 1440 % slot_minutes or max_seconds <= 0:
        raise ValueError("Invalid grid size or time limit")
    if min_break < 0 or min_break % slot_minutes:
        raise ValueError("min_break must be a nonnegative multiple of slot_minutes")
    if (not isinstance(idle_weight, int) or isinstance(idle_weight, bool)
            or not isinstance(day_weight, int) or isinstance(day_weight, bool)
            or idle_weight < 0 or day_weight < 0
            or idle_weight + day_weight == 0):
        raise ValueError("Weights must be nonnegative integers, with at least one positive")
    if len({s.name for s in sessions}) != len(sessions):
        raise ValueError("Session names must be unique")
    if not sessions:
        return Result("OPTIMAL", (), 0, 0, 0)
    if any(s.duration % slot_minutes for s in sessions):
        raise ValueError("Durations must be multiples of slot_minutes")

    model = cp_model.CpModel()
    choices = {}
    day_assignments = defaultdict(list)
    occupancy = defaultdict(list)
    # Reserve a post-session buffer to enforce breaks in either order.
    # Buffer slots past midnight are harmless: no next-day sessions overlap them.
    for i, session in enumerate(sessions):
        candidates = set()
        for w in session.windows:
            first = ((w.start + slot_minutes - 1) // slot_minutes) * slot_minutes
            for start in range(first, w.end - session.duration + 1, slot_minutes):
                candidates.add((w.day, start))
        if not candidates:
            return Result("INFEASIBLE", (), None)
        variables = []
        for day, start in sorted(candidates, key=lambda x: (DAYS.index(x[0]), x[1])):
            v = model.NewBoolVar(f"s{i}_{day}_{start}")
            choices[(i, day, start)] = v
            variables.append(v)
            day_assignments[day].append((start, start + session.duration, v))
            for minute in range(start, start + session.duration + min_break, slot_minutes):
                occupancy[(day, minute)].append(v)
        model.AddExactlyOne(variables)

    for variables in occupancy.values():
        model.AddAtMostOne(variables)

    idle_vars = []
    active_vars = []
    for day, entries in day_assignments.items():
        active = model.NewBoolVar(f"active_{day}")
        model.AddMaxEquality(active, [v for _, _, v in entries])
        active_vars.append(active)
        first = model.NewIntVar(0, 1440, f"first_{day}")
        last = model.NewIntVar(0, 1440, f"last_{day}")
        starts = []
        ends = []
        for j, (start, end, selected) in enumerate(entries):
            a = model.NewIntVar(0, 1440, f"start_candidate_{day}_{j}")
            b = model.NewIntVar(0, 1440, f"end_candidate_{day}_{j}")
            model.Add(a == start).OnlyEnforceIf(selected)
            model.Add(a == 1440).OnlyEnforceIf(selected.Not())
            model.Add(b == end).OnlyEnforceIf(selected)
            model.Add(b == 0).OnlyEnforceIf(selected.Not())
            starts.append(a)
            ends.append(b)
        raw_first = model.NewIntVar(0, 1440, f"raw_first_{day}")
        model.AddMinEquality(raw_first, starts)
        model.Add(first == raw_first).OnlyEnforceIf(active)
        model.Add(first == 0).OnlyEnforceIf(active.Not())
        model.AddMaxEquality(last, ends)
        busy = sum((end - start) * v for start, end, v in entries)
        idle = model.NewIntVar(0, 1440, f"idle_{day}")
        model.Add(idle == last - first - busy)
        idle_vars.append(idle)

    model.Minimize(idle_weight * sum(idle_vars) + day_weight * sum(active_vars))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_seconds
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return Result(solver.StatusName(status), (), None)
    assignments = []
    for (i, day, start), v in choices.items():
        if solver.Value(v):
            assignments.append(Assignment(sessions[i].name, day, start, start + sessions[i].duration))
    assignments.sort(key=lambda a: (DAYS.index(a.day), a.start))
    # Calculate observable metrics from the returned assignments rather than
    # confusing the weighted objective score with idle minutes.
    grouped = defaultdict(list)
    for a in assignments:
        grouped[a.day].append(a)
    idle_minutes = sum(
        max(a.end for a in items) - min(a.start for a in items)
        - sum(a.end - a.start for a in items)
        for items in grouped.values()
    )
    active_days = len(grouped)
    score = idle_weight * idle_minutes + day_weight * active_days
    return Result(solver.StatusName(status), tuple(assignments), idle_minutes, active_days, score)
