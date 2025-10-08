## Application Description

A Python GTK4/Libadwaita application for Uma Musume support card deck building. Uses an event-driven observer pattern where application state is kept in module classes and UI in widget classes. Separate functions are provided through distinct views selectable from the title bar.

---

### Views

#### Deck Builder
**Status:** Work in progress - core functionality implemented, refinements needed

**Layout:**
- **Left sidebar:** Card selection with search/filter
- **Center:** Deck carousel showing multiple decks (3×2 card grid per deck)
- **Bottom center:** Turn settings for efficiency calculator
- **Right:** Efficiency plots showing stat gain distributions

**Features Implemented:**
1. ✅ Card list sidebar with all available cards
2. ✅ Info button to inspect cards in detail (view planned, not implemented)
3. ✅ Add cards to active deck by clicking in sidebar
4. ✅ Remove cards by clicking them in carousel
5. ✅ Navigate between 5 decks via carousel
6. ✅ Adjust limit breaks per card (0-4 via slider)
7. ✅ Mute/unmute cards in deck (toggle via button)
8. ✅ Turn settings: facility levels, energy, mood, fan count
9. ✅ Debounced efficiency calculation on changes (150ms)
10. ✅ Violin plots showing stat gain distributions per facility

**Features In Progress:**
- Search and filter by name (fuzzy), type, rarity, ownership
- Card inspector view with detailed stats at all limit breaks
- Responsive header button (show sidebar when collapsed)
- Card ownership state tracking (owned at which limit breaks)
- Data persistence via `dconf`

**Known Issues:**
- Poor layout of turn settings and violin plots, both take too much space
- Muted card is removed from the active deck rather than being muted
- Carousel hints not showing correctly (could be removed to simplify)
- Missing Scenario selection and Character selection in turn settings
- Cards can be added to deck when they are of the same character
- Adding the `stopwatch` decorator to the efficiency recalculation function breaks it

---

#### Legacy Manager
**Status:** Not implemented

**Purpose:** To be defined

---

#### Banner Planner
**Status:** Not implemented

**Purpose:** To be defined

---

#### Pull Chance
**Status:** Not implemented

**Purpose:** Simple binomial distribution probability calculator

**Planned Features:**
1. User selects number of trials (pulls)
2. User selects probability from predefined values (0.5%, 0.75%, 3%, 2.25%, 3.75%, 12.5%)
3. Histogram shows chances to get 0, 1+, 2+, 3+, 4+, 5+ successes

---

#### Race Simulator
**Status:** Not implemented

**Purpose:** Simulate race performance and stamina consumption

**Planned Features:**
1. Show endurance (HP) consumption during race
2. Provide list of top 10 skills that reduce race completion time
3. Reference implementation: https://github.com/alpha123/uma-skill-tools

---

### Application Flow at current state of develpment

#### Startup
1. Load card database from `data/cards.json` (with async image loading)
2. Load scenario database from `data/scenarios.json`
5. Create test decks with sample cards (for development)
6. Initialize main window with view stack
7. Set up event subscriptions
8. Present window

#### Card Selection
1. User clicks card in sidebar
2. Card is added to active deck at first empty slot
3. `deck.card_added` event triggers
4. Sidebar updates (card gets "in deck" styling)
5. Carousel updates (card appears in slot)
6. Efficiency calculator recalculates (after debounce)

#### Card Removal
1. User clicks card in carousel
2. Card is removed from that slot
3. `deck.card_removed` event triggers
4. Sidebar updates (card styling reverts)
5. Carousel updates (slot shows empty state)
6. Efficiency calculator recalculates (after debounce)

#### Limit Break Adjustment
1. User drags slider in card slot
2. Limit break value updates for that slot
3. `deck.limit_break_changed` event triggers
4. Card artwork updates if needed
5. Efficiency calculator recalculates (after debounce)

#### Deck Navigation
1. User swipes carousel or clicks navigation hints
2. Carousel animates to new deck
3. Active deck index updates
4. `deck_list.slot_activated` event triggers
5. All UI components update to reflect new active deck
6. Efficiency calculator recalculates for new deck

#### Efficiency Calculation
1. User changes settings (energy, facility levels, etc.)
2. Debounce timer starts (cancels if more changes)
3. Timer expires, calculation begins
4. `calculator.calculation_started` event fires
5. Progress events fire every 1% (for progress indicator)
6. Monte Carlo simulation runs (default 1000 turns):
   - Distribute cards randomly across facilities
   - Calculate stat gains per facility per turn
   - Aggregate results
7. `calculator.calculation_finished` event fires with results
8. Violin plots update to show distributions

---

### Data Management

#### Card Data Structure
Cards are loaded from JSON with:
- Basic info: id, name, rarity, type
- Effects arrays: milestone values at levels 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50
- Unique effects: special effects that unlock at specific levels
- Event skills: skills that can be granted
- Hints: stat bonuses and skill hints

#### Effect Caching
All card effects are pre-calculated at initialization:
- Calculate interpolated values for all levels (1-50)
- Store in LRU cache for fast lookup
- Cache key: (effect_type, level)
- Approximately 50 effects × 50 levels = 2,500 cached values per card

#### Image Loading
Card images are loaded asynchronously:
- Images fetched from Gametora CDN
- Cached locally after first load
- Loading states: empty → spinner → image/error
- No blocking of UI thread

---

### Responsive Design

**Breakpoints:**
- Wide mode: Sidebar + content side-by-side
- Narrow mode: Sidebar overlays content, collapsible

**Adaptations:**
- Carousel spacing adjusts based on window width
- Card slot sizes remain constant (150×200px)
- View switcher in title bar adapts to width
- Navigation split view handles sidebar collapse

---

### Styling

**Theme:** Follows libadwaita styling with custom CSS for:
- Carousel animations (scaling and opacity during transitions)
- Empty card slots (dashed border, subdued color)
- Error card slots (error color border and background)
- Cards in deck (reduced opacity when visible in sidebar)
- Muted cards (further reduced opacity)

**Animations:**
- Carousel transitions: 200ms reveal duration
- Card scaling: 85% when not active, 100% when active
- Smooth CSS transitions with easing

---

### Future Enhancements

**Usability:**
- Remember limit break of cards removed from deck to re-add them at same level
- Add a button next to the limit break slider to reset the card at owned limit break (if available)

**Data Persistence:**
- Save deck configurations on exit
- Save card ownership states
- Load on startup
- Use `dconf` for storage

**Search/Filter:**
- Fuzzy name search
- Filter by type (Speed, Stamina, Power, Guts, Wit, Pal)
- Filter by rarity (R, SR, SSR)
- Filter by ownership state (owned/not owned, limit break level)
- Combine filters (AND logic)

**Card View:**
- Detailed view showing all effects at all limit breaks
- Skill information
- Button to set the owned limit break and to add the card at selected limit break

**Mobile Support:**
- Further responsive improvements
- Touch-friendly controls
- Portrait mode optimization
