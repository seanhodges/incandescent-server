import json
import logging
import requests
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    process_devices()
    
def process_devices():
    # Load latest structure, zones and rooms 
    # Parse each device in the structure
    # Process each feature set in the device
    # Get the room for the feature set (match on featureSetId)
    # Get the zone for the room (match on room groupId)
    # Publish SQS message with device, room, and zone data
    pass
