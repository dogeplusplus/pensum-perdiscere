from nicegui import events
from nicegui import ui


front = "frontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfrontfront"
back = "back"

card_text = f"## Front: \n\n {front}"
show_front = True

cards = {
    "card1": {
        "front": "Front of card 1",
        "back": "Back of card 1",
    },
    "card2": {
        "front": "Front of card 2",
        "back": "Back of card 2",
    },
}


@ui.page("/deck/{deck_id}")
def deck(deck_id: str):
    return cards




@ui.page("/card/{card_id}/{front}")
def show_card(card_id, front):
    global button
    
    with ui.card().style(add="width: 50%;"):
        markdown = ui.markdown(card_text)
        
        if front == "front":
            markdown.set_content(f"## Front: \n\n {cards[card_id]['front']}")
        else:
            markdown.set_content(f"## Back: \n\n {cards[card_id]['back']}")

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
    ui.button("Create Deck")



@ui.page("/review")
def review():
    default_style = "width: 100%; margin: 10px; word-break: break-word;"
    # card = ui.card().style(default_style).on("mousedown", show_card)
    # with card:
    #     ui.markdown(card_text)
    
    show_card("card1", "front").on("mousedown", show_card("card1", "back"))

    with ui.row():
        ui.textarea("Answer:", placeholder="Type your answer here").style(default_style).style(add="height: 100px;")
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