## Umamusume Game Mechanics

The game is a rogue-like. Before starting a racing career (a run), the player picks 6 support cards and a trainee (a character).

Cards can be of 6 types Speed, Stamina, Power, Guts, Wit and Pal. There is also the Group type but it can be considered equivalent to the Pal type for most cases. Every support card is associated with a character: a character could have more than one card but only one can be used in the same deck. For example, the character Special Week has a SSR Speed support card and a SSR Guts support card, only one can be used in the same deck. Additionally, support cards of one character can not be used if that trainee is that character. For example, if the trainee is Special Week, neither of the support cards previously mentioned can be used.

Each character has 5 stat values: Speed, Stamina, Power, Guts and Wit. They start low and the objective is to increase them to meet requirements for winning races. The trainee can also accumulate skill points during a career, used to buy skills that help win races.

Every turn the player is presented with options:
- Use Speed training facility
- Use Stamina training facility
- Use Power training facility
- Use Guts training facility
- Use Wit training facility
- Resting
- Recreation
- Infirmary
- Run an optional race

Using a training facility costs Energy and provides stats relative to that facility. Each training facility provides:
- Speed: Speed + some Power + someSkill points
- Stamina: Stamina + some Guts + some Skill points
- Power: Power + some Stamina + some Skill points
- Guts: Guts + some Speed + some Power + some Skill points
- Wit: Wit + Skill points (recovers a little Energy)

Resting recovers Energy, Recreation improves mood, Infirmary cures negative statuses, running a race provides random stats and many Skill points.

### Card Distribution Mechanics

Each turn, cards are randomly distributed across the 5 training facilities or don't appear at all. The distribution is weighted by each card's **specialty_priority** effect.

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

The stat gain from using a training facility is improved by which and how many cards landed on it. Notably, if a card of matching type lands on its preferred facility (e.g., Speed card on Speed facility), the gains are strongly improved. The exact amount of stats gained can only be calculated when taking into account the numerous effects each card has.

### Card Levels and Effects

Cards can go from level 1 to:
- R rarity: level 40 maximum
- SR rarity: level 45 maximum
- SSR rarity: level 50 maximum

**Effect Interpolation System:**

Card effects are stored as milestone values at specific levels (1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50). For levels between milestones, values are linearly interpolated. In the data format:
- `-1` means "no milestone at this level, use interpolation"
- Any other value is a milestone value at that level

Example from data:
```
[14, 10, -1, -1, -1, -1, -1, 25, -1, -1, -1, 30]
```
This represents friendship_effectiveness:
- Level 1: 10%
- Levels 2-29: interpolated between 10% and 25%
- Level 30: 25%
- Levels 31-49: interpolated between 25% and 30%
- Level 50: 30%

### Stat Gain Calculation

Here's an example calculating total Power gain from the Power facility. Note that `power_bonus` applies because the Power facility provides Power, but a card with `power_bonus` landing on the Speed facility would still apply this bonus since Speed facility also provides some Power. Current mood can provide -20%, -10%, 0%, 10% or 20% bonus.

```
base_stat_gain = (base_facility_gain + power_bonus[card0] + ...)
friendship_multiplier = (((100% + friendship_bonus[card0]) * (100% + friendship_bonus[card1]) * ...)) / 100%
mood_multiplier = (100% + (current_mood_bonus * (100% + mood_effect[card0] + mood_effect[card1] + ...))) / 100%
training_effectiveness_multiplier = (100% + training_effectiveness[card0] + training_effectiveness[card1] + ...) / 100%
support_multiplier = (100% + 5% * number_of_support_cards_on_facility) / 100%
trainee_multiplier = (100% + trainee_power_growth) / 100%

final_power_gain = base_stat_gain * friendship_multiplier * mood_multiplier * training_effectiveness_multiplier * support_multiplier * trainee_multiplier
```

`final_power_gain` is then rounded down to an integer. Note that the `friendship_multiplier` value of a card is only taken into account if the type of the card matches the type of facility (e.g., both cards are Power cards for a Power facility).

**Special Case - Friendship Bonus:**
Unlike other effects that are additive, friendship bonuses are multiplicative:
- Normal static friendship + unique static friendship are additive within their categories
- But unique friendship (static + dynamic) is multiplicative with normal friendship
- Formula: `(1 + unique_friendship/100) × (1 + normal_friendship/100)`

### Character Growth Bonuses

Each character has individual growth bonuses for each stat (typically 0-20%). For example, a character with 20% Stamina bonus will gain 20% more Stamina whenever it's gained via training (i.e. from Stamina and Power training facilities). The final value of the calculation is rounded down.

### Career Constraints

Each career has a limited number of turns. Many turns are spent on resting and racing. Resting is particularly important because as Energy gets low, the risk of failure from any training facility increases. Failing a training in any non-Wit training can lead to injury, requiring wasted turns in Recreation and Infirmary, which can ruin a career. Each training facility also has a level from 1 to 5; higher level facilities provide higher gains.

### Scenarios

Each career is set in a Scenario which the player can choose. Each scenario changes the stat gain for each training facility and the cap for each stat. It also adds extra mechanics which are too complicated to consider for this application.

Currently, the game only has one scenario called "URA Finals". Its mechanics: every 4 times a facility is used it goes up a level. It starts at level 1 and after 4 uses goes to level 2. To reach level 5 requires 16 uses. The level of the facilities influences stat gain significantly. The stat gain values for each facility at every level from each scenario can be found in `src/data/scenarios.json`.

### Fan Club

The trainee gains fans as she participates in races, with placing determining the amount gained. The Fan count is relevant for this application because some cards provide dynamic effects like "Increased training effectiveness per N fans".
