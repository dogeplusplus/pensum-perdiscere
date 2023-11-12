# pensum-perdiscere (PePe)

Submission to the Anthropic London Hackathon 2023.

## Inspiration

- School education has well-established learning paths for subjects like English/Math.
- Niche subjects lack this organized structure
- Practicing is one of the best ways to retain knowledge

## What it does

PePe can:
- create bespoke study plans for any topic by breaking it down into key concepts to know
- test you on your knowledge with feedback for better retention

## How we built it
- NiceGUI for the web application
- Basic SQLAlchemy ORM for the data store
- Claude-2 for topic and card creation
- LangChain output parsers for formatting the outputs into nice python data structures

## Challenges we ran into
- State management in the web application
- Web socket connection dying because we're not good at WebDev

## Accomplishments that we're proud of
- Being able to create a working UI that can display cards
- Learning about new frameworks and APIs that use state of the art LLMs

## What we learned
- Using LangChain
- Using Claude API
- How to make a user interface with NiceGUI (and that it's not actually that nice)

## What's next for PePe (PensumPerdiscere)
- Being able to ramp up the difficulty levels of quizzes
- Design new interactive exercises for learner that Claude can give detailed feedback for
- Delete cards, automatic quality scoring and fact checking of cards
- Suggest new things that the student can learn
- Provide detailed summary based on their answers and scores from reviewing
