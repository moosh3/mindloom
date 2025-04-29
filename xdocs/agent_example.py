from os import getenv, path
from agno.agent import Agent, AgentKnowledge
from agno.embedder.azure_openani import AzureOpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.models.azure import AzureOpenAI
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.pgvector import PgVector, SearchType

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

def create_agent(debug_mode: bool = False) -> Agent:
    return Agent(
        name="Example Agent",
        agent_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        model=AzureOpenAI(id="gpt-4.1", api_version="2024-12-01-preview"),
        tools=[ReasoningTools()],
        knowledge=knowledge_base,
        additional_context="",
        markdown=False,
        add_datetime_to_instructions=True,
        add_history_to_messages=True,
        num_history_reponses=5,
        read_chat_history=True,
        show_tool_calls=True,
        debug_mode=debug_mode,
        storage=PostgresAgentStorage(
            db_url=os.getenv("DATABASE_URL"),
            table_name="agent_storage"
        ),
        description=dedent("""
        You do a thing
        """),
        instructions=dedent("""
        Do a thing
        """),
    )


if __name__ == "__main__":
    agent = create_agent(debug_mode=True)
    agent.run()
    