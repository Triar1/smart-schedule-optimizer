# Smart Schedule Optimizer v1.0.0

First stable public release of an interactive constraint-based weekly scheduling optimizer.

### Highlights
- CP-SAT scheduling engine with availability, duration, overlap and minimum-break constraints.
- Weighted optimization of idle time and active working days.
- Streamlit dashboard with editable sessions, weekly calendar and strategy comparison.
- JSON input, CSV output and command-line interface.
- Automated pytest checks and GitHub Actions CI.

### Live demo
https://smart-schedule-optimizer-triar1.streamlit.app/

### Scope
The solver models one shared resource and a discrete weekly time grid. `FEASIBLE` does not guarantee optimality. Use fictional or anonymized data in the public demo.
