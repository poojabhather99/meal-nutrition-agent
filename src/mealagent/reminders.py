"""Day-ahead reminders: tell the user tonight what to prepare or order tomorrow."""

from __future__ import annotations

from datetime import date, timedelta

from .planner import DAYS, DayPlan


def reminder_for(week: list[DayPlan], today: date) -> str:
    tomorrow = today + timedelta(days=1)
    day = next(d for d in week if d.day == DAYS[tomorrow.weekday()])
    parts = [f"{m}: " + ", ".join(i.food.name for i in items) for m, items in day.meals.items()]
    return f"Tomorrow ({day.day}) - " + " | ".join(parts)


def is_planning_day(today: date) -> bool:
    """The weekly planning conversation happens on Sundays."""
    return today.weekday() == 6
