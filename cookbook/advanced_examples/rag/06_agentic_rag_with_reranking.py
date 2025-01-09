"""
1. Run: `pip install openai lancedb tantivy pypdf sqlalchemy phidata cohere` to install the dependencies
2. Run: `python cookbook/rag/03_traditional_rag_lancedb.py` to run the agent
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFUrlKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.reranker.cohere import CohereReranker

# Create a knowledge base of PDFs from URLs
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    # Use LanceDB as the vector database and store embeddings in the `recipes` table
    vector_db=LanceDb(
        table_name="recipes",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(model="text-embedding-3-small"),
        reranker=CohereReranker(model="rerank-multilingual-v3.0"),  # Add a reranker
    ),
)
# Load the knowledge base: Comment after first run as the knowledge base is already loaded
knowledge_base.load()

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge_base,
    # Add a tool to search the knowledge base which enables agentic RAG.
    # This is enabled by default when `knowledge` is provided to the Agent.
    search_knowledge=True,
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("How do I make chicken and galangal in coconut milk soup", stream=True)
