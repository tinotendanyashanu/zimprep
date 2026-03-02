from openai import AsyncOpenAI
from core.config import settings

# Initialize AsyncOpenAI client
# It relies on settings.openai_api_key being properly set in .env
client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_embedding(text: str) -> list[float]:
    """Generates an embedding for the given text using OpenAI API."""
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
