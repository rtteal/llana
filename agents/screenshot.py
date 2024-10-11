import asyncio
import argparse
import os
import sys

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
from utils.prompts import SCREENSHOT_PROMPT, SCREENSHOT_EVAL_PROMPT
from database.main import DatabaseManager
from database.models.article import Article
from utils.logger import get_logger


class ScreenshotAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)
        self.logger = get_logger("screenshot_agent")
        self.llm = LLM(temperature=0.1, max_tokens=5500)
        self.db_manager = DatabaseManager()
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET"),
            public_key=os.getenv("LANGFUSE_PUBLIC"),
            host=os.getenv("LANGFUSE_HOST"),
        )

    async def read_screenshot(self, path):
        return await self.llm.read_image(self.get_message_history(), path)

    @observe
    def run(self, article_id=None):
        langfuse_context.update_current_trace(tags=["screenshot_agent_run"])
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
                        content = asyncio.run(
                            self.read_screenshot(article.screenshot_path)
                        )
                        article.content = content
                        session.merge(article)
                        self.logger.info(
                            f"Successfully processed content for article: {article.title}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error processing article {article.title}: {str(e)}"
                        )
                else:
                    self.logger.info(f"Article already has content: {article.title}")

            try:
                session.commit()
                self.logger.info("Successfully committed changes to the database")
            except Exception as e:
                self.logger.error(f"Error committing changes to the database: {str(e)}")

        self.logger.info("ScreenshotAgent run completed")

    @observe
    def evaluate(self):
        self.logger.info("Starting ScreenshotAgent evaluate")
        langfuse_context.update_current_trace(tags=["screenshot_agent_evaluate"])
        now = datetime.now()
        # Get traces from 5am yesterday to now()
        five_am_today = datetime(now.year, now.month, now.day, 5, 0)
        five_am_yesterday = five_am_today - timedelta(days=1)
        self.logger.info(
            f"Fetching traces from {five_am_yesterday} to {datetime.now()}"
        )
        # Fetch traces, target traces with tags screenshot_agent
        traces = self.langfuse.fetch_traces(
            limit=100,
            tags=["screenshot_agent"],
            from_timestamp=five_am_yesterday,
            to_timestamp=datetime.now(),
        ).data
        self.logger.info(f"Traces fetched: {len(traces)}")
        # Evaluate each trace
        for trace in traces:
            self.logger.info(f"Evaluating trace: {trace.id}")
            agent = EvaluateAgent(SCREENSHOT_EVAL_PROMPT)
            observation = self.langfuse.get_observation(trace.observations[0])
            self.logger.info(f"Adding observation for evaluation: {observation.id}")
            agent.add_message(
                {"role": "user", "content": observation.output["content"]}
            )
            is_valid = agent.run(trace_id=trace.id)
            self.logger.info(f"Evaluation result: {is_valid}")


if __name__ == "__main__":
    logger = get_logger("screenshot_agent")
    # Parse command-line arguments
    parser = ArgumentParser(description="Screenshot Agent")
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD)")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation mode")
    args = parser.parse_args()

    # Get the day from --date argument or use current date
    day = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    evaluate = args.evaluate

    if evaluate:
        logger.info("Running trace evaluation mode.")
        agent = ScreenshotAgent(SCREENSHOT_PROMPT)
        agent.evaluate()
    else:
        logger.info(f"Processing day: {day}")
        db_manager = DatabaseManager()
        articles = db_manager.get_articles_by_field("day", day)
        logger.info(f"Found {len(articles)} articles to process")
        for article in articles:
            agent = ScreenshotAgent(SCREENSHOT_PROMPT)
            agent.run(article_id=article.id)
