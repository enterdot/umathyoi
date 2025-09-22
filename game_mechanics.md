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

Another mechanic that should be considered is the Fan club. The trainee gains fans as she participates in races with the placing determining the amount gained. The Fan count is relevant for this application because some cards provide exotic effects like "Increased training effectiveness per N fans".

There are many more mechanics but this should suffice to create a context for the implementation of all application features.
