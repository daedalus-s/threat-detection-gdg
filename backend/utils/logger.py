from loguru import logger
import sys

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file logging
logger.add(
    "logs/threat_detection_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

def get_logger(name: str):
    """Get a logger instance with a specific name"""
    return logger.bind(name=name)