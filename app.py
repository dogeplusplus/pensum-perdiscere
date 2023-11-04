from nicegui import events
from nicegui import ui
import random

from cards import Card, Deck, SIDE, FRONT, BACK, CARD_ID

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

anthropic = Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my api key",
)

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
    

# decks = {"deck1": cards}

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


@ui.page("/update/card")
def update_card():
    ui.markdown("## Update Card")
    with ui.row():
        ui.label("Deck:")
        ui.select(options=["Deck 1", "Deck 2", "Deck 3"], label="Deck")


def handle_upload(e: events.UploadEventArguments):
    text = e.content.read().decode("utf-8")
    return text


@ui.page("/fact_check")
def fact_check():
    ui.upload(on_upload=handle_upload, label="Reference Material")


@ui.page("/deck")
def deck():
    ui.markdown("# Create Deck")
    ui.input("Topic of Interest", placeholder="Type something you want to learn here")
    ui.input("Deck Name", placeholder="Type something you want to learn here")
    ui.input(
        "Additional Information",
        placeholder="Add things here like: your goals, things you already know",
    )
    ui.button("Create Deck")


@ui.page("/review")
def review():
    default_style = "width: 100%; margin: 10px; word-break: break-word;"
    # card = ui.card().style(default_style).on("mousedown", show_card)
    # with card:
    #     ui.markdown(card_text)
    
    show_card("card1", FRONT)

    with ui.row():
        ui.textarea("Answer:", placeholder="Type your answer here").style(
            default_style
        ).style(add="height: 100px;")
        ui.button("Send", icon="file")

    with ui.row().style(add="align-self: center;"):
        ui.button("AGAIN", color="red")
        ui.button("HARD", color="orange")
        ui.button("GOOD", color="green")
        ui.button("EASY", color="blue")


# Main page

with ui.column().style("width: 100%; height: 100%;"):
    with ui.tabs() as tabs:
        ui.tab("Update Card", icon="home")
        ui.tab("Fact Check", icon="info")
        ui.tab("Create Deck", icon="")
        ui.tab("Review", icon="user")

    with ui.tab_panels(tabs).classes("w-full") as panels:
        with ui.tab_panel("Create Deck"):
            deck()

        with ui.tab_panel("Review"):
            review()

        with ui.tab_panel("Fact Check"):
            fact_check()

ui.run()
