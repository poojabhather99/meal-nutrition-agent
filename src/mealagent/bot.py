"""Transport-independent command router. A Telegram adapter only calls `handle`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .planner import DayPlan, format_day, plan_week, shopping_list
from .profile import Profile, update_profile
from .reminders import reminder_for

DISCLAIMER = ("This is meal-planning help with approximate numbers, not medical or "
              "dietetic advice.")
HELP = ("/plan - plan the week\n/today - today's meals\n/remind - tomorrow's prep\n"
        "/shopping - grocery list\n/profile - what I know about you\n"
        "Or just tell me: 'I am eggetarian, 62 kg, want to gain muscle, I hate okra'.")


@dataclass
class Session:
    profile: Profile = field(default_factory=Profile)
    week: list[DayPlan] | None = None


class Bot:
    def __init__(self, today=date.today):
        self.sessions: dict[int, Session] = {}
        self.today = today

    def handle(self, chat_id: int, text: str) -> str:
        s = self.sessions.setdefault(chat_id, Session())
        text = (text or "").strip()[:1000]
        if not text:
            return HELP
        cmd = text.split()[0].lower()
        today = self.today()
        if cmd in ("/start", "/help"):
            return f"{HELP}\n\n{DISCLAIMER}"
        if cmd == "/profile":
            p = s.profile
            return (f"diet: {p.diet}, weight: {p.weight_kg or 'unknown'} kg, goal: {p.goal}, "
                    f"dislikes: {', '.join(sorted(p.dislikes)) or 'none'}\n"
                    f"daily protein target ~{p.protein_target_g} g, ~{p.kcal_target} kcal")
        if cmd == "/plan":
            s.week = plan_week(s.profile, today.month)
            return "\n\n".join(format_day(d) for d in s.week) + f"\n\n{DISCLAIMER}"
        if cmd in ("/today", "/remind", "/shopping"):
            if s.week is None:
                return "No plan yet. Send /plan first."
            if cmd == "/today":
                return format_day(next(d for d in s.week if d.day == _day_name(today)))
            if cmd == "/remind":
                return reminder_for(s.week, today)
            return "\n".join(f"{k}: {v} g" for k, v in shopping_list(s.week).items())
        changes = update_profile(s.profile, text)
        if changes:
            s.week = None  # profile changed: the old plan is stale
            return "Got it. " + "; ".join(changes) + ". Send /plan to rebuild the week."
        return "I didn't pick up anything to change. " + HELP


def _day_name(d: date) -> str:
    from .planner import DAYS

    return DAYS[d.weekday()]
