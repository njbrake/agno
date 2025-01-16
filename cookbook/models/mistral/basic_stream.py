import os

from agno.agent import Agent, RunResponse  # noqa
from agno.models.mistral import Mistral

mistral_api_key = os.getenv("MISTRAL_API_KEY")

agent = Agent(
    model=Mistral(
        id="mistral-large-latest",
        api_key=mistral_api_key,
    ),
    markdown=True,
)

# Get the response in a variable
# run_response: Iterator[RunResponse] = agent.run("Share a 2 sentence horror story", stream=True)
# for chunk in run_response:
#     print(chunk.content)

# Print the response in the terminal
agent.print_response("Share a 2 sentence horror story", stream=True)
