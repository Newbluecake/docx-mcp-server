import logging
import traceback


class StackTraceFormatter(logging.Formatter):
    """Custom formatter that adds call stack to ERROR level logs."""

    def format(self, record):
        result = super().format(record)

        # Add call stack for ERROR level logs without exception info
        if record.levelno >= logging.ERROR and not record.exc_info:
            stack = ''.join(traceback.format_stack()[:-2])  # Exclude formatter frames
            result += f'\nCall Stack:\n{stack}'

        return result
