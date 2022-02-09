import json
import logging
import requests
import boto3
import os
from botocore.exceptions import ClientError

sqs = boto3.resource('sqs')
secrets_manager = boto3.client('secretsmanager', endpoint_url=os.environ['SecretsManagerEndpoint'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    process_devices()
    
def process_devices():
    access_token = secrets_manager.get_secret_value(SecretId=os.environ['AccessTokenArn']).get('SecretString')

    # Load latest structure, zones and rooms
    home_id = get_top_level_structure_id(access_token)
    structure = get_structure_for_id(access_token, home_id)
    room_groups = get_by_group_type(access_token, 'rooms')
    zone_groups = get_by_group_type(access_token, 'zones')
    # Parse each device in the structure
    for device in structure['devices']:
        # Process each feature set in the device
        for feature_set in device['featureSets']:
            # Get the room for the feature set (match on featureSetId)
            room_group = list(filter(lambda r, fsi=feature_set['featureSetId']: fsi in r["featureSets"], room_groups))[0]
            # Get the zone for the room (match on room groupId)
            zone_group = list(filter(lambda z, rg=room_group['groupId']: rg in z["rooms"], zone_groups['zone']))[0]
            # Publish SQS message with device, room, and zone data
            publish_to_sqs(device, feature_set, room_group, zone_group)

def get_top_level_structure_id(access_token):
    logger.info(f'Getting top level structure id')

    headers = {
        'authorization': 'bearer %s' % access_token,
        'content-type': 'application/json'
    }
    r = requests.get(f'https://publicapi.lightwaverf.com/v1/structures', headers=headers)
    result_body = r.json()
    
    if r.status_code == 400:
        raise BadInputError(result_body.get('message') if 'message' in result_body else 'Invalid request body')
    elif r.status_code >= 401:
        logger.error(result_body)
        raise Exception(result_body.get('message') if 'message' in result_body else '')
    return result_body['structures'][0] # Assuming one home for now

def get_structure_for_id(access_token, structure_id):
    logger.info(f'Getting structure for {structure_id}')

    headers = {
        'authorization': 'bearer %s' % access_token,
        'content-type': 'application/json'
    }
    r = requests.get(f'https://publicapi.lightwaverf.com/v1/structure/{structure_id}', headers=headers)
    result_body = r.json()
    
    if r.status_code == 400:
        raise BadInputError(result_body.get('message') if 'message' in result_body else 'Invalid request body')
    elif r.status_code >= 401:
        logger.error(result_body)
        raise Exception(result_body.get('message') if 'message' in result_body else '')
    return result_body

def get_by_group_type(access_token, group_type):
    logger.info(f'Getting {group_type} groups')

    headers = {
        'authorization': 'bearer %s' % access_token,
        'content-type': 'application/json'
    }
    r = requests.get(f'https://publicapi.lightwaverf.com/v1/{group_type}', headers=headers)
    result_body = r.json()
    
    if r.status_code == 400:
        raise BadInputError(result_body.get('message') if 'message' in result_body else 'Invalid request body')
    elif r.status_code >= 401:
        logger.error(result_body)
        raise Exception(result_body.get('message') if 'message' in result_body else '')
    return result_body

def get_sqs_queue(name):
    try:
        queue = sqs.get_queue_by_name(QueueName=name)
        logger.info(f'Got queue {name} at {queue.url}')
    except ClientError as error:
        logger.error(f'No queue named {name}')
        raise error
    else:
        return queue

def publish_to_sqs(device, feature_set, room_group, zone_group):
    # TODO: Fetch the current queue name
    queue = get_sqs_queue('test-stack-DeviceReceivedQueue-Q5E7XGQ2YQ9R')
    try:
        message = {
            'zoneData': zone_group,
            'roomData': room_group,
            'deviceData': device,
            'featureSetData': feature_set,
        }
        queue.send_message(MessageBody=json.dumps(message))
    except ClientError as error:
        logger.error(f'Failed to send message to queue {queue.url}')
        raise error