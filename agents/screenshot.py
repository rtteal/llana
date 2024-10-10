import asyncio
import os
import sys

from datetime import datetime

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)


from base import BaseAgent
from utils.llm import LLM
from utils.prompts import SCREENSHOT_PROMPT
from database.main import DatabaseManager
from database.models.article import Article
from utils.logger import get_logger


class ScreenshotAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)
        self.logger = get_logger("screenshot_agent")
        self.llm = LLM(temperature=0.1, max_tokens=6500)
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
        return await self.llm.read_image(self.get_message_history(), path)

    def run(self, article_id=None):
        self.logger.info(f"Starting ScreenshotAgent run for article_id: {article_id}")
        articles = self.db_manager.get_articles_by_field("id", article_id)
        self.logger.info(f"Found {len(articles)} articles to process")
        
        with self.db_manager.get_session() as session:
            for article in articles:
                if article.content is None:
                    self.logger.info(f"Processing article: {article.title}")
                    self.add_message(
                        {
                            "role": "system",
                            "content": f'The screenshot\'s main section title is: "{article.title}". Answer with a JSON object.',
                        }
                    )
                    try:
                        content = asyncio.run(self.read_screenshot(article.screenshot_path))
                        article.content = content
                        self.logger.info(f"Successfully processed content for article: {article.title}")
                    except Exception as e:
                        self.logger.error(f"Error processing article {article.title}: {str(e)}")
                else:
                    self.logger.info(f"Article already has content: {article.title}")
            
            try:
                session.commit()
                self.logger.info("Successfully committed changes to the database")
            except Exception as e:
                self.logger.error(f"Error committing changes to the database: {str(e)}")
        
        self.logger.info("ScreenshotAgent run completed")


if __name__ == "__main__":
    logger = get_logger("screenshot_agent")
    db_manager = DatabaseManager()
    articles = db_manager.get_articles_by_field("day", "2024-10-09")
    logger.info(f"Found {len(articles)} articles to process")
    for article in articles:
        agent = ScreenshotAgent(SCREENSHOT_PROMPT)
        agent.run(article_id=article.id)
