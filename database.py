import os
import sqlalchemy

from typing import List
from dataclasses import dataclass
from sqlalchemy import String
from sqlalchemy.orm import (
    sessionmaker,
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


@dataclass
class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[int] = mapped_column(primary_key=True)
    front: Mapped[str] = mapped_column(String(1000))
    back: Mapped[str] = mapped_column(String(1000))
    deck_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("decks.deck_id"))

    deck: Mapped["Deck"] = relationship(back_populates="cards")

    def __repr__(self):
        return f"Card(front={self.front}, back={self.back})"
    

class Deck(Base):
    __tablename__ = "decks"

    deck_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    cards: Mapped[List["Card"]] = relationship(back_populates="deck", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Deck(name={self.name}, cards={self.cards})"
    
    def __json__(self):
        return {
            "deck_id": self.deck_id,
            "name": self.name,
            "cards": self.cards
        }
    

class DatabaseConnector:
    def __init__(self, db_file):
        if not os.path.exists(db_file):
            engine = sqlalchemy.create_engine(db_file)
            Base.metadata.create_all(bind=engine)

        engine = sqlalchemy.create_engine(db_file)
        self.engine = engine
        self.session = sessionmaker(bind=engine)()

    def create_deck(self, deck_name: str):
        deck = Deck(name=deck_name)
        self.session.add(deck)
        self.session.commit()
        return deck

    def create_card(self, deck_name: str, front: str, back: str):
        deck_id = (
            self.session.query(Deck).filter(Deck.name == deck_name).first().deck_id
        )
        card = Card(front=front, back=back, deck_id=deck_id)
        self.session.add(card)
        self.session.commit()
        return card

    def edit_card(self, card_id: int, front: str, back: str):
        card = self.session.query(Card).filter(Card.card_id == card_id).first()
        card.front = front
        card.back = back
        self.session.commit()

    def delete_card(self, card_id: int):
        card = self.session.query(Card).filter(Card.card_id == card_id).first()
        self.session.delete(card)
        self.session.commit()

    def delete_deck(self, deck_name: str):
        deck_id = (
            self.session.query(Deck).filter(Deck.name == deck_name).first().deck_id
        )
        deck = self.session.query(Deck).filter(Deck.deck_id == deck_id).first()
        self.session.delete(deck)
        self.session.commit()
        
    def get_deck(self, deck_name: str):
        deck = self.session.query(Deck).filter(Deck.name == deck_name).first()
        return deck
        
    def get_cards(self, deck_name: str):
        deck_id = (
            self.session.query(Deck).filter(Deck.name == deck_name).first().deck_id
        )
        cards = self.session.query(Card).filter(Card.deck_id == deck_id).all()
        cards = [
            {
                k: v for k, v in cards.__dict__.items() 
                if k != "_sa_instance_state"
            } for cards in cards
        ]
        return cards

    def get_decks(self):
        decks = self.session.query(Deck).all()
        decks = [deck.name for deck in decks]
        return decks
