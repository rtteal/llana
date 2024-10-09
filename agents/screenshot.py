import asyncio
import os
import sys

from datetime import datetime

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)


from base import BaseAgent
from utils.llm import read_image
from utils.prompts import SCREENSHOT_PROMPT


class ScreenshotAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--screenshot-folder", type=str, help="Path to the screenshot folder"
        )
        parser.add_argument("--date", type=str, help="Date for the screenshot folder")
        parser.add_argument("--filename", type=str, help="Filename of the screenshot")

    async def read_screenshot(self, path):
        return await read_image(self.get_message_history(), path)

    def run(self):
        date = self.args.date or datetime.now().strftime("%Y-%m-%d")
        filename = self.args.filename or "screenshot"
        root_folder = self.args.screenshot_folder or "screenshots"
        path = f"{parent_dir}/{root_folder}/{date}/{filename}"
        return asyncio.run(self.read_screenshot(path))


if __name__ == "__main__":
    agent = ScreenshotAgent(SCREENSHOT_PROMPT)
    result = agent.run()
    print(result)
