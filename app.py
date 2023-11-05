import os
import asyncio
import PyPDF2

from tempfile import TemporaryDirectory
from nicegui import run
from argparse import Namespace
from nicegui import events
from nicegui import ui
import random


from anki_deck import create_deck, answer_eval, fact_check
from database import DatabaseConnector
from cards import Deck, SIDE, FRONT, BACK

connector = DatabaseConnector("sqlite:///anki.db")

ANSWER= "answer"
FRONT = "front"
BACK = "back"
CARD_ID = "card_id"
CARD = "card"
CARDS = "cards"
DECK = "deck"

decks = connector.get_decks()
if len(decks) == 0:
    connector.create_deck("default")
    connector.create_card("default", "front", "back")
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
    return connector.get_deck(STATE[DECK])

@ui.refreshable
@ui.page("/decks")
def view_decks():
    decks = connector.get_decks()


    with ui.row():
        ui.label("Deck")
        ui.select(options=decks, label="Decks", on_change=lambda e : update_deck(e.value), value=STATE[DECK])

    cards = connector.get_cards(STATE[DECK])
    
    with ui.column().style("width: 50%;"):
        for i, card in enumerate(cards):
            with ui.card():
                ui.markdown("**Front**")
                ui.label(cards[i].front)
                ui.separator()
                ui.markdown("**Back**")
                ui.label(cards[i].back)

    

@ui.refreshable
async def edit_card(card_id, front, back):
    connector.edit_card(card_id, "new front", "new back")
    
@ui.refreshable
def delete_card(card_id):
    connector.delete_card(card_id)
    

def delete_deck(deck_name):
    connector.delete_deck(deck_name)
    view_decks.refresh()
    

def flip(side):
    if side == FRONT: 
        return BACK 
    else: 
        return FRONT

@ui.refreshable
def card_ui():
    card = STATE[CARD]
    side = STATE[SIDE]
    
    with ui.card().on("mousedown", flip_card):
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
    review.refresh()


@ui.refreshable
@ui.page("/card")
def show_card():
    card_ui()
    ui.button("Random Card", on_click=random_card)

async def handle_upload(e: events.UploadEventArguments, card_front: str, card_back: str):
    import pdb; pdb.set_trace()
    with e.content as f, TemporaryDirectory() as temp_dir:

        temp_file = os.path.join(temp_dir, "temp.pdf")
        with open(temp_file, "wb") as f2:
            f2.write(f.read())

        if e.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(temp_file)


            reference = ""
            for page_num in range(len(pdf_reader.pages)):
                pdf_page = pdf_reader.pages[page_num]
                reference += pdf_page.extract_text()
        elif e.type == "text/plain":
            reference = f.read().decode("utf-8")
        else:
            ui.notify("File type not supported", type="error")


    check = await run.io_bound(fact_check, card_front=card_front, card_back=card_back, evidence=reference)

    with ui.card():
        ui.circular_progress(value=check.score, max=100, min=0, size="xl", show_value=True)
        ui.label(f"Score: {check.score}")
        ui.label(f"Explanation: {check.explanation}")
        ui.label(f"Verdict: {check.verdict}")
        ui.label(f"Possible Changes: {check.possible_changes}")

@ui.refreshable
@ui.page("/fact_check")
def fact_check_page():
    ui.markdown("### Fact Check")

    card_front = ui.textarea("Card Front", placeholder="Front of the card")
    card_back = ui.textarea("Card Back", placeholder="Back of the card")
    ui.upload(on_upload=lambda e: handle_upload(e, card_front.value, card_back.value), label="Reference Material")



@ui.page("/create_deck")
def deck():
    ui.markdown("### Create Deck")
    topic = ui.input("Topic of Interest", placeholder="Type something you want to learn here")
    num_cards = ui.input("Number of Cards", placeholder="Type a number here")
    
    ui.input(
        "Additional Information",
        placeholder="Add things here like: your goals, things you already know",
    )


    ui.button("Create Deck", on_click=lambda: create_deck_and_add_to_db(topic.value, num_cards.value))
    
@ui.page("/create_deck/{topic}/{num_cards}")
async def create_deck_and_add_to_db(topic, num_cards):
    spinner.set_visibility(True)
    deck = await run.io_bound(create_deck, topic=topic, num_cards=num_cards)
    connector.create_deck(deck.name)
    for card in deck.cards:
        connector.create_card(deck.name, card.front, card.back)
    
    spinner.set_visibility(False)
    ui.notify("Deck Created")
    view_decks.refresh()
    fact_check_page.refresh()
    review.refresh()
    

@ui.refreshable
def update_deck(deck_name):
    STATE[DECK] = deck_name
    STATE[CARDS] = connector.get_cards(deck_name)
    STATE[CARD] = random.choice(STATE[CARDS])
    STATE[SIDE] = FRONT
    STATE[ANSWER] = Namespace(score="", explanation="")

    card_ui.refresh()
    view_decks.refresh()
        

@ui.refreshable
def update_card(card_id):
    STATE[CARD] = connector.get_card(card_id)
    STATE[SIDE] = FRONT
    STATE[ANSWER] = Namespace(score="", explanation="")
    card_ui.refresh()
    

@ui.refreshable
@ui.page("/review")
def review():
    default_style = "width: 100%; margin: 10px; word-break: break-word;"
    ui.markdown("### Review")
    
    with ui.row():
        ui.select(options=decks, label="Decks", on_change=lambda e : update_deck(e.value), value=STATE[DECK])
    
    ui.markdown("#### Card")
    show_card()

    with ui.row():
        answer = ui.textarea("Answer:", placeholder="Type your answer here").style(
            default_style
        ).style(add="height: 80%; word-break: break-word; width: 100%;")
        
    with ui.row():
        ui.button("Send", icon="question", on_click=lambda: answer_eval_page(answer.value))

    color_score_map = {
        1: "#FF0000",  # Red
        2: "#FF3300",
        3: "#FF6600",
        4: "#FF9900",
        5: "#FFCC00",
        6: "#FFFF00",
        7: "#CCFF00",
        8: "#99FF00",
        9: "#66FF00",
        10: "#00FF00"  # Green
    }

    # color map dictionary from 1 to 10, 1 being red and 10 being green
    
    if STATE[ANSWER].score != "":
        score_color = color_score_map[STATE[ANSWER].score]
        with ui.card():
            ui.circular_progress(value=STATE[ANSWER].score, max=10, min=1, size="xl", show_value=True, color=score_color)
            ui.label(f"Score: {STATE[ANSWER].score}")
            ui.label(f"Explanation: {STATE[ANSWER].explanation}")
    
@ui.refreshable
@ui.page("/answer_eval")
async def answer_eval_page(answer):
    spinner.set_visibility(True)
    card_front = STATE[CARD].front
    card_back = STATE[CARD].back

    evaluation = await run.io_bound(answer_eval, card_front=card_front, card_back=card_back, answer=answer)
    STATE[ANSWER] = evaluation

    spinner.set_visibility(False)
    review.refresh()


# Main page

with ui.row().style("width: 100%; height: 100%;"):
    ui.image("ankiclaude.png").style("width: 3%; height: 3%;")
    with ui.column().style("padding: 0px; margin: 0px;"):
        ui.markdown("#### **Pe**nsum**Pe**rdiscere \n\n(Pensum - Task, Perdiscere - To Learn Thoroughly)")
        

    with ui.tabs() as tabs:
        ui.tab("Review", icon="plagiarism")
        ui.tab("Create Deck", icon="add_circle")
        ui.tab("Decks", icon="view_list")
        ui.tab("Fact Check", icon="fact_check")


with ui.tab_panels(tabs).style("width: 50%;") as panels:
    with ui.tab_panel("Create Deck"):
        deck()

    with ui.tab_panel("Review"):
        review()

    with ui.tab_panel("Fact Check"):
        fact_check_page()
        
    with ui.tab_panel("Decks"):
        view_decks()


dark = ui.dark_mode()
dark.enable()

spinner = ui.spinner(size="xl")
spinner.set_visibility(False)

with ui.row():
    ui.button('Dark', on_click=dark.enable)
    ui.button('Light', on_click=dark.disable)
ui.run(title="PensumPerdiscere")
