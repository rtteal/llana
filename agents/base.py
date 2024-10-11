from argparse import ArgumentParser
from langfuse.decorators import observe

class BaseAgent:
    def __init__(self, system_prompt):
        self.message_history = [{"role": "system", "content": system_prompt}]

    def add_message(self, message):
        self.message_history.append(message)

    def get_message_history(self):
        return self.message_history

    @observe
    def run(self):
        raise NotImplementedError("Subclasses must implement run method")
