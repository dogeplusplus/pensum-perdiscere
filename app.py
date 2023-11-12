import os
import PyPDF2
import random

from enum import Enum
from tempfile import TemporaryDirectory
from nicegui import run
from nicegui import events, ui, app


class Side(Enum):
    FRONT = "front"
    BACK = "back"


from anki_deck import create_deck, answer_eval, fact_check
from database import DatabaseConnector


@ui.page("/")
async def main():
    db = DatabaseConnector("sqlite:///anki.db")
    decks = db.get_decks()
    if len(decks) == 0:
        db.create_deck("default")
        db.create_card("default", "front", "back")
        decks = db.get_decks()


    init_deck = decks[0]
    init_cards = db.get_cards(init_deck)

    app.storage.user["deck"] = app.storage.user.get("deck", init_deck)
    app.storage.user["cards"] = app.storage.user.get("cards", init_cards)
    app.storage.user["card"] = app.storage.user.get("card", random.choice(init_cards))
    app.storage.user["side"] = app.storage.user.get("side", Side.FRONT)
    app.storage.user["answer"] = app.storage.user.get("answer", dict(score=0, explanation=""))


    @ui.refreshable
    @ui.page("/decks")
    def view_decks():
        decks = db.get_decks()

        with ui.row():
            ui.label("Deck")
            ui.select(options=decks, label="Decks", on_change=lambda e : update_deck(e.value), value=app.storage.user["deck"])

        cards = db.get_cards(app.storage.user["deck"])
        
        with ui.column().style("width: 50%;"):
            for i, card in enumerate(cards):
                with ui.card():
                    ui.markdown("**Front**")
                    ui.label(cards[i]["front"])
                    ui.separator()
                    ui.markdown("**Back**")
                    ui.label(cards[i]["back"])


    @ui.refreshable
    def card_ui():
        with ui.card().on("click", flip_card):
            card = app.storage.user["card"]
            if app.storage.user["side"] == Side.FRONT:
                ui.markdown("FRONT").style("margin-right: 0; text-align: right; font-weight: bold;")
                ui.label(card["front"])
            else:
                ui.label("BACK").style("margin-right: 0; text-align: right; font-weight: bold;")
                ui.label(card["back"])


    def flip_card():
        app.storage.user["side"] = Side.BACK if app.storage.user["side"] == Side.FRONT else Side.FRONT
        card_ui.refresh()
        
    def random_card():
        new_card = random.choice(app.storage.user["cards"])

        app.storage.user["card"] = new_card
        app.storage.user["side"] = Side.FRONT
        app.storage.user["answer"] = dict(score=0, explanation="")
        card_ui.refresh()
        review.refresh()


    @ui.refreshable
    @ui.page("/card")
    def show_card():
        card_ui()
        ui.button("Random Card", on_click=random_card, color="mediumseagreen")

    @ui.refreshable
    @ui.page("/fact_check")
    async def fact_check_page():
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


        ui.button("Create Deck", on_click=lambda: create_deck_and_add_to_db(topic.value, num_cards.value), color="mediumseagreen")
        
    @ui.page("/create_deck/{topic}/{num_cards}")
    async def create_deck_and_add_to_db(topic, num_cards):
        spinner.set_visibility(True)
        deck = await run.io_bound(create_deck, topic=topic, num_cards=num_cards)
        db.create_deck(deck.name)
        for card in deck.cards:
            db.create_card(deck.name, card["front"], card["back"])
        
        spinner.set_visibility(False)
        ui.notify("Deck Created")
        view_decks.refresh()
        fact_check_page.refresh()
        review.refresh()
        
    async def handle_upload(e: events.UploadEventArguments, card_front: str, card_back: str):
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
            ui.circular_progress(value=check["score"], max=100, min=0, size="xl", show_value=True)
            ui.label(f"Score: {check.score}")
            ui.label(f"Explanation: {check.explanation}")
            ui.label(f"Verdict: {check.verdict}")
            ui.label(f"Possible Changes: {check.possible_changes}")


    @ui.refreshable
    def update_deck(deck_name):
        app.storage.user["deck"] = deck_name
        app.storage.user["cards"] = db.get_cards(deck_name)
        app.storage.user["card"] = random.choice(app.storage.user["cards"])
        app.storage.user["side"] = Side.FRONT
        app.storage.user["answer"] = dict(score=0, explanation="")

        card_ui.refresh()
        view_decks.refresh()
            

    @ui.refreshable
    @ui.page("/review")
    def review():
        default_style = "width: 100%; margin: 10px; word-break: break-word;"
        ui.markdown("### Review")
        
        with ui.row():
            ui.select(options=decks, label="Decks", on_change=lambda e : update_deck(e.value), value=app.storage.user["deck"])
        
        ui.markdown("#### Card")
        show_card()

        with ui.row():
            answer = ui.textarea("Answer:", placeholder="Type your answer here").style(
                default_style
            ).style(add="height: 80%; word-break: break-word; width: 100%;")
            
        with ui.row():
            ui.button("Send", icon="question", on_click=lambda: answer_eval_page(answer.value), color="mediumseagreen")

        color_score_map = {
            1: "#FF0000",
            2: "#FF3300",
            3: "#FF6600",
            4: "#FF9900",
            5: "#FFCC00",
            6: "#FFFF00",
            7: "#CCFF00",
            8: "#99FF00",
            9: "#66FF00",
            10: "#00FF00"
        }

        score = app.storage.user["answer"]["score"]
        explanation = app.storage.user["answer"]["explanation"]
        if score != 0:
            score_color = color_score_map[score]
            with ui.card():
                ui.circular_progress(value=score, max=10, min=1, size="xl", show_value=True, color=score_color)
                ui.label(f"Score: {score}")
                ui.label(f"Explanation: {explanation}")
        
    @ui.refreshable
    @ui.page("/answer_eval")
    async def answer_eval_page(answer):
        spinner.set_visibility(True)
        card_front = app.storage.user["card"]["front"]
        card_back = app.storage.user["card"]["back"]

        evaluation = await run.io_bound(answer_eval, card_front=card_front, card_back=card_back, answer=answer)
        app.storage.user["answer"] = evaluation

        spinner.set_visibility(False)
        review.refresh()


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
            await fact_check_page()
            
        with ui.tab_panel("Decks"):
            view_decks()


    dark = ui.dark_mode()
    dark.enable()

    spinner = ui.spinner(size="xl")
    spinner.set_visibility(False)

ui.run(
    title="PensumPerdiscere", 
    favicon="ankiclaude.png",
    storage_secret="secret",
)
