## Architecture Overview

**Application:** GTK4/Libadwaita deck building application for Uma Musume card game support cards

**Architecture Pattern:** Event-driven MVC with reactive UI updates
- **Flow:** User Interaction → Module State Change → Event Trigger → Widget Updates
- **Example:** Button click → `deck.add_card()` → `deck.card_added` event → Button grays out

**Key Components:**

1. **Data Layer:**
   - `Card`: Individual card with stats per limit break level
   - `Deck`: Collection of 6 cards with limit break levels
   - `DeckList`: Container of 5 decks with active deck tracking
   - `CardInspector`: Currently inspected card state for info view
   - `Event`: Custom event system for loose coupling
   - **Databases:**: For managing data extracted from JSON files
   - ... and more, all located in `src/modules`

2. **UI Layer:**
   - **Views:** High-level page containers (DeckBuilder, LegacyManager, etc.)
   - **Widgets:** Reusable components (CardArtwork, CardSlot, CardSelection, etc.)
   - **Windows:** Main application window with responsive breakpoints

**TODOs:**
1. `deck_carousel.py` to multiple files - Split content view, deck carousel, turn settings and plots (right sidebar)
2. Deck efficiency calculation - Display the data, core application feature
3. Data persistence - Save/load decks and card ownership via `dconf`
4. Card Inspector - Detailed card information view activated from info button on action rows
5. Search/Filter system - Essential for browsing hundreds of cards
6. Responsive Header Button - Show the sidebar when collaped, critical for mobile/narrow screen usability
7. Consistent Errors - Use `errno` module and `strerror` from `os` module for consistent error messages
8. Complete the remaining `TODO`s left in the code

