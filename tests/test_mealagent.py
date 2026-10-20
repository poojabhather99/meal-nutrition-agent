from datetime import date

import pytest

from mealagent.bot import Bot
from mealagent.foods import ALLOWED, FOODS
from mealagent.planner import DAYS, plan_week, shopping_list
from mealagent.profile import Profile, update_profile
from mealagent.reminders import is_planning_day, reminder_for


def test_profile_parsing():
    p = Profile()
    ch = update_profile(p, "I am eggetarian, weigh 62 kg, want to build muscle, I hate okra")
    assert p.diet == "egg" and p.weight_kg == 62 and p.goal == "gain" and "okra" in p.dislikes
    assert len(ch) >= 4


@pytest.mark.parametrize(
    ("text", "diet"),
    [("I eat chicken", "nonveg"), ("I'm vegetarian", "veg"), ("non-veg please", "nonveg")],
)
def test_diet_detection(text, diet):
    p = Profile()
    update_profile(p, text)
    assert p.diet == diet


def test_implausible_weight_ignored():
    p = Profile()
    update_profile(p, "I am 5 kg")
    assert p.weight_kg is None


def test_targets_scale_with_goal_and_weight():
    lose, gain = Profile(weight_kg=70, goal="lose"), Profile(weight_kg=70, goal="gain")
    assert gain.protein_target_g > lose.protein_target_g
    assert gain.kcal_target > lose.kcal_target


@pytest.mark.parametrize("diet", ["veg", "egg", "nonveg"])
def test_plan_respects_diet(diet):
    week = plan_week(Profile(diet=diet, weight_kg=60), month=1)
    for d in week:
        for items in d.meals.values():
            assert all(i.food.diet in ALLOWED[diet] for i in items)


def test_veg_plan_has_no_egg_or_meat():
    names = {i.food.name for d in plan_week(Profile(), 1) for m in d.meals.values() for i in m}
    assert not names & {"egg", "chicken breast", "fish (rohu)"}


def test_dislikes_excluded():
    p = Profile(weight_kg=60, dislikes={"paneer"})
    names = {i.food.name for d in plan_week(p, 1) for m in d.meals.values() for i in m}
    assert "paneer" not in names


def test_seasonal_vegetables_only():
    for month in (1, 7, 10):
        week = plan_week(Profile(weight_kg=60), month)
        for d in week:
            for items in d.meals.values():
                for i in items:
                    if i.food.kind == "vegetable" and i.food.months:
                        assert month in i.food.months


def test_protein_close_to_target():
    p = Profile(weight_kg=65, goal="gain", diet="nonveg")
    for d in plan_week(p, 1):
        assert 0.8 * p.protein_target_g <= d.protein <= 1.35 * p.protein_target_g
        assert 0.7 * p.kcal_target <= d.kcal <= 1.3 * p.kcal_target


def test_plan_covers_seven_days_and_is_deterministic():
    a, b = plan_week(Profile(), 1), plan_week(Profile(), 1)
    assert [d.day for d in a] == DAYS
    assert [d.protein for d in a] == [d.protein for d in b]


def test_no_eligible_foods_raises():
    p = Profile(dislikes={"paneer", "tofu", "moong dal", "chickpeas", "rajma", "greek yogurt"})
    with pytest.raises(ValueError):
        plan_week(p, 1)


def test_shopping_list_sums_grams():
    week = plan_week(Profile(weight_kg=60), 1)
    assert sum(shopping_list(week).values()) == sum(
        i.grams for d in week for m in d.meals.values() for i in m
    )


def test_reminder_names_tomorrows_meals():
    week = plan_week(Profile(), 1)
    r = reminder_for(week, date(2026, 10, 19))  # Monday -> Tuesday
    assert r.startswith("Tomorrow (Tuesday)") and "lunch:" in r
    assert "Monday" in reminder_for(week, date(2026, 10, 18))  # Sunday -> Monday
    assert is_planning_day(date(2026, 10, 18)) and not is_planning_day(date(2026, 10, 19))


def test_bot_flow():
    bot = Bot(today=lambda: date(2026, 1, 12))
    assert "No plan yet" in bot.handle(1, "/today")
    assert "diet: egg" in bot.handle(1, "I am eggetarian and 60 kg")
    plan = bot.handle(1, "/plan")
    assert "Monday" in plan and "not medical" in plan
    assert "Monday" in bot.handle(1, "/today")
    assert "Tomorrow (Tuesday)" in bot.handle(1, "/remind")
    assert "g" in bot.handle(1, "/shopping")
    assert "60" in bot.handle(1, "/profile")


def test_profile_change_invalidates_plan_and_chats_are_isolated():
    bot = Bot(today=lambda: date(2026, 1, 12))
    bot.handle(1, "/plan")
    bot.handle(1, "I want to gain weight")
    assert "No plan yet" in bot.handle(1, "/today")
    assert "goal: maintain" in bot.handle(2, "/profile")


def test_bot_handles_junk():
    bot = Bot()
    assert "/plan" in bot.handle(1, "")
    assert "didn't pick up" in bot.handle(1, "blah blah")
    assert bot.handle(1, "x" * 5000)


def test_food_table_sane():
    assert len({f.name for f in FOODS}) == len(FOODS)
    assert all(f.protein_g >= 0 and f.kcal > 0 for f in FOODS)
