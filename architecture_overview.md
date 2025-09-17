## Architecture Overview

**Application:** GTK4/Libadwaita deck building application for Uma Musume card game support cards

**Architecture Pattern:** Event-driven MVC with reactive UI updates
- **Flow:** User Interaction → Module State Change → Event Trigger → Widget Updates
- **Example:** Button click → `deck.add_card()` → `deck.card_added` event → Button grays out
- **Flexibility:** Pattern can be broken for simpler code when it makes sense

**Key Components:**

1. **Data Layer (modules/):**
   - `Card`: Individual card with stats per limit break level
   - `Deck`: Collection of 6 cards with limit break levels
   - `DeckList`: Container of 5 decks with active deck tracking
   - `CardDatabase`: Card data management with async image loading
   - `CardStats`: Currently inspected card state for info view
   - `Event`: Custom event system for loose coupling

2. **UI Layer:**
   - **Views:** High-level page containers (DeckBuilder, LegacyManager)
   - **Widgets:** Reusable components (CardArtwork, CardSlot, CardSelection, etc.)
   - **Windows:** Main application window with responsive breakpoints

3. **Navigation:**
   - Main app has ViewStack with DeckBuilder/LegacyManager tabs
   - DeckBuilder has NavigationSplitView: CardSelection sidebar + DeckCarousel content
   - CardSelection has ViewStack: card list ↔ card stats info view

**Data Flow Examples:**
- Card selection → deck updates → carousel refreshes
- Deck switching → sidebar updates card visibility
- Info button → CardStats updates → stats view shows details

**Current State:**
- Core architecture implemented
- Basic UI structure complete
- Image loading working
- Event system in place
- Logging system in place
- Type hints everywhere

**TODOs:**
- Add deck efficency calculation and display (currently a placeholder). This should be done asynchronously because the calculation is not smart, it's brute-forced via continuous iterations until it converges.
- Data persistence: serialize decks to save and load them
- Stats display
- Add button to the header bar when the view is collapsed and only the carousel is visible, otherwise the user is not able to add cards anymore
- Stats display: utilize CardStats class which holds information on the currently inspected card. It is used by the secondary view in the sidebar of the Deck Builder. It gets activated when clicking the info button on one of the action rows
- Maybe add the info button also on the cards added to decks in the carousel
- There needs to be a way to filter cards in the selection list sidebar because eventually there'll be hundreds of cards. This might be achieved via filter buttons but I would prefer a fuzzy search solution with a search box in a Revealer widget controlled by a search button.

**Development Questions:**
- Data serialization strategy needed, what options are there? Preferably built-in in Python library.
- Drag and drop to move a card already in the deck to different slot should be considered. How hard would it be to implement?
