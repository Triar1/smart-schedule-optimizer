# Smart Schedule Optimizer

[![Python tests](https://github.com/Triar1/smart-schedule-optimizer/actions/workflows/tests.yml/badge.svg)](https://github.com/Triar1/smart-schedule-optimizer/actions/workflows/tests.yml)

**An interactive constraint-programming application for scheduling sessions with availability windows, minimum breaks, and multiple optimization objectives.**

> Portfolio project · Python · Google OR-Tools CP-SAT · Streamlit · Plotly

## Live demo

Deploy on Streamlit Community Cloud (see below), then replace this line with your live URL.

## Demo screenshot

Add a screenshot of the running dashboard at `assets/dashboard.png` and embed it here before publicizing the project.

## Features

- Assign each session exactly once within its allowed availability windows.
- Support variable session durations and a configurable time grid.
- Prevent all overlaps on a shared single-resource calendar.
- Minimize **total daily idle time** between the first and last sessions.
- Return explicit `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE` solver statuses.
- CLI, sample dataset, and automated tests.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e '.[dev]'
smart-schedule examples/sample.json
pytest -q
```

For Windows PowerShell, install dependencies with `python -m pip install -e ".[dev]"`.

## Input format

See [`examples/sample.json`](examples/sample.json). Each session has a unique name, a duration in minutes, and one or more availability windows with `day`, `start`, and `end`.

## Mathematical model

Binary variable `x[s,t]` indicates that session `s` starts at feasible time `t`.
Each session is assigned exactly once, and at most one selected session occupies any time slot.
The objective minimizes `sum_d (last_end[d] - first_start[d] - busy_minutes[d])` over active days; inactive days contribute zero.

## Scope and limitations

V1 assumes one shared resource (e.g. one tutor), one session per name, no travel/break constraints, and a fixed weekly horizon. All session durations must be multiples of the time grid (default 15 minutes). Availability bounds are rounded inward to grid-aligned start times. A `FEASIBLE` result is valid but not necessarily globally optimal if the time limit is reached.

## Next steps

Support required breaks, multiple resources, participant priorities, fewer active days, and a Streamlit interface.


## V1.1 — Multi-objective scheduling

Set a minimum break (multiple of the slot size) and integer objective weights:

```powershell
smart-schedule examples/sample.json --min-break 15 --idle-weight 1 --day-weight 60
```

The objective is `idle_weight * idle_minutes + day_weight * active_days`.
A day weight of 60 treats an extra active day as costly as 60 idle minutes
when the idle weight is 1. Defaults (`--min-break 0 --idle-weight 1
--day-weight 0`) preserve V1 behavior.

The reported metrics are independent of the objective score. An `OPTIMAL`
status certifies the best score for the configured objective; a `FEASIBLE`
status indicates a solution was found but optimality was not proved within
the time limit.

## V2 — Interactive dashboard

Install from the project root (Windows PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m streamlit run src/scheduler/dashboard.py
```

Streamlit opens a local browser app. Use the sidebar to upload a JSON schedule,
set the minimum break and objective weights, and compare three optimization
strategies. The schedule can be downloaded as CSV. The CLI remains available:

```powershell
.\.venv\Scripts\smart-schedule.exe examples/sample.json --min-break 15 --idle-weight 1 --day-weight 60
```

Run the automated tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

**Optimization caveats:** `OPTIMAL` proves the minimum for the configured
objective; `FEASIBLE` only indicates a schedule was found before the time limit.
The weighted score is not comparable across different weight settings. The
minimum break is counted as idle time between sessions. Only time slots
aligned to the selected grid can be used. No data is sent to a remote service
by the app itself; uploaded data is processed in the local Streamlit process.

## V2.1: edit sessions in the browser

Run `python -m streamlit run src/scheduler/dashboard.py`, then edit the availability table and click **Apply changes**. Each row represents one availability window. Repeat the same session name to add multiple windows, using the same duration on each row. Add or delete rows using the table controls. Use **Download edited input JSON** to save your changes.

The dashboard displays the weekly schedule and allows comparison of three optimization strategies. Run the tests with `python -m pytest -v`.

**Notes:** The solver uses a discrete time grid; durations must be multiples of the chosen slot size. A `FEASIBLE` status is not proof of global optimality. The comparison chart uses separate axes for idle minutes and active days.


## Dashboard

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m streamlit run src/scheduler/dashboard.py
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud choose **Create app** and select this repository.
3. Set the main file path to `src/scheduler/dashboard.py`.
4. `requirements.txt` installs the project and its dependencies.
5. Once deployed, paste the public URL into the **Live demo** section above.

## Engineering notes

- One shared resource: all sessions are scheduled without overlap.
- Times are discrete; slot size must divide the day, and session durations must align with it.
- The solver may return `FEASIBLE` when the time limit expires: this does not certify optimality.
- The weighted objective is `idle_weight × idle_minutes + day_weight × active_days`.
- Do not upload private student data; the included sample uses fictitious names.

## License

MIT. See [LICENSE](LICENSE).
