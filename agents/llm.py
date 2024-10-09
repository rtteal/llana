from dotenv import load_dotenv
from dotenv import load_dotenv
from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI


import base64
import openai
import os

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
        "model": "gpt-4o-mini",
    },
}

# Choose configuration
CONFIG_KEY = "openai_gpt-4"
CONFIG = CONFIGURATIONS[CONFIG_KEY]

# Initialize the OpenAI async client
client = AsyncOpenAI()

GEN_KWARGS = {"model": CONFIG["model"], "temperature": 0.7, "max_tokens": 500}


@observe
async def read_image(message_history, path, image_type="png"):
    with open(path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
        message_history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        )
    response = await client.chat.completions.create(
        messages=message_history, **GEN_KWARGS
    )
    return response.choices[0].message.content
