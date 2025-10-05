## Umamusume game mechanics

The game is a rogue-like, before the start of a racing career (a run) the player picks 6 support cards which have varying stats and a trainee (a character). Each character has 5 stat values: Speed, Stamina, Power, Guts and Wit. They start low and the objective is to increased to meet whatever requirements the player thinks must be met to win races. The trainee can also accumulate skill points during a career: they are used to buy skills that help the runner win races.

Every turn the player is presented with a few options:
- Use Speed training facility
- Use Stamina training facility
- Use Power training facility
- Use Guts training facility
- Use Wit training facility
- Resting
- Recreation
- Infirmary
- Run an optional race

Using a training facility costs Energy and provides stats relative to that training facility and increase the level of the training facility. Each training facility provides the following stats:
- Speed training facility consumes Energy and gives Speed and some Power
- Stamina training facility consumes Energy and gives Stamina and some Guts
- Power training facility consumes Energy and gives Power and some Stamina
- Guts training facility consumes Energy and gives Guts, some Speed and some Power
- Wit training facility recovers a little Energy and gives Wit and Skill points

In addition, all training facilities give skill points, with the Wit training facility granting more than the others. Resting recovers Energy, Recreation improves mood, Infirmary cures negative statuses, running a race provides random stats and many Skill points.

The way the support cards come into play is that each turn, cards are randomly distributed across the 5 training facilities or don't appear at all. The distribution is weighted by each card's **specialty_priority** effect.

**Formula:**
- Total weight = `500 + specialty_priority + 50`
- Preferred facility chance = `(100 + specialty_priority) / total_weight`
- Each non-preferred facility chance = `100 / total_weight`  
- Non-appearance chance = `50 / total_weight`

**Examples:**
- At specialty_priority = 0: All facilities equal at ~18%, ~9% no show
- At specialty_priority = 30: Preferred ~22%, others ~17% each, ~9% no show
- At specialty_priority = 100: Preferred ~31%, others ~15% each, ~8% no show

**Special case:** Pal (Friend) cards have no preferred facility, so all 5 facilities receive base weight (100 each).

The stat gain from using a training facility is improved by which and how many cards landed on it. Notably, if a card of type Speed lands on the Speed training facility (its preferred facility), the amount of Speed and Power gained is strongly improved. The exact amount of stats gained however can only be calculated when taking into account the numerous effects the each card has.

Cards can go from level 1 to level 50 if they are of SSR rarity, to level 45 if of SR rarity and to level 40 if they are of R rarity. The Limit Break values (LB for short) refers to the possibility of upgrading the level of the card, in this way:

- R rarity card:
  - LB0 -> max_level = 20
  - LB1 -> max_level = 25
  - LB2 -> max_level = 30
  - LB3 -> max_level = 35
  - LB4 -> max_level = 40

- SR rarity card:
  - LB0 -> max_level = 25
  - LB1 -> max_level = 30
  - LB2 -> max_level = 35
  - LB3 -> max_level = 40
  - LB4 -> max_level = 45

- SSR rarity card:
  - LB0 -> max_level = 30
  - LB1 -> max_level = 35
  - LB2 -> max_level = 40
  - LB3 -> max_level = 45
  - LB4 -> max_level = 50
  
LB4 is sometimes referred to as MLB (short for Maximum Limit Break). The limit break is the most important value for players, rather than level, because leveling a card is trivial and as such the limit break is the actual indicator of the maximum level currently achievable by the card, and the level of the card determines its effectiveness.

Card effects are identified in the scraped Gametora JSON by type (a number): they can be normal effects or unique effects. All cards (R, SR and SSR) can have normal effects, only SSR cards can have one or more unique effects. The effects currently in the game are:
- Normal effect types: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 25, 26, 27, 28, 30, 31, 32]
- Unique effect types: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 27, 28, 30, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122]

Normal effects and Unique effects can look similar. For example, the card **Vodka Power SSR** (`30005-vodka` in `src/data/cards.json`) has the following effects (among others):
- unique effect of type 1: Increases the effectiveness of Friendship Training (10%)
- unique effect of type 19: Increases the frequency at which the character participates in their preferred training type (20)
- normal effect of type 1: Increases the effectiveness of Friendship Training (35% at max level 50)
- normal effect of type 19: Increases the frequency at which the character participates in their preferred training type (65 at max level 50)

When calculating the total effect of the type 1 effects, the two values are multiplied: 

Also, each character has a bonus to the growth rate of 1 or more stats. For example a character with 20% Stamina bonus will gain 20% more Stamina whenever it's gained via training (so from the Stamina training facility and the Power training facility). The final value of the calculation is rounded down.

Each career has a limited amount of turns and many of them will be spent on resting and racing. Resting is particularly important because as Energy gets low the risk of failure from using any of training facility increases. Failing a training in any non-Wit training can lead to injury which then requires wasting turns in Recreation and Infirmary which can ruin a career. Each training facility also has a level, from 1 to 5, higher level facilities provide higher gains.

On top of all this, each career is set in a Scenario which the player can choose. Each scenario changes the stat gain for each training facility and the cap for each stat. It also adds extra mechanics which are simply too complicated to even take in consideration and it would be unnecessary anyway. Currently, the game only has one scenario, with its second coming soon, they are quite different but ultimately what is of interest for this application is how the scenario affect the level of the training facilities. The current and only scenario is called "URA Finals" and its mechanics are: every 4 times a facility is used it goes up a level, so it starts at level 1 and after 4 uses it goes to level 2, to reach level 5 you would need 16 uses. The level of the facilities influences the stat gain significantly. The stat gain values for each facility at every level from each scenario can be found in `src/data/scenarios.json`.

Another mechanic that should be considered is the Fan club. The trainee gains fans as she participates in races with the placing determining the amount gained. The Fan count is relevant for this application because some cards provide dynamic effects like "Increased training effectiveness per N fans".

Here's an example of how a stat gain would be calculated. Note that I'm calculating total Power gain from the Power facility in this example, `power_bonus` applies because the Power facility provides Power but a card with `power_bonus` landing on the Speed facility would still apply this bonus because the Speed facility also provides some amount of Power. The current mood can provide -20%, -10%, 0%, 10% or 20% bonus.
```
base_stat_gain = (base_facility_gain + power_bonus[card0] + ...)
friendship_multiplier = (((100% + friendship_bonus[card0]) * (100% + friendship_bonus[card1]) * ...)) / 100%
mood_multiplier = (100% + (current_mood_bonus * (100% + mood_effect[card0] + mood_effect[card1] + ...))) / 100%
training_effectiveness_multiplier = (100% + training_effectiveness[card0] + training_effectiveness[card1] + ...) / 100%
support_multiplier = (100% + 5% * number_of_support_cards_on_facility ) / 100%
trainee_multiplier = (100% + trainee_power_growth) / 100%

final_power_gain = base_stat_gain * friendship_multiplier * mood_multiplier * training_effectiveness_multiplier * support_multiplier * trainee_multiplier
```

`final_power_gain` is then rounded down to an integer. Note that the `friendship_multiplier` value of a card is only taken into account if the type of the card matches the type of facility, in this case I'm assuming `card0` and `card1` are Power cards.

There are many more mechanics but this should suffice to create a context for the implementation of all application features.
