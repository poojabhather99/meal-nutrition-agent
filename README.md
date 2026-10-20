# meal-nutrition-agent

[![CI](https://github.com/poojabhather99/meal-nutrition-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/poojabhather99/meal-nutrition-agent/actions/workflows/ci.yml)

**Live demo (runs in your browser):** https://poojabhather99.github.io/meal-nutrition-agent/

A single-user meal planning agent in the shape of a "nutritionist friend": you tell it about yourself in plain language, it keeps a small evolving profile, plans the week around a protein target, and reminds you the evening before what to prepare or order.

The planner, profile parser, reminders and command router are plain Python with no dependencies, so the whole thing is testable without a Telegram token, an LLM or a network. A Telegram adapter only needs to call `Bot.handle(chat_id, text)` and send back the string.

## What it does

- **Profile from free text.** "I am eggetarian, 62 kg, want to build muscle, I hate okra" sets diet (veg, eggetarian, non-veg), weight, goal and dislikes. Implausible weights are ignored.
- **Weekly plan.** Three meals a day. Protein is split across meals to hit a daily target (1.2 g/kg to maintain, 1.4 to lose, 1.6 to gain), grain portions are sized toward a calorie share, vegetables are limited to those in season for the current month, and diet and dislikes are always respected.
- **Day-ahead reminders.** `reminder_for` names tomorrow's meals; Sunday is the planning day.
- **Shopping list** totals grams per food across the week.
- **Commands:** `/plan`, `/today`, `/remind`, `/shopping`, `/profile`, `/help`. Changing the profile invalidates the old plan.

## Run

```bash
pip install -e ".[dev]"
pytest -q            # 21 tests
python - <<'PY'
from mealagent.bot import Bot
bot = Bot()
print(bot.handle(1, "I am vegetarian, 60 kg, want to lose weight"))
print(bot.handle(1, "/plan"))
PY
```

## Honest limits

- **Nutrition numbers are approximate and hand-entered.** The 21-food table in `foods.py` holds rough per-100 g figures for planning. It is not USDA FoodData Central data. `FoodSource` is the seam for a real FoodData Central client, which is the first thing to add.
- **Not medical or dietetic advice.** The targets are generic rules of thumb (protein per kg, 30 kcal/kg base) and the bot says so on every plan. It does not handle medical conditions, allergies or portion safety.
- **Calories land within about 30% of target, not on it.** Portion sizes are capped (grain 80 to 350 g), so low-calorie vegetarian plans can fall short of the target.
- **Meal suitability is minimal.** Only oats are treated as a breakfast food; other proteins can land at any meal, so you may get chicken at breakfast.
- **Rule-based, not an LLM.** The profile parser uses regular expressions, so it understands a fixed set of phrasings. There is no LLM, no minute-by-minute recipe generation and no Telegram adapter in this repo yet; the router is the part those would plug into.
- Sessions are in memory and single-process.
