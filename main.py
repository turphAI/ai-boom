"""
Main entry point for the Boom-Bust Sentinel system.
"""

import logging
import sys
from typing import List

from config.settings import settings


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('boom_bust_sentinel.log')
        ]
    )


def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Boom-Bust Sentinel")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize alert service to show configured channels
    from services.alert_service import AlertService
    alert_service = AlertService()
    channel_names = [c.get_channel_name() for c in alert_service.channels]
    logger.info(f"Alert channels configured: {', '.join(channel_names)}")
    
    # TODO: Add scraper execution logic in future tasks
    logger.info("System initialized successfully")


if __name__ == "__main__":
    main()