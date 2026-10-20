"""Turn free-form messages into a small, evolving profile (rule-based, no LLM needed)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Profile:
    diet: str = "veg"
    weight_kg: float | None = None
    goal: str = "maintain"  # lose, maintain, gain
    dislikes: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    @property
    def protein_target_g(self) -> int:
        """Daily protein planning target in grams per kg of body weight, by goal."""
        per_kg = {"lose": 1.4, "maintain": 1.2, "gain": 1.6}[self.goal]
        return round((self.weight_kg or 60) * per_kg)

    @property
    def kcal_target(self) -> int:
        base = (self.weight_kg or 60) * 30
        return round(base * {"lose": 0.85, "maintain": 1.0, "gain": 1.15}[self.goal])


def update_profile(p: Profile, text: str) -> list[str]:
    """Apply what the message says. Returns human-readable changes."""
    low = text.lower()
    changes: list[str] = []
    if re.search(r"\bnon[- ]?veg(etarian)?\b|\bi eat (chicken|fish|meat)\b", low):
        p.diet = "nonveg"
        changes.append("diet: non-veg")
    elif re.search(r"\begg(etarian)?\b", low):
        p.diet = "egg"
        changes.append("diet: eggetarian")
    elif re.search(r"\bveg(etarian)?\b|\bvegan\b", low):
        p.diet = "veg"
        changes.append("diet: vegetarian")
    m = re.search(r"(\d{2,3}(?:\.\d)?)\s*(?:kg|kgs|kilos?)\b", low)
    if m and 30 <= float(m.group(1)) <= 250:
        p.weight_kg = float(m.group(1))
        changes.append(f"weight: {p.weight_kg:g} kg")
    if re.search(r"lose weight|weight loss|\bcut\b|slim", low):
        p.goal = "lose"
        changes.append("goal: lose weight")
    elif re.search(r"gain|bulk|build muscle", low):
        p.goal = "gain"
        changes.append("goal: gain")
    elif re.search(r"maintain", low):
        p.goal = "maintain"
        changes.append("goal: maintain")
    for d in re.findall(r"(?:hate|dislike|don't like|do not like|no)\s+([a-z ]{3,25})", low):
        item = d.strip().split(" and ")[0].strip()
        if item and item not in p.dislikes:
            p.dislikes.add(item)
            changes.append(f"dislikes: {item}")
    return changes
