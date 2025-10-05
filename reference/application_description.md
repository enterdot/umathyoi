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


