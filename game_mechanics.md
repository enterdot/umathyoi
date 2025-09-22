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

Resting recovers Energy, Recreation improves mood, Infirmary cures negative statuses, running a race provides random stats and many Skill points.

The way the support cards come into play is that every turn, each of the 6 cards is randomly placed on one of the training facilities or none at all. The stat gain from using a training facility is improved by which and how many cards landed on it. Notably, if a card of type Speed lands on the Speed training facility, the amount of Speed and Power gained is strongly improved. The exact amount of stats gained however can only be calculated when taking into account the numerous stats the each card has. Also, each character has a bonus to the growth rate of 1 or more stats, for example a character with 20% Stamina bonus will gain 20% more Stamina whenever it's gained via training (so from the Stamina training facility and the Power training facility). The final value of the calculation is rounded down.

Each career has a limited amount of turns and many of them will be spent on resting and racing. Resting is particularly important because as Energy gets low the risk of failure from using any of training facility increases. Failing a training in any non-Wit training can lead to injury which when requires wasting turns in Recreation and Infirmary which can ruin a career. Each training facility also has a level, from 1 to 5, higher level facilities provide higher gains.

On top of all this each career is set in a Scenario which the player can choose. Each scenario changes the stat gain for each training facility and the cap for each stat. It also adds extra mechanics which are simply too complicated to even take in consideration and it would be unnecessary anyway. Currently, the game only has one scenario, with its second coming soon, they are quite different but ultimately what is of interest for this application is how the scenario effects the level of the training facilities. The current and only scenario is called "URA Finals" and its mechanics is simply this: every 4 times a facility is used it goes up a level, so it starts at level 1 and after 4 uses it goes to level 2, to reach level 5 you would need 16 uses. The level of the facilities influences the stat gain significantly.

For reference, the "URA Finals" scenario has the following stat gain values:

Speed facility:
    Level 1: +10 Speed, +5 Power, +2 Skill Points
    Level 2: +11 Speed, +6 Power, +2 Skill Points
    Level 3: +11 Speed, +7 Power, +3 Skill Points
    Level 4: +12 Speed, +7 Power, +3 Skill Points
    Level 5: +13 Speed, +8 Power, +4 Skill Points
Stamina facility:
    Level 1: +9 Stamina, +4 Guts, +2 Skill Points
    Level 2: +10 Stamina, +4 Guts, +2 Skill Points
    Level 3: +11 Stamina, +5 Guts, +3 Skill Points
    Level 4: +11 Stamina, +5 Guts, +3 Skill Points
    Level 5: +12 Stamina, +6 Guts, +4 Skill Points
Power facility:
    Level 1: +5 Stamina, +8 Power, +2 Skill Points
    Level 2: +5 Stamina, +9 Power, +2 Skill Points
    Level 3: +6 Stamina, +9 Power, +3 Skill Points
    Level 4: +6 Stamina, +10 Power, +3 Skill Points
    Level 5: +7 Stamina, +11 Power, +4 Skill Points
Guts facility:
    Level 1: +4 Speed, +4 Power, +8 Guts, +2 Skill Points
    Level 2: +4 Speed, +4 Power, +9 Guts, +2 Skill Points
    Level 3: +5 Speed, +5 Power, +9 Guts, +3 Skill Points
    Level 4: +5 Speed, +5 Power, +10 Guts, +3 Skill Points
    Level 5: +6 Speed, +6 Power, +11 Guts, +4 Skill Points
Wit facility:
    Level 1: +2 Speed, +9 Wit, +4 Skill Points
    Level 2: +3 Speed, +9 Wit, +4 Skill Points
    Level 3: +3 Speed, +10 Wit, +5 Skill Points
    Level 4: +4 Speed, +11 Wit, +6 Skill Points
    Level 5: +4 Speed, +12 Wit, +7 Skill Points

Another mechanic that should be considered is the Fan club. The trainee gains fans as she participates in races with the placing determining the amount gained. The Fan count is relevant for this application because some cards provide exotic effects like "Increased training effectiveness per N fans".

Here's an example of how a stat gain would be calculated. Note that I'm calculating total Power gain from the Power facility in this example, `power_bonus` would be `speed_bonus` for the Speed facility. The current mood can provide -20%, -10%, 0%, 10% or 20% bonus.
```
base_stat_gain = (base_facility_gain + power_bonus[card0] + ...)
friendship_multiplier = (((100% + friendship_bonus[card0]) * (100% + friendship_bonus[card1]) * ...)) / 100%
mood_multiplier = (100% + (current_mood_bonus * (100% + mood_effect[card0] + mood_effect[1] + ...))) / 100%
training_effectiveness_multiplier = (100% + training_effectiveness[card0] + training_effectiveness[card1] + ...) / 100%
support_multiplier = (100% + 5% * number_of_support_cards_on_facility ) / 100%
trainee_multiplier = (100% + trainee_power_growth) / 100%

final_power_gain = base_stat_gain * friendship_multiplier * mood_multiplier * training_effectiveness_multiplier * support_multiplier * trainee_multiplier
```

`final_power_gain` is then rounded down to an integer. Note that the `friendship_multiplier` value of a card is only taken into account if the type of the card matches the type of facility, in this case I'm assuming `card0` and `card1` are Power cards.
Finally, it's possible that future cards could have more conditional effects that might break the rules, for example there might be a card that triggers a friendship training for facilities NOT of its type. I'm just speculating but I want to clarify that our lambda dictionary should be able to accommodate a variety of exotic effects.

There are many more mechanics but this should suffice to create a context for the implementation of all application features.
