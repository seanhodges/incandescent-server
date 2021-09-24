import json
import logging
import requests
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.resource('sqs')

def lambda_handler(event, context):
    process_devices()
    
def process_devices():
    # Load latest structure, zones and rooms 
    home_id = get_top_level_structure_id()
    structure = get_structure_for_id(home_id)
    room_groups = get_by_group_type('rooms')
    zone_groups = get_by_group_type('zones')
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

def get_top_level_structure_id():
    logger.info(f'Getting top level structure id')

    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiIxYTRhMzVkNTE4NTFiYmY4MTU3ZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2MzI1NTIyNTUsImlhdCI6MTYzMjUxNjI1NSwic2NvcGUiOiJsd3B1YmxpYyJ9.qE1XgvaAM8LhFTtGWi-WXtO4COgoWwort7nRa1TQsyyFNFc2fOi8-bXcZV67_oKonLAmu0zTZYHoB-FRmcnpbtja25ightujKpJ_-ANda71Gq1x8vG7Vmbuvd_sjpAHJLLaY1J8uidDZqd6kdQUU-Zj1nfBWTuOD2WySyMxt2xTu6gU3eeKFRgugJNlV291Nyd4EnQnsFDoXSl_h46Ax6nmn_Kvc4OQOANyyBgNeMAzjk08-hNnkAmAAqSPqjkCGROtOLlyVrluvh9AazUhZYH9bGAtWdEtcsAv6Wc2tc5jImwwbKitnUO_l3S24mkK-WBKUXp8q3OrTB5CXH8abUJ3n6XxlOhtBX0iEPule4uuEB5GPhDF06LqglohkToYynfAo915aL93GUWAjXuFEJugHhEdBmOUrAamxjaS-WEtiOdINzDO6ddGpIqdAs8XmJYI6Op-3sfuGWt2xBywIhu_xvIDhDMBC3Z4P1HD0T3upf3vnMAiTZ7vDCAMTKMSZKj3jnbO73tj2IRSMkrU2MuI0HnPwBXVBfL1a4CpmGamyDHMHokX8VkHRceAZCol3eCuz5ArKL-2BNQAbFPBP7Yy4UnJAXR5gg1Fqg7JbHuLB5A21cr63OG7wg-SwG8O8kfFWEJ0pfIHz-vrX3IJcOuvwh3FkIl8JF0M0elJRFqE',
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

def get_structure_for_id(structure_id):
    logger.info(f'Getting structure for {structure_id}')

    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiIxYTRhMzVkNTE4NTFiYmY4MTU3ZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2MzI1NTIyNTUsImlhdCI6MTYzMjUxNjI1NSwic2NvcGUiOiJsd3B1YmxpYyJ9.qE1XgvaAM8LhFTtGWi-WXtO4COgoWwort7nRa1TQsyyFNFc2fOi8-bXcZV67_oKonLAmu0zTZYHoB-FRmcnpbtja25ightujKpJ_-ANda71Gq1x8vG7Vmbuvd_sjpAHJLLaY1J8uidDZqd6kdQUU-Zj1nfBWTuOD2WySyMxt2xTu6gU3eeKFRgugJNlV291Nyd4EnQnsFDoXSl_h46Ax6nmn_Kvc4OQOANyyBgNeMAzjk08-hNnkAmAAqSPqjkCGROtOLlyVrluvh9AazUhZYH9bGAtWdEtcsAv6Wc2tc5jImwwbKitnUO_l3S24mkK-WBKUXp8q3OrTB5CXH8abUJ3n6XxlOhtBX0iEPule4uuEB5GPhDF06LqglohkToYynfAo915aL93GUWAjXuFEJugHhEdBmOUrAamxjaS-WEtiOdINzDO6ddGpIqdAs8XmJYI6Op-3sfuGWt2xBywIhu_xvIDhDMBC3Z4P1HD0T3upf3vnMAiTZ7vDCAMTKMSZKj3jnbO73tj2IRSMkrU2MuI0HnPwBXVBfL1a4CpmGamyDHMHokX8VkHRceAZCol3eCuz5ArKL-2BNQAbFPBP7Yy4UnJAXR5gg1Fqg7JbHuLB5A21cr63OG7wg-SwG8O8kfFWEJ0pfIHz-vrX3IJcOuvwh3FkIl8JF0M0elJRFqE',
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

def get_by_group_type(group_type):
    logger.info(f'Getting {group_type} groups')

    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiIxYTRhMzVkNTE4NTFiYmY4MTU3ZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2MzI1NTIyNTUsImlhdCI6MTYzMjUxNjI1NSwic2NvcGUiOiJsd3B1YmxpYyJ9.qE1XgvaAM8LhFTtGWi-WXtO4COgoWwort7nRa1TQsyyFNFc2fOi8-bXcZV67_oKonLAmu0zTZYHoB-FRmcnpbtja25ightujKpJ_-ANda71Gq1x8vG7Vmbuvd_sjpAHJLLaY1J8uidDZqd6kdQUU-Zj1nfBWTuOD2WySyMxt2xTu6gU3eeKFRgugJNlV291Nyd4EnQnsFDoXSl_h46Ax6nmn_Kvc4OQOANyyBgNeMAzjk08-hNnkAmAAqSPqjkCGROtOLlyVrluvh9AazUhZYH9bGAtWdEtcsAv6Wc2tc5jImwwbKitnUO_l3S24mkK-WBKUXp8q3OrTB5CXH8abUJ3n6XxlOhtBX0iEPule4uuEB5GPhDF06LqglohkToYynfAo915aL93GUWAjXuFEJugHhEdBmOUrAamxjaS-WEtiOdINzDO6ddGpIqdAs8XmJYI6Op-3sfuGWt2xBywIhu_xvIDhDMBC3Z4P1HD0T3upf3vnMAiTZ7vDCAMTKMSZKj3jnbO73tj2IRSMkrU2MuI0HnPwBXVBfL1a4CpmGamyDHMHokX8VkHRceAZCol3eCuz5ArKL-2BNQAbFPBP7Yy4UnJAXR5gg1Fqg7JbHuLB5A21cr63OG7wg-SwG8O8kfFWEJ0pfIHz-vrX3IJcOuvwh3FkIl8JF0M0elJRFqE',
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