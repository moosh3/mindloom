from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.team.team import Team
from agno.embedder.azure_openani import AzureOpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from os import getenv
import asyncio

knowledge_base = TextKnowledgeBase(
    path="knowledge_base.txt",
    vector_db=PgVector(
        table_name="knowledge_base",
        db_url=os.getenv("DATABASE_URL"),
        embedder=AzureOpenAIEmbedder(
            model_name="text-embedding-ada-002",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_base=os.getenv("AZURE_OPENAI_API_BASE")
        ),
        search_type=SearchType.hybrid
    )
)

english_agent = Agent(
    name="English Agent",
    role="You only answer in English",
    model=AzureOpenAI(id="gpt-4.1", api_version="2024-12-01-preview"),
)

spanish_agent = Agent(
    name="Spanish Agent",
    role="You only answer in Spanish",
    model=AzureOpenAI(id="gpt-4.1", api_version="2024-12-01-preview"),
)

team = Team(
    name="Translation Team",
    members=[english_agent, spanish_agent],
    model=AzureOpenAI(id="gpt-4.1", api_version="2024-12-01-preview"),
    mode=["coordinate", "collaborate", "route"],
    show_tool_calls=True,
    markdown=False,
    enable_agentic_context=True,    # Allows the team leader to maintain and update the team's context during the run
    share_member_interactions=True, # Share interactions between team members, allowing agents to learn from each others outputs
    enable_team_history=True,       # Maintain a memory of previous interactions, enabling contextual awareness
    num_of_interactions_from_history=5,
    enable_agentic_memory=True,    # Enables the team to maintain and update its own memory during the run
    show_members_responses=True,
    show_tool_calls=True,
    knowledge=knowledge_base,
    description="You are a language router that directs questions to the appropriate language agent.",
    instructions=["Direct questions to the appropriate language agent."]
)

async def main():
    async for chunk in await team.arun("What is 2+2?", stream=True):
        print(chunk.content, end="", flush=True)