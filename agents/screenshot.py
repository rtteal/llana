import asyncio

from datetime import datetime
from llm import read_image
from base import BaseAgent

SYSTEM_PROMPT = """\
You are a helpful assistant that students access to understand the content inside a screenshot. 
Your main task is to summarize the content inside the screenshot, and provide a detailed explanation
of the content. The intended audience is a computer science student so the explanation should be tailored
to this audience.
"""


class ScreenshotAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument('--screenshot-folder', type=str, help='Path to the screenshot folder')
        parser.add_argument('--date', type=str, help='Date for the screenshot folder')
        parser.add_argument('--filename', type=str, help='Filename of the screenshot')

    async def read_screenshot(self, path):
        return await read_image(self.get_message_history(), path)

    def run(self):
        date = self.args.date or datetime.now().strftime("%Y-%m-%d")
        filename = self.args.filename or "screenshot"    
        root_folder = self.args.screenshot_folder or "screenshots"
        path = f"{root_folder}/{date}/{filename}.png"
        
        return asyncio.run(self.read_screenshot(path))


if __name__ == "__main__":
    agent = ScreenshotAgent(SYSTEM_PROMPT)
    result = agent.run()
    print(result)
