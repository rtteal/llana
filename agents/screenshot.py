import openai
from dotenv import load_dotenv
import os
from langsmith.wrappers import wrap_openai
import base64
import asyncio
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
        "model": "gpt-4o-mini",
    },
}
# Choose configuration
CONFIG_KEY = "openai_gpt-4"
CONFIG = CONFIGURATIONS[CONFIG_KEY]

# Initialize the OpenAI async client
client = wrap_openai(
    openai.AsyncClient(api_key=CONFIG["api_key"], base_url=CONFIG["endpoint_url"])
)

GEN_KWARGS = {"model": CONFIG["model"], "temperature": 0.7, "max_tokens": 500}
SYSTEM_PROMPT = """\
You are a helpful assistant that can read screenshots and provide summaries.
"""
class ScreenshotAgent:
    def __init__(self, system_prompt):
        self.message_history = [{"role": "system", "content": system_prompt}]

    async def read_screenshot(self, path):
        with open(path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
            self.message_history.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            )
        response = await client.chat.completions.create(
            messages=self.message_history,
            **GEN_KWARGS
        )
        return response.choices[0].message.content

async def main():
    agent = ScreenshotAgent(SYSTEM_PROMPT)
    r =  await agent.read_screenshot("screenshots/Show HN: Winamp and other media players, rebuilt for the web with Web Components.png")
    print(r)

if __name__ == "__main__":
    asyncio.run(main())