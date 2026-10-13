import argparse
import json
from pathlib import Path
from .models import Session, Window
from .optimizer import solve


def parse_time(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    if not (0 <= hour <= 24 and 0 <= minute < 60) or (hour == 24 and minute != 0):
        raise ValueError(f"Invalid time: {value}")
    return hour * 60 + minute


def format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize a weekly session schedule")
    parser.add_argument("input", type=Path, help="JSON input file")
    parser.add_argument("--slot", type=int, default=15)
    parser.add_argument("--time-limit", type=float, default=15.0)
    parser.add_argument("--min-break", type=int, default=0, help="Required break in minutes")
    parser.add_argument("--idle-weight", type=int, default=1)
    parser.add_argument("--day-weight", type=int, default=0)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    sessions = [Session(s["name"], s["duration"], tuple(
        Window(w["day"], parse_time(w["start"]), parse_time(w["end"]))
        for w in s["windows"])) for s in data["sessions"]]
    result = solve(
        sessions, args.slot, args.time_limit,
        min_break=args.min_break,
        idle_weight=args.idle_weight, day_weight=args.day_weight,
    )
    print(f"Status: {result.status}")
    if result.idle_minutes is not None:
        print(f"Total idle time: {result.idle_minutes} minutes")
        print(f"Active days: {result.active_days}")
        print(f"Objective score: {result.objective_score}")
        for a in result.assignments:
            print(f"{a.day} {format_time(a.start)}–{format_time(a.end)}  {a.name}")


if __name__ == "__main__":
    main()
