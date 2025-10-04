import logging
logger = logging.getLogger(__name__)

from .deck import Deck
from .event import Event
from utils import auto_title_from_instance

class DeckList:
    def __init__(self, decks: list[Deck | None] | None = None) -> None:

        self._size = 5

        logger.info(f"Initializing deck list with {self._size} slots")

        if decks is not None:
            if len(decks) > self._size:
                logger.warning(f"Size is {self._size} but {len(decks)} decks were given, discarding {len(decks) - self._size}")
                decks = decks[:self._size]
            self._decks = [deck if deck is not None else Deck() for deck in decks]

            if len(self._decks) < self._size:
                self._decks.extend([Deck() for _ in range(self._size - len(self._decks))])
        else:
            self._decks = [Deck() for _ in range(self._size)]
        
        for slot, deck in enumerate(self._decks):
            if deck:
                logger.info(f"Slot {slot}: {repr(deck)}")
        
        self._active_slot: int = 0

        # Existing deck list events
        self.slot_activated: Event = Event()
        self.slot_deactivated: Event = Event()
        
        # Active deck events to match all Deck events
        self.card_added_to_active_deck_at_slot: Event = Event()
        self.card_removed_from_active_deck_at_slot: Event = Event()
        self.limit_break_set_for_active_deck_at_slot: Event = Event()
        self.active_deck_was_cleared: Event = Event()
        self.active_deck_pushed_past_capacity: Event = Event()

        # Set up event forwarding for all decks
        self._setup_deck_event_forwarding()
        
        logger.debug(f"{auto_title_from_instance(self)} initialized")

    def _setup_deck_event_forwarding(self):
        """Subscribe to all deck events and forward active deck events."""
        # Mapping of deck events to their corresponding active deck events
        event_mapping = {
            'card_added_at_slot': self.card_added_to_active_deck_at_slot,
            'card_removed_at_slot': self.card_removed_from_active_deck_at_slot,
            'limit_break_set_at_slot': self.limit_break_set_for_active_deck_at_slot,
            'deck_was_cleared': self.active_deck_was_cleared,
            'deck_pushed_past_capacity': self.active_deck_pushed_past_capacity,
        }
        
        # Ensure that we have a mapping for every Deck event
        sample_deck = Deck()
        deck_events = {name for name, attr in vars(sample_deck).items() if isinstance(attr, Event)}
        mapped_events = set(event_mapping.keys())        
        if not mapped_events == deck_events:
            logger.error(f"Missing from mapping: {deck_events - mapped_events}")
            logger.error(f"Extraneous in mapping: {deck_events - mapped_events}")
            raise RuntimeError("Event mapping mismatch")

        for deck in self._decks:
            for deck_event_name, active_event in event_mapping.items():
                deck_event = getattr(deck, deck_event_name)
                # Create a closure that captures the current active_event
                def create_handler(target_event):
                    def handler(source_deck, **kwargs):
                        # Only forward if this deck is the active deck
                        if source_deck is self.active_deck:
                            target_event.trigger(self, **kwargs)
                    handler.__name__ = f"{deck_event_name} - forward event by {__name__}"
                    return handler
                
                deck_event.subscribe(create_handler(active_event))

    @property
    def size(self) -> int:
        """Maximum number of decks this deck list can hold."""
        return self._size

    @property
    def active_deck(self) -> Deck | None:
        return self._decks[self._active_slot]

    @property
    def active_slot(self) -> int:
        return self._active_slot

    @active_slot.setter
    def active_slot(self, index: int) -> None:
        if 0 <= index < self._size:
            if index != self.active_slot:
                self.slot_deactivated.trigger(self, index=self.active_slot, deck=self.active_deck)
                self._active_slot = index
                self.slot_activated.trigger(self, index=self.active_slot, deck=self.active_deck)
                logger.debug(f"Activated deck '{self.active_deck.name}' in slot {self._active_slot}")
        else:
            raise ValueError(f"Slot {index} is out of bounds")

    def get_slot_at_offset(self, offset: int) -> int:
        offset_index = self._active_slot + offset
        offset_index = ((offset_index % self._size) + self._size) % self._size
        return offset_index

    def get_deck_at_offset(self, offset: int) -> Deck:
        index = self.get_slot_at_offset(offset)
        return self._decks[index]

    def get_deck_at_slot(self, index: int):
        return self._decks[index]

    def find_slot_by_deck(self, target_deck: Deck) -> int | None:
        """Find which slot number contains the given deck."""
        for slot, deck in self:
            if deck is target_deck:
                return slot
        return None

    def find_deck_by_slot(self, target_slot: int) -> Deck | None:
        """Get deck at specific slot (convenience method)."""
        if 0 <= target_slot < self._size:
            return self._decks[target_slot]
        return None

    def __contains__(self, deck: Deck) -> bool:
        return deck in self._decks

    def __iter__(self):
        for index in range(self._size):
            yield (index, self._decks[index])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self._size}, decks={repr(self._decks)})"
