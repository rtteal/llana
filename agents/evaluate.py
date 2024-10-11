import asyncio
import os
import json
import sys
from typing import List

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from base import BaseAgent
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.prompts import SCREENSHOT_EVAL_PROMPT
from utils.llm import LLM
from utils.logger import get_logger

load_dotenv()

BATCH_SIZE = 10
TOTAL_TRACES = 50

langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET"),
    public_key=os.getenv("LANGFUSE_PUBLIC"),
    host=os.getenv("LANGFUSE_HOST"),
)


class EvaluateAgent(BaseAgent):
    def __init__(self, system_prompt):
        super().__init__(system_prompt)
        self.message_history = [{"role": "system", "content": system_prompt}]
        self.llm = LLM(temperature=0.1, max_tokens=100)
        self.logger = get_logger("evaluate_agent")

    @observe
    def run(self, trace_id):
        self.logger.info(f"Running agent for trace_id: {trace_id}")
        try:
            # Tag the trace with the agent name
            langfuse_context.update_current_trace(tags=["evaluate"])
            # Evaluate the trace response
            self.logger.info("Getting LLM response")
            response = asyncio.run(
                self.llm.get_llm_response_stream(self.message_history)
            )
            self.logger.info(f"LLM response: {response}")
            # Score the trace
            langfuse.score(trace_id=trace_id, name="is_valid", value=response)
            return response
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return "An error occurred"
