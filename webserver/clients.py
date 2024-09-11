from openai import AsyncOpenAI

from common.utils.logger import setup_logging
from webserver.config import get_openai_api_key

# Set up logging
logger = setup_logging()

# Global variable to store the OpenAI client
openai_client: AsyncOpenAI | None = None


async def openai_client_setup() -> None:
    global openai_client
    if openai_client is None:
        api_key = get_openai_api_key()
        if not api_key:
            logger.error("OpenAI API key is not set.")
            raise ValueError("OpenAI API key is not set.")
        openai_client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI client initialized.")


async def open_ai_client_teardown() -> None:
    global openai_client
    if openai_client is not None:
        await openai_client.close()
        logger.info("OpenAI client closed.")
        openai_client = None


async def get_openai_client() -> AsyncOpenAI:
    global openai_client
    if openai_client is None:
        await openai_client_setup()
    logger.info(f"OpenAI client retrieved: {openai_client}")
    return openai_client
