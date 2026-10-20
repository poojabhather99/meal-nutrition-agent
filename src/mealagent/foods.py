"""Small built-in food table.

Values are APPROXIMATE per-100 g figures for cooked or ready-to-eat foods, entered by hand as
rough planning numbers. They are not pulled from USDA FoodData Central. `FoodSource` is the
interface to replace this table with a real FoodData Central client.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Food:
    name: str
    kcal: float
    protein_g: float
    diet: str  # "veg", "egg" or "nonveg"
    kind: str  # "protein", "grain", "vegetable"
    months: tuple[int, ...] = ()  # seasonal months for vegetables; empty = all year
    breakfast: bool = False  # grains only: True = breakfast food, False = lunch/dinner food


FOODS = [
    Food("paneer", 265, 18, "veg", "protein"),
    Food("tofu", 145, 15, "veg", "protein"),
    Food("moong dal", 105, 7, "veg", "protein"),
    Food("chickpeas", 165, 9, "veg", "protein"),
    Food("rajma", 125, 8.5, "veg", "protein"),
    Food("greek yogurt", 60, 10, "veg", "protein"),
    Food("egg", 150, 12.5, "egg", "protein"),
    Food("chicken breast", 165, 31, "nonveg", "protein"),
    Food("fish (rohu)", 130, 20, "nonveg", "protein"),
    Food("brown rice", 125, 2.7, "veg", "grain"),
    Food("roti (whole wheat)", 260, 9, "veg", "grain"),
    Food("oats", 70, 2.5, "veg", "grain", (), True),
    Food("spinach", 25, 3, "veg", "vegetable", (11, 12, 1, 2, 3)),
    Food("cauliflower", 25, 2, "veg", "vegetable", (11, 12, 1, 2)),
    Food("peas", 80, 5, "veg", "vegetable", (12, 1, 2)),
    Food("carrot", 40, 1, "veg", "vegetable", (11, 12, 1, 2)),
    Food("bottle gourd", 15, 0.6, "veg", "vegetable", (4, 5, 6, 7, 8)),
    Food("okra", 33, 2, "veg", "vegetable", (5, 6, 7, 8, 9)),
    Food("pumpkin", 26, 1, "veg", "vegetable", (8, 9, 10, 11)),
    Food("tomato", 20, 1, "veg", "vegetable"),
    Food("beans", 30, 2, "veg", "vegetable", (9, 10, 11, 12, 1)),
]

ALLOWED = {"veg": {"veg"}, "egg": {"veg", "egg"}, "nonveg": {"veg", "egg", "nonveg"}}


class FoodSource(Protocol):
    def all(self) -> list[Food]: ...


class BuiltinFoods:
    def all(self) -> list[Food]:
        return list(FOODS)
