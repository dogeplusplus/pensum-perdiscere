import os
from cards import Card

from langchain.chat_models import ChatAnthropic
from langchain.prompts import PromptTemplate
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from langchain.output_parsers import PydanticOutputParser

load_dotenv(find_dotenv())

api_key = os.getenv("ANTHROPIC_API_KEY")
chat = ChatAnthropic(anthropic_api_key=api_key, model="claude-2")


class AnkiCard(BaseModel):
    front: str
    back: str


class Deck(BaseModel):
    name: str
    cards: List[AnkiCard]


def create_card(subtopic):
    parser = PydanticOutputParser(pydantic_object=AnkiCard)
    prompt = PromptTemplate(
        template="Give me an anki card for the subtopic\n{format_instructions}\n{subtopic}\n",
        input_variables=["subtopic"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    _input = prompt.format_prompt(subtopic=subtopic)

    output = chat.predict(_input.text)
    result = parser.parse(output)
    return result


class Topic(BaseModel):
    topic: str
    subtopics: List[str]


def create_subtopics(topic, num):
    parser = PydanticOutputParser(pydantic_object=Topic)
    prompt = PromptTemplate(
        template="Give me a list of {num} topics for the topic\n{format_instructions}\n{topic}\n",
        input_variables=["topic", "num"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    _input = prompt.format_prompt(topic=topic, num=num)

    output = chat.predict(_input.text)
    result = parser.parse(output)
    return result


def fact_check(topic, card_front: str, card_back: str, evidence: str):
    parser = PydanticOutputParser(pydantic_object=Topic)
    prompt = PromptTemplate(
        template="Here is the front of the current anki card: <FRONT>{card_front}</FRONT>\n \
                and here is the back of the current anki card: <BACK>{card_back}</BACK>.\n \
                The back is supposed to be the answer to the front of the card.\
                Here is some expert evidence that you should use to evaluate if the card is correct: <EVIDENCE>{evidence}</EVIDENCE>\
                Does the evidence show that the card is correct? Explain your reasoning.\n \
                If there needs to be any corrections, suggest what they should be.\n{format_instructions}\n{topic}",
        input_variables=["card_front", "card_back", "evidence"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    _input = prompt.format_prompt(
        topic=topic, card_front=card_front, card_back=card_back, evidence=evidence
    )

    output = chat.predict(_input.text)
    result = parser.parse(output)
    return result


def create_deck(topic, num_cards):
    subtopics = create_subtopics(topic, num_cards)
    cards = []
    for subtopic in subtopics.subtopics:
        card = create_card(subtopic)
        cards.append(card)

    deck = Deck(cards=cards, name=subtopics.topic)
    return deck


def main():
    # test create deck
    # deck = create_deck("Linear Algebra", 5)
    # print(deck)

    # test fact check
    evidence = "Brian is a 70 year-old alcoholic and needs a new kidney"
    card_front = "Is Brian OK?"
    card_back = (
        "Yeah Brian is OK I saw him yesterday and all his organs seem to be working"
    )

    print(fact_check("Health", card_front, card_back, evidence))


if __name__ == "__main__":
    main()
