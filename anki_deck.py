import os

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
    Front: str
    Back: str
    
class Deck(BaseModel):
    name: str
    cards: List[AnkiCard]


def create_card(subtopic):
    parser = PydanticOutputParser(pydantic_object=AnkiCard)
    prompt = PromptTemplate(
        template="Give me an anki card for the subtopic`n{format_instructions}\n{subtopic}\n",
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
        template="Give me a list of {num} topics for the topic`n{format_instructions}\n{topic}\n",
        input_variables=["topic", "num"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )


    _input = prompt.format_prompt(topic=topic, num=num)

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
        

deck = create_deck("Linear Algebra", 5)




