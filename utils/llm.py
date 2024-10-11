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


class LLM:
    def __init__(self, config_key=CONFIG_KEY, temperature=0.1, max_tokens=500):
        self.config_key = config_key
        self.config = CONFIGURATIONS[self.config_key]
        self.client = AsyncOpenAI()
        self.gen_kwargs = {
            "model": self.config["model"],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    
    async def read_image(self, message_history, path, image_type="png"):
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
        response = await self.client.chat.completions.create(
            messages=message_history, **self.gen_kwargs
        )
        return response.choices[0].message.content

    async def get_llm_response_stream(self, message_history):
        try:
            gpt_response = ""
            stream = await self.client.chat.completions.create(
                messages=message_history, stream=True, **self.gen_kwargs
            )
            # Get GPT response via streaming
            async for part in stream:
                if token := part.choices[0].delta.content or "":
                    # await response.stream_token(token)
                    gpt_response += token
            return gpt_response
        except Exception as e:
            print(f"Error in get_gpt_response_stream: {str(e)}")
            return f"An error occurred: {str(e)}"
