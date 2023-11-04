import os
from nicegui import events
from nicegui import ui
import random


from anki_deck import create_deck
from database import DatabaseConnector
from cards import Card, Deck, SIDE, FRONT, BACK, CARD_ID

connector = DatabaseConnector("sqlite:///anki.db")

FRONT = "front"
BACK = "back"
CARD_ID = "card_id"


test_cards = Deck(
    "deck1",
    {
        "card1": Card("card1", "Front of card 1", "Back of card 1"),
        "card2": Card("card2", "Front of card 2?", "Back of card 2!!!!!"),
        "card3": Card("card3", "Front of card 3", "Back of card 3")
    }
)

# STATE VARIABLES
CURRENT_CARD_STATE = {CARD_ID: "card1", SIDE: FRONT}
CURRENT_DECK_ID = "deck1"
DECKS = {"deck1": test_cards}

def current_deck() -> Deck: 
    return DECKS[CURRENT_DECK_ID]

# completion = anthropic.completions.create(
#     model="claude-2",
#     max_tokens_to_sample=300,
#     prompt=f"{HUMAN_PROMPT} how does a court case get to the Supreme Court?{AI_PROMPT}",
# )
# print(completion.completion)





# cards = {
#     "card1": {
#         FRONT: "Front of card 1",
#         BACK: "Back of card 1",
#     },
#     "card2": {
#         FRONT: "Front of card 2",
#         BACK: "Back of card 2",
#     },
# }

@ui.refreshable
@ui.page("/decks")
def view_decks():
    decks = connector.get_decks()

    with ui.row():
        ui.label("Deck")
        ui.select(options=decks, label="Decks", on_change=lambda e : load_deck(e.value))


@ui.refreshable
@ui.page("/deck/{deck_name}")
def load_deck(deck_name):
    cards = connector.get_cards(deck_name)
    
    with ui.column():
        for card in cards:
            with ui.card():
                ui.label(card.front)
                ui.label(card.back)
                ui.button("Delete", on_click=lambda: delete_card(card.card_id))
                
    ui.button("Delete Deck", on_click=lambda: delete_deck(deck_name))
    


@ui.refreshable
def edit_card(card_id, front, back):
    connnector.edit_card(card_id, "new front", "new back")
    
@ui.refreshable
def delete_card(card_id):
    connector.delete_card(card_id)
    load_deck.refresh()
    
def delete_deck(deck_name):
    connector.delete_deck(deck_name)
    load_deck.refresh()
    

def flip(side):
    if side == FRONT: 
        return BACK 
    else: 
        return FRONT

# @ui.page("/deck/{deck_id}")
# def deck(deck_id: str):
#     return ui.label(str(g_decks[deck_id]))

@ui.refreshable
def card_ui():
    card_id = CURRENT_CARD_STATE[CARD_ID]
    card_front = CURRENT_CARD_STATE[SIDE]
    ui.label(f"{card_id, card_front}:")
    card = current_deck().cards[card_id]
    ui.label(card.side(card_front))


def flip_card():
    CURRENT_CARD_STATE[SIDE] = flip(CURRENT_CARD_STATE[SIDE])
    card_ui.refresh()
    
def random_card(default_side = FRONT, random_side = False):
    new_card = current_deck().random_card()
    print(new_card)
    CURRENT_CARD_STATE[CARD_ID] = new_card.card_id
    CURRENT_CARD_STATE[SIDE] = random.sample([FRONT, BACK], 1)[0] if random_side else default_side
    card_ui.refresh()


@ui.page("/card/{card_id}/{front}")
def show_card(card_id, front):
    
    card_ui()
    ui.button("Flip", on_click=flip_card)
    ui.button("Random Card", on_click=random_card)

@ui.page("/answer")
def evaluate_answer():
    pass

def handle_upload(e: events.UploadEventArguments):
    text = e.content.read().decode("utf-8")
    return text


@ui.page("/fact_check")
def fact_check():
    ui.upload(on_upload=handle_upload, label="Reference Material")


@ui.page("/create_deck")
def deck():
    ui.markdown("# Create Deck")
    topic = ui.input("Topic of Interest", placeholder="Type something you want to learn here")
    num_cards = ui.input("Number of Cards", placeholder="Type a number here")
    
    ui.input(
        "Additional Information",
        placeholder="Add things here like: your goals, things you already know",
    )

    ui.button("Create Deck", on_click=lambda: create_deck_and_add_to_db(topic.value, num_cards.value))
    
@ui.page("/create_deck/{topic}/{num_cards}")
def create_deck_and_add_to_db(topic, num_cards):
    deck = create_deck(topic, num_cards)
    connector.create_deck(deck.name)
    for card in deck.cards:
        connector.create_card(deck.name, card.front, card.back)
    
    ui.label("Deck Created")       
    # ui.notify(f"Deck Created: {topic}, {deck.cards}", type="success")
    # ui.open(f"/deck/{deck.name}")


@ui.page("/review")
def review():
    default_style = "width: 100%; margin: 10px; word-break: break-word;"
    
    show_card("card1", FRONT)

    with ui.row():
        ui.textarea("Answer:", placeholder="Type your answer here").style(
            default_style
        ).style(add="height: 100px;")
        ui.button("Send", icon="file")

    with ui.row():
        ui.button("AGAIN", color="red")
        ui.button("HARD", color="orange")
        ui.button("GOOD", color="green")
        ui.button("EASY", color="blue")


# Main page

with ui.column().style("width: 100%; height: 100%;"):
    with ui.tabs() as tabs:
        ui.tab("Fact Check", icon="info")
        ui.tab("Create Deck", icon="")
        ui.tab("Review", icon="user")
        ui.tab("Decks")

    with ui.tab_panels(tabs).classes("w-full") as panels:
        with ui.tab_panel("Create Deck"):
            deck()

        with ui.tab_panel("Review"):
            review()

        with ui.tab_panel("Fact Check"):
            fact_check()
            
        with ui.tab_panel("Decks"):
            view_decks()

dark = ui.dark_mode()
dark.enable()
ui.label('Switch mode:')
ui.button('Dark', on_click=dark.enable)
ui.button('Light', on_click=dark.disable)
ui.run()
