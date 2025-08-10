"""Simple test handler to verify deployment works."""

import json
import logging

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """Simple test handler."""
    logger.info("Test handler called successfully")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Test handler working',
            'event': event,
            'aws_request_id': getattr(context, 'aws_request_id', 'unknown')
        })
    }