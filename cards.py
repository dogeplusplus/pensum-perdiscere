
import attrs
import random

SIDE = "side"
FRONT = "front"
BACK = "back"
CARD_ID = "card_id"

@attrs.define
class Card:
    card_id: str
    front: str
    back: str
    
    def side(self, front):
        if front==FRONT:
            return self.front
        else:
            return self.back

@attrs.define
class Deck:
    deck_id: str
    cards: dict
    
    def __post_init__(self):
        assert all( self.cards[k].card_id == k for k in self.cards.keys() )
    def random_card(self) -> Card:
        key = random.sample(sorted(self.cards), 1)[0]
        return self.cards[key]