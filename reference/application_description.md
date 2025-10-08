## Application Description

An application written in Python using GTK4/libadwaita widgets. It's designed using an observer model. The application state is kept in the modules classes and the ui in the widgets classes. It has separate functions in distinct views from the `views` module and selectable in the title bar:

- Deck Builder: build deck to evaluate their effectiveness, work in progress
- Legacy Manager: not implemented
- Banner Planner: not implemented
- Pull Chance: A simple binomial distribution probability calculator, not implemented
- Race Simulator: not implemented

---

### Deck Builder

1. The sidebar contains a list of all cards available
2. An info button can be used to inspect a card in more detail from the sidebar
3. In the card inspection panel, the user can set the card as owned at a particular limit break
4. Search and filter cards by fuzzy name search, type, rarity and owned state
5. On the right is the deck display view with a deck carousel, turn settings and plots on the right
6. The user can select a card which is added to the currently active deck
7. The active deck is the one currently showing in the carousel
8. The user can change the parameters for a typical turn via settings under the deck carousel
8. As cards are added and removed and turn settings are changed a debounced calculation is triggered
10. The number of decks is fixed and so is the number of cards in a deck.
11. All the decks and card ownership states are saved via `dconf` at exit
12. A button on the left of the header bar appears when the view is collapsed so the user can switch to the card selection

---

### Legacy Manager

1. To be defined

---

### Banner Planner

1. To be defined

---

### Pull Chance

1. The user selects a number of trials (pulls) and a probability value from a set of predefined values
2. The values are: 0.5%, 0.75%, 3%, 12.5%
3. An histogram show the chances to get 0, 1+, 2+, 3+, 4+, 5+ successes

---

### Race Simulator

1. To be defined, but the repository found at https://github.com/alpha123/uma-skill-tools can be refrenced
2. The main function is to show the endurance (HP) consumption
3. It should also provide a list of the best 10 skills to reduce time taken to complete the track
