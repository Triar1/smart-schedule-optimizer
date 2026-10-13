from dataclasses import dataclass

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class Window:
    day: str
    start: int  # Minutes after midnight
    end: int

    def __post_init__(self):
        if self.day not in DAYS or not (0 <= self.start < self.end <= 1440):
            raise ValueError("Invalid availability window")


@dataclass(frozen=True)
class Session:
    name: str
    duration: int
    windows: tuple[Window, ...]

    def __post_init__(self):
        if not self.name or self.duration <= 0 or not self.windows:
            raise ValueError("Session needs a name, positive duration, and availability")


@dataclass(frozen=True)
class Assignment:
    name: str
    day: str
    start: int
    end: int


@dataclass(frozen=True)
class Result:
    status: str
    assignments: tuple[Assignment, ...]
    idle_minutes: int | None
    active_days: int | None = None
    objective_score: int | None = None
