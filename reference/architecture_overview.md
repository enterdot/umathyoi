## Architecture Overview

**Application:** GTK4/Libadwaita deck building application for Uma Musume card game support cards

**Architecture Pattern:** Event-driven MVC with reactive UI updates
- **Flow:** User Interaction → Module State Change → Event Trigger → Widget Updates
- **Example:** Button click → `deck.add_card()` → `deck.card_added` event → Button grays out

---

### Key Components

#### 1. Data Layer (`src/modules/`)

**Core Classes:**
- `Card`: Individual card with effects per level, uses interpolation for level-based effects
- `Deck`: Collection of up to 6 cards with limit break levels per slot
- `DeckList`: Container of 5 decks with active deck tracking
- `CardInspector`: Currently inspected card state for info view
- `Event`: Custom event system for loose coupling between modules and UI
- `EfficiencyCalculator`: Monte Carlo simulation engine for deck analysis

**Database Classes:**
- `CardDatabase`: Manages card data and async image loading with caching
- `ScenarioDatabase`: Loads scenario data (facility stat gains per level)
- (Future: `CharacterDatabase`, `SkillDatabase`)

**Supporting Classes:**
- `Scenario`: Contains facility configurations and stat gain values
- `Facility`: Individual training facility with level-based gains
- `GenericCharacter`: Character with stat growth bonuses
- Enums: `CardRarity`, `CardType`, `CardEffect`, `CardUniqueEffect`, `FacilityType`, `StatType`, `Mood`

#### 2. UI Layer

**Views (`src/views/`):**
High-level page containers selectable from title bar:
- `DeckBuilder`: Main working view with sidebar and carousel
- `LegacyManager`: (Not implemented)
- `BannerPlanner`: (Not implemented)
- `PullChance`: Binomial probability calculator (not implemented)
- `RaceSimulator`: (Not implemented)

**Widgets (`src/widgets/`):**
Reusable components:
- `CardSelection`: Sidebar with card list and search/filter
- `CardArtwork`: Displays card images with loading/error states
- `CardSlot`: Individual card slot in deck with limit break selector
- `DeckCarousel`: Carousel showing multiple decks with animations
- `DeckInspector`: Container for carousel, settings, and plots
- `TurnSettings`: Configuration for efficiency calculator
- `EfficiencyPlots`: Violin plots showing stat gain distributions

**Windows (`src/windows/`):**
- `MainWindow`: Main application window with responsive breakpoints and view stack

---

### Efficiency Calculator System

**Purpose:** Simulates thousands of training turns to calculate expected stat gains and skill points from a deck configuration.

**Key Features:**
- Monte Carlo simulation (default 1000 turns)
- Debounced recalculation (150ms wait) to prevent UI lag
- Progressive calculation with progress events
- Pre-calculated static effects for performance
- Card appearance probability based on specialty_priority
- All game mechanics: friendship multipliers, mood effects, training effectiveness, support bonuses, character growth

**Performance Characteristics:**
- ~220ms for 10,000 turns (after optimization from initial 1,700ms)
- 87% performance improvement achieved through:
  - Caching card effects and stat bonuses
  - Pre-calculating static effects (normal + unique static)
  - Optimizing random selection with cumulative probability distributions
  - Flattening nested data structures for hot loops

**Architecture:**
See `docs/efficiency_calculator_architecture.txt` for detailed flow diagrams and implementation details.

---

### Event System

**Pattern:** Observer pattern for loose coupling
- Modules expose `Event` instances (e.g., `deck.card_added`)
- Widgets subscribe to events: `deck.card_added.subscribe(self._on_card_added)`
- State changes trigger events: `self.card_added.trigger(self, card=card, slot=slot)`
- Events carry relevant data via kwargs

**Benefits:**
- Modules don't need to know about UI
- UI updates automatically when data changes
- Easy to add new UI components without modifying modules
- Clear separation of concerns

---

### Card Effect System

**Three Types of Effects:**

1. **Normal Static Effects** (CardEffect enum)
   - Always active, scale with card level
   - Examples: friendship_effectiveness, speed_stat_bonus, training_effectiveness
   - Stored in interpolated milestone format

2. **Unique Static Effects** (CardUniqueEffect enum < 100)
   - Special card-specific effects that unlock at a specific level
   - Behave like normal effects but with threshold
   - Examples: effect_bonus_if_min_bond, extra_appearance_if_min_bond

3. **Dynamic Unique Effects** (CardUniqueEffect enum >= 100)
   - Require turn-by-turn calculation based on game state
   - 22 types total (see `src/modules/efficiency_calculator.py` for commented implementation)
   - Examples: training_effectiveness_for_fans, effect_bonus_per_card_on_facility
   - ~20% performance cost but necessary for accuracy

**Effect Combination Rules:**
- Most effects are additive: normal static + unique static + dynamic unique
- **Exception - Friendship:** Unique (static + dynamic) is multiplicative with normal
  - Formula: `(1 + unique_friendship/100) × (1 + normal_friendship/100)`

---

### Data Persistence

**Current State:** Not yet implemented

**Planned:** Use `dconf` for:
- Deck configurations (cards and limit breaks per deck)
- Card ownership states (which cards owned at which limit breaks)
- User preferences
- Last used scenarios and characters

---

### TODOs

**High Priority:**
1. Refine Deck Builder UI - Fix bugs with muted cards and carousel hints not showing
2. Data persistence - Save/load decks and card ownership via `dconf`
3. Search/Filter system - Essential for browsing hundreds of cards (fuzzy search)
4. Responsive Header Button - Show sidebar when collapsed, critical for mobile/narrow screens

**Medium Priority:**
5. Card View - Detailed card information view activated from info button
6. Consistent Errors - Use `errno` module and `os.strerror()` for consistent error messages
7. Complete remaining `TODO`s in codebase

**Low Priority:**
8. Implement other views (Legacy Manager, Banner Planner, Pull Chance, Race Simulator)

---

### Development Guidelines

**Code Style:**
- Modern Python 3.13+ features
- Type hints everywhere: `Type | None` not `Optional[Type]`
- snake_case for enums, UPPER_CASE for constants
- Relative imports within packages: `from .foo import bar`
- Fail early for programmer errors: `raise ValueError()`
- Recover only from bad user input or failed resource loading
- Short docstrings - type hints provide parameter/return info
- Less code is better

**Error Handling:**
- Use descriptive error messages
- Log errors with appropriate level (debug, info, warning, error)
- Prefer returning None over raising exceptions for expected failures
- Use ValueError for programmer errors, handle IOError for file operations

**Performance Considerations:**
- Pre-calculate what you can (static effects, probability distributions)
- Use caching for expensive operations (LRU cache for card effects)
- Debounce user input that triggers heavy calculations (150ms sweet spot)
- Profile before optimizing - measure don't guess
