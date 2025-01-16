"""Run `pip install duckduckgo-search sqlalchemy cohere` to install dependencies."""

from agno.agent import Agent
from agno.models.cohere import Cohere
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.agent.postgres import PostgresDbAgentStorage

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

agent = Agent(
    model=Cohere(id="command-r-08-2024"),
    storage=PostgresDbAgentStorage(table_name="agent_sessions", db_url=db_url),
    tools=[DuckDuckGoTools()],
    add_history_to_messages=True,
)
agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")
