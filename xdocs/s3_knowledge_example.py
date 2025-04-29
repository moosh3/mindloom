from agno.agent import Agent
from agno.knowledge.s3.pdf import S3PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = S3PDFKnowledgeBase(
    bucket_name="agno-public",
    key="recipes/ThaiRecipes.pdf",
    vector_db=PgVector(table_name="recipes", db_url=db_url),
)

agent = Agent(
    knowledge=knowledge_base,
    search_knowledge=True,
)
agent.knowledge.load(recreate=False)

agent.print_response("How to make Thai curry?")