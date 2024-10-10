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
from database.main import DatabaseManager
from database.models.article import Article


class ScreenshotAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)
        self.db_manager = DatabaseManager()

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

    def run(self, article_id=None):
        articles = self.db_manager.get_articles_by_field("id", article_id)
        print(articles)
        with self.db_manager.get_session() as session:
            for article in articles:
                if article.content is None:
                    self.add_message(
                        {
                            "role": "system",
                            "content": f'The screenshot\'s main section title is: "{article.title}". Answer with a JSON object.',
                        }
                    )
                    content = asyncio.run(self.read_screenshot(article.screenshot_path))
                    article.content = content
                    session.merge(article)
            session.commit()


if __name__ == "__main__":
    db_manager = DatabaseManager()
    articles = db_manager.get_articles_by_field("day", "2024-10-09")
    for article in articles:
        agent = ScreenshotAgent(SCREENSHOT_PROMPT)
        agent.run(article_id=article.id)
