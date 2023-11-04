from argparse import Namespace
from nicegui import events
from nicegui import ui
import random


from anki_deck import create_deck, answer_eval
from database import DatabaseConnector
from cards import Card, Deck, SIDE, FRONT, BACK, CARD_ID

connector = DatabaseConnector("sqlite:///anki.db")

ANSWER= "answer"
FRONT = "front"
BACK = "back"
CARD_ID = "card_id"
CARD = "card"
CARDS = "cards"
DECK = "deck"

decks = connector.get_decks()

init_deck = decks[0]
init_cards = connector.get_cards(init_deck)

STATE = {
    DECK: init_deck,
    CARDS: init_cards,
    CARD: random.choice(init_cards),
    SIDE: FRONT,
    ANSWER: Namespace(score="", explanation=""),
}

def current_deck() -> Deck: 
    return connector.get_deck(CURRENT_DECK_ID)

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
        for i, card in enumerate(cards):
            with ui.card():
                ui.label(cards[i].front)
                ui.label(cards[i].back)
    


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

@ui.refreshable
def card_ui():
    card = STATE[CARD]
    side = STATE[SIDE]
    
    with ui.card():
        if side == FRONT:
            ui.markdown("FRONT").style("margin-right: 0; text-align: right; font-weight: bold;")
            ui.label(card.front)
        else:
            ui.label("BACK").style("margin-right: 0; text-align: right; font-weight: bold;")
            ui.label(card.back)


def flip_card():
    STATE[SIDE] = flip(STATE[SIDE])
    card_ui.refresh()
    
def random_card():
    new_card = random.choice(STATE[CARDS])
    STATE[CARD] = new_card
    STATE[SIDE] = FRONT
    STATE[ANSWER] = Namespace(score="", explanation="")
    card_ui.refresh()


@ui.page("/card")
def show_card():
    
    card_ui()
    with ui.row():
        ui.button("Flip", on_click=flip_card)
        ui.button("Random Card", on_click=random_card)

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
    load_deck.refresh()
    view_decks.refresh()
    

@ui.refreshable
def update_deck(deck_name):
    STATE[DECK] = deck_name
    STATE[CARDS] = connector.get_cards(deck_name)
    STATE[CARD] = random.choice(STATE[CARDS])
    STATE[SIDE] = FRONT
    STATE[ANSWER] = Namespace(score="", explanation="")

    card_ui.refresh()
        
    

@ui.refreshable
@ui.page("/review")
def review():
    default_style = "width: 100%; margin: 10px; word-break: break-word;"
    
    with ui.row():
        ui.select(options=decks, label="Decks", on_change=lambda e : update_deck(e.value), value=STATE[DECK])
    
    ui.markdown("#### Card")
    show_card()

    with ui.row():
        answer = ui.textarea("Answer:", placeholder="Type your answer here").style(
            default_style
        ).style(add="height: 80%;")
        
    with ui.row():
        ui.button("Send", icon="question", on_click=lambda: answer_eval_page(answer.value))

    
    color_score_map = {
        1: "red",
        2: "orange",
        3: "green",
        4: "blue",
    }
    if STATE[ANSWER].score != "":
        score_color = color_score_map[STATE[ANSWER].score]
        with ui.card().style(f"background-color: {score_color}; color: white;"):
            ui.label(f"Score: {STATE[ANSWER].score}")
            ui.label(f"Explanation: {STATE[ANSWER].explanation}")
    
@ui.refreshable
@ui.page("/answer_eval")
def answer_eval_page(answer):
    card_front = STATE[CARD].back
    card_back = STATE[CARD].front

    evaluation = answer_eval(card_front, card_back, answer)
    STATE[ANSWER] = evaluation

        
    review.refresh()


# Main page

with ui.column().style("width: 100%; height: 100%;"):
    ui.image("ankiclaude.png").style("width: 3%; height: 3%;")
    with ui.tabs() as tabs:
        ui.tab("Review", icon="plagiarism")
        ui.tab("Create Deck", icon="add_circle")
        ui.tab("Decks", icon="view_list")
        ui.tab("Fact Check", icon="fact_check")

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
with ui.row():
    ui.button('Dark', on_click=dark.enable)
    ui.button('Light', on_click=dark.disable)
ui.run()
