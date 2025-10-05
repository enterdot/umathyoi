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
- Deck Efficiency Calculation - Display the data, core application feature
- Data Persistence - Save/load decks and card ownership via `dconf`
- Card Inspector - Detailed card information view activated from info button on action rows
- Search/Filter System - Essential for browsing hundreds of cards
- Responsive Header Button - Show the sidebar when collaped, critical for mobile/narrow screen usability
- Consistent Errors - Use `errno` module and `strerror` from `os` module for consistent error messages

