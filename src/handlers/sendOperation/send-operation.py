import json
import logging
import requests
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BadInputError(Exception):
    pass

def lambda_handler(event, context):
    try:
        device_ref = event.get('deviceRef')
        operation = event.get('operation')
        value = event.get('value')
    
        return toggle_switch(device_ref, operation, value)
    except BadInputError as e:
        api_error = {
            'errorType': e.__class__.__name__,
            'errorMessage': str(e)
        }
        raise Exception(json.dumps(api_error))
    
def toggle_switch(device_ref, operation, value):
    feature_id = find_feature(device_ref, operation)
    # '5b8aa9b4d36c330fd5b4e100-320-3157332334%2B1' # TODO: lookup the feature from the device and operation
    logger.info(f'Setting {feature_id} {operation} to {value}')
        
    if feature_id == None or len(feature_id) < 3:
        raise BadInputError(f'Invalid feature id: {feature_id}')
            
    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiIxYTRhMzVkNTE4NTFiYmY4MTU3ZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2MzI1NTIyNTUsImlhdCI6MTYzMjUxNjI1NSwic2NvcGUiOiJsd3B1YmxpYyJ9.qE1XgvaAM8LhFTtGWi-WXtO4COgoWwort7nRa1TQsyyFNFc2fOi8-bXcZV67_oKonLAmu0zTZYHoB-FRmcnpbtja25ightujKpJ_-ANda71Gq1x8vG7Vmbuvd_sjpAHJLLaY1J8uidDZqd6kdQUU-Zj1nfBWTuOD2WySyMxt2xTu6gU3eeKFRgugJNlV291Nyd4EnQnsFDoXSl_h46Ax6nmn_Kvc4OQOANyyBgNeMAzjk08-hNnkAmAAqSPqjkCGROtOLlyVrluvh9AazUhZYH9bGAtWdEtcsAv6Wc2tc5jImwwbKitnUO_l3S24mkK-WBKUXp8q3OrTB5CXH8abUJ3n6XxlOhtBX0iEPule4uuEB5GPhDF06LqglohkToYynfAo915aL93GUWAjXuFEJugHhEdBmOUrAamxjaS-WEtiOdINzDO6ddGpIqdAs8XmJYI6Op-3sfuGWt2xBywIhu_xvIDhDMBC3Z4P1HD0T3upf3vnMAiTZ7vDCAMTKMSZKj3jnbO73tj2IRSMkrU2MuI0HnPwBXVBfL1a4CpmGamyDHMHokX8VkHRceAZCol3eCuz5ArKL-2BNQAbFPBP7Yy4UnJAXR5gg1Fqg7JbHuLB5A21cr63OG7wg-SwG8O8kfFWEJ0pfIHz-vrX3IJcOuvwh3FkIl8JF0M0elJRFqE',
        'content-type': 'application/json'
    }
    r = requests.post(f'https://publicapi.lightwaverf.com/v1/feature/{feature_id}', json={'value': value}, headers=headers)
    result_body = r.json()
    
    if r.status_code == 400:
        raise BadInputError(result_body.get('message') if 'message' in result_body else 'Invalid request body')
    elif r.status_code >= 401:
        logger.error(result_body)
        raise Exception(result_body.get('message') if 'message' in result_body else '')
    return result_body

def find_feature(device_ref, operation):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('test-stack-DeviceTable-MGKXW4KKJRMR')
    response = table.query(
        KeyConditionExpression = Key('userId').eq('seanhodges') & Key('deviceRef').eq(device_ref)
    )
    return response['Items'][0][operation + 'Id']
