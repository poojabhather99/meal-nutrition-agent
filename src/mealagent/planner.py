"""Weekly planner: protein-first, diet-respecting, seasonal, deterministic."""

from __future__ import annotations

from dataclasses import dataclass

from .foods import ALLOWED, BuiltinFoods, Food, FoodSource
from .profile import Profile

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEALS = ("breakfast", "lunch", "dinner")


@dataclass
class MealItem:
    food: Food
    grams: int

    @property
    def protein(self) -> float:
        return self.food.protein_g * self.grams / 100

    @property
    def kcal(self) -> float:
        return self.food.kcal * self.grams / 100


@dataclass
class DayPlan:
    day: str
    meals: dict[str, list[MealItem]]

    @property
    def protein(self) -> float:
        return sum(i.protein for m in self.meals.values() for i in m)

    @property
    def kcal(self) -> float:
        return sum(i.kcal for m in self.meals.values() for i in m)


def _eligible(profile: Profile, foods: list[Food], month: int, kind: str) -> list[Food]:
    ok = ALLOWED[profile.diet]
    out = [
        f for f in foods
        if f.kind == kind and f.diet in ok and f.name not in profile.dislikes
        and not any(d in f.name for d in profile.dislikes)
        and (not f.months or month in f.months)
    ]
    return sorted(out, key=lambda f: f.name)


def plan_week(profile: Profile, month: int, source: FoodSource | None = None) -> list[DayPlan]:
    foods = (source or BuiltinFoods()).all()
    proteins = sorted(_eligible(profile, foods, month, "protein"),
                      key=lambda f: -f.protein_g / max(f.kcal, 1))
    all_grains = _eligible(profile, foods, month, "grain")
    grains = [g for g in all_grains if not g.breakfast]
    breakfast_grains = [g for g in all_grains if g.breakfast] or grains
    veg = _eligible(profile, foods, month, "vegetable")
    if not proteins or not grains:
        raise ValueError("no eligible foods for this profile")
    per_meal_protein = profile.protein_target_g / len(MEALS)
    per_meal_kcal = profile.kcal_target / len(MEALS)
    week: list[DayPlan] = []
    for d, day in enumerate(DAYS):
        meals: dict[str, list[MealItem]] = {}
        for m, meal in enumerate(MEALS):
            p = proteins[(d * len(MEALS) + m) % len(proteins)]
            pool = breakfast_grains if meal == "breakfast" else grains
            g = pool[(d + m) % len(pool)]
            v = veg[(d + m) % len(veg)] if (veg and meal != "breakfast") else None
            veg_item = MealItem(v, 150) if v else None
            # first guess at protein grams, then size the grain to reach the calorie share
            p_grams = min(max(round(per_meal_protein / p.protein_g * 100 / 10) * 10, 50), 300)
            grain_g = 150
            for _ in range(2):  # grain adds protein too: re-balance once
                grain_prot = g.protein_g * grain_g / 100
                need = max(per_meal_protein - grain_prot, 0)
                p_grams = min(max(round(need / p.protein_g * 100 / 10) * 10, 50), 300)
                rest = per_meal_kcal - p.kcal * p_grams / 100 - (veg_item.kcal if veg_item else 0)
                grain_g = min(max(round(rest / g.kcal * 100 / 10) * 10, 80), 350)
            items = [MealItem(p, p_grams), MealItem(g, grain_g)]
            if veg_item:
                items.append(veg_item)
            meals[meal] = items
        week.append(DayPlan(day, meals))
    return week


def shopping_list(week: list[DayPlan]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for day in week:
        for items in day.meals.values():
            for i in items:
                totals[i.food.name] = totals.get(i.food.name, 0) + i.grams
    return dict(sorted(totals.items()))


def format_day(d: DayPlan) -> str:
    lines = [f"{d.day}  (~{round(d.protein)} g protein, ~{round(d.kcal)} kcal)"]
    for meal, items in d.meals.items():
        lines.append(f"  {meal}: " + ", ".join(f"{i.food.name} {i.grams} g" for i in items))
    return "\n".join(lines)
