from argparse import ArgumentParser


class BaseAgent:
    def __init__(self, system_prompt):
        self.message_history = [{"role": "system", "content": system_prompt}]
        self.args = self.parse_arguments()

    def add_message(self, message):
        self.message_history.append(message)

    def get_message_history(self):
        return self.message_history

    @classmethod
    def parse_arguments(cls):
        parser = ArgumentParser(description=f"Arguments for {cls.__name__}")
        cls.add_arguments(parser)
        return parser.parse_args()

    @classmethod
    def add_arguments(cls, parser):
        # Add common arguments here
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )

    def run(self):
        raise NotImplementedError("Subclasses must implement run method")
