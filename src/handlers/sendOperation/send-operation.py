import json
import logging
import requests
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BadInputError(Exception):
    pass

def lambda_handler(event, context):
    secrets_manager = boto3.client('secretsmanager', endpoint_url=os.environ['SecretsManagerEndpoint'])
    access_token = secrets_manager.get_secret_value(SecretId=os.environ['AccessTokenArn']).get('SecretString')

    try:
        device_ref = event.get('deviceRef')
        operation = event.get('operation')
        value = event.get('value')
    
        return toggle_switch(access_token, device_ref, operation, value)
    except BadInputError as e:
        api_error = {
            'errorType': e.__class__.__name__,
            'errorMessage': str(e)
        }
        raise Exception(json.dumps(api_error))
    
def toggle_switch(access_token, device_ref, operation, value):
    feature_id = find_feature(device_ref, operation)
    logger.info(f'Setting {feature_id} {operation} to {value}')
        
    if feature_id == None or len(feature_id) < 3:
        raise BadInputError(f'No matching device for: {device_ref}')
            
    headers = {
        'authorization': 'bearer %s' % access_token,
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
    # TODO: Fetch the current table name
    table = dynamodb.Table('test-stack-DeviceTable-MGKXW4KKJRMR')
    response = table.query(
        KeyConditionExpression = Key('userId').eq('seanhodges') & Key('deviceRef').eq(device_ref)
    )
    
    if len(response['Items']) == 0:
        return None 
    
    return response['Items'][0][operation + 'Id']
