import os
from dotenv import load_dotenv
import chainlit as cl
import openai
from prompts import SYSTEM_PROMPT
from langsmith import traceable

# Load environment variables
load_dotenv()

CONFIGURATIONS = {
    "mistral_7B_instruct": {
        "endpoint_url": os.getenv("MISTRAL_7B_INSTRUCT_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
    },
    "mistral_7B": {
        "endpoint_url": os.getenv("MISTRAL_7B_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-v0.1",
    },
    "openai_gpt-4": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4",
    },
}

# Choose configuration
CONFIG_KEY = "openai_gpt-4"
CONFIG = CONFIGURATIONS[CONFIG_KEY]

# Initialize the OpenAI async client
client = openai.AsyncClient(api_key=CONFIG["api_key"], base_url=CONFIG["endpoint_url"])

GEN_KWARGS = {"model": CONFIG["model"], "temperature": 0.3, "max_tokens": 500}

def initialize_bot():
    message_history = cl.user_session.get("message_history", [])
    if not message_history:
        message_history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        cl.user_session.set("message_history", message_history)

@traceable(run_type="llm")
async def get_gpt_response_stream(request):
    message_history = cl.user_session.get("message_history", [])
    message_history.append(request)
    response = cl.Message(content="")
    
    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **GEN_KWARGS
    )
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response.stream_token(token)
    
    message_history.append({"role": "assistant", "content": response.content})
    cl.user_session.set("message_history", message_history)
    await response.send()

@traceable
@cl.on_chat_start
async def on_chat_start():
    initialize_bot()

@traceable
@cl.on_message
async def on_message(message: cl.Message):
    await get_gpt_response_stream({"role": "user", "content": message.content})

if __name__ == "__main__":
    cl.main()