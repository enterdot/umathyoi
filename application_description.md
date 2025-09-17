## Application Description

An application written in Python using GTK4/libadwaita widgets. It's designed using an observer model. The application state is kept in the modules classes and the ui in the widgets classes.
It has two separate function (more could be added) in two distinct views selectable in the title bar.

**Legacy Manager**: not implemented (just a placeholder)

**Deck Builder**: work in progress. When completed it should work as follows:

1. The user select a card which is added to the currently active deck

2. As cards are added and removed to the active deck an efficiency score for the deck is automatically updated.

3. The user can change the active deck by scrolling a carousel. Each page of the carousel contains a deck.

4. The number of decks is fixed. So is the number of cards in a deck.

5. The sidebar contains a list of all cards available, when added to the active deck they are made invisible to indicate they've been added.

6. Search and filter card to more easily add them to the deck.

7. All the decks in the deck carousel are serialized and saved to disk when the application exits and loaded the next time.

8. A button on the left of the header bar appears when the view is collapsed and only the carousel is visible, so the user can switch to the card selection sidebar and still add cards

The entire project should follow a consistent style for the naming of methods, variables and classes. The style should be Pythonic and use modern Python (3.13, or 3.10+ at worst) features and style.

The application is developed in a Linux environment (ArchLinux).
