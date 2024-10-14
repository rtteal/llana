import asyncio
import argparse
import os
import sys
import json
from argparse import ArgumentParser
from datetime import datetime, timedelta
from langfuse.decorators import observe, langfuse_context
from langfuse import Langfuse

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from agents.evaluate import EvaluateAgent
from base import BaseAgent
from utils.llm import LLM
from utils.prompts import PODCAST_GENERATOR_PROMPT
from database.main import DatabaseManager
from database.models.article import Article
from utils.logger import get_logger


class PodcastGeneratorAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)
        self.logger = get_logger("podcast_generator_agent")
        self.llm = LLM(temperature=0.7, max_tokens=5500)
        self.db_manager = DatabaseManager()
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET"),
            public_key=os.getenv("LANGFUSE_PUBLIC"),
            host=os.getenv("LANGFUSE_HOST"),
        )

    async def generate_podcast(self):
        return await self.llm.get_llm_response_stream(self.get_message_history())

    @observe
    def run(self, article_id=None):
        langfuse_context.update_current_trace(tags=["podcast_generator_agent", "run"])
        self.logger.info(f"Starting PodcastGeneratorAgent run for article_id: {article_id}")
        article = self.db_manager.get_articles_by_field("id", article_id)[0]
        self.logger.info(f"Found article to process: {article.title}")

        with self.db_manager.get_session() as session:
            if article.content is not None and article.podcast is None:
                parsed_content = json.loads(article.content)
                self.logger.info(f"Creating podcast for article: {article.title}")
                self.add_message(
                    {
                        "role": "system",
                            "content": f'The article\'s summary is: "{parsed_content["main"]["summary"]}"',
                    }
                )
                try:
                    podcast = asyncio.run(
                        self.generate_podcast()
                    )
                    article.podcast = podcast
                    session.merge(article)
                    self.logger.info(
                            f"Successfully processed content for article: {article.title}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error processing article {article.title}: {str(e)}"
                        )
            else:
                self.logger.info(f"Article has already been processed: {article.title}")

            try:
                session.commit()
                self.logger.info("Successfully committed changes to the database")
            except Exception as e:
                self.logger.error(f"Error committing changes to the database: {str(e)}")

        self.logger.info("PodcastGeneratorAgent run completed")

    @observe
    def evaluate(self):
        self.logger.info("Starting PodcastGeneratorAgent evaluate")

if __name__ == "__main__":
    logger = get_logger("podcast_generator_agent")
    # Parse command-line arguments
    parser = ArgumentParser(description="Podcast Generator Agent")
    parser.add_argument("--id", help="Article ID to process")
    args = parser.parse_args()

    article_id = args.id

    logger.info(f"Processing article_id: {article_id}")
    db_manager = DatabaseManager()
    articles = db_manager.get_articles_by_field("id", article_id)
    logger.info(f"Found {len(articles)} articles to process")
    for article in articles:
        transcript = json.loads(article.content)["transcript"]
        summary = json.loads(article.content)["main"]["summary"]
        explanation = json.loads(article.content)["main"]["explanation"]
        agent = PodcastGeneratorAgent(PODCAST_GENERATOR_PROMPT.format(
            transcript=transcript, summary=summary, explanation=explanation))
        agent.run(article_id=article.id)

