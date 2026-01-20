import logging
import sys
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger that writes to stderr (to avoid interfering with MCP stdout communication).
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # MCP servers communicate via stdout, so logs MUST go to stderr
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
