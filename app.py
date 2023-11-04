from nicegui import events
from nicegui import ui

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

anthropic = Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my api key",
)

FRONT = "front"
BACK = "back"
CARD_ID = "card_id"
g_current_card = {CARD_ID: "card1", FRONT: FRONT}

# completion = anthropic.completions.create(
#     model="claude-2",
#     max_tokens_to_sample=300,
#     prompt=f"{HUMAN_PROMPT} how does a court case get to the Supreme Court?{AI_PROMPT}",
# )
# print(completion.completion)



front = "frontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfront"
back = BACK

card_text = f"## Front: \n\n {front}"
show_front = True

cards = {
    "card1": {
        FRONT: "Front of card 1",
        BACK: "Back of card 1",
    },
    "card2": {
        FRONT: "Front of card 2",
        BACK: "Back of card 2",
    },
}


# @attrs.define
# class Card:
#     card_id: str
#     front: str
#     back: str
#     tags: set = attrs.field(factory=list)


# card1 = Card("card1", "front of card 1", "back of card 1")
# card2 = Card("card1", "front of card 2", "back of card 2")

decks = {"deck1": cards}

def flip(front):
    if front == FRONT: 
        return BACK 
    else: 
        return FRONT

@ui.page("/deck/{deck_id}")
def deck(deck_id: str):
    return decks[deck_id]

@ui.refreshable
def card_ui():
    card_id = g_current_card[CARD_ID]
    card_front = g_current_card[FRONT]
    ui.label(f"{card_id, card_front}:")
    ui.label(cards[card_id][card_front])

def flip_card():
    g_current_card["front"] = flip(g_current_card["front"])
    card_ui.refresh()

    
    
    
@ui.page("/card/{card_id}/{front}")
def show_card(card_id, front):
    
    card_ui()
    ui.button("Flip", on_click=flip_card)


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
