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
    logger.info(f'Setting {feature_id} {operation} to {value}')
        
    if feature_id == None or len(feature_id) < 3:
        raise BadInputError(f'Invalid feature id: {feature_id}')
            
    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiJhZTIxOTU1N2M0ZjI0NmYyZWQ4YSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2MzEzMzg4NzQsImlhdCI6MTYzMTMwMjg3NCwic2NvcGUiOiJsd3B1YmxpYyJ9.Yo_yeoxYB9bULfmzPFMhWPrBm13yCl_YEm5jTj5SBd2-pUiDV4zSMEOLis_voWjdLJaI1DIxlIJMN2nreB3x-VNRH9TOgnuqSdAScWUwBdXf9W65kiZcGl78KhFvy9Q7xDSDeV8slbtZKFOVsuK9w5SFcciUd3tQFWc7l3couqbDSP81hhT6EDh3Uvb3cCxVqJA0h5F63y_H27J-gLJ9obcXzLQWRJCZTLp4WRX-LGJi4MV1zmNDhhbBx-Vsd_g8f_YQNnMnrzw0394IoNX9DWuEMbP_-9aHuQYDnd44WQGNm_TWaQlBL2P4M-6sbekc3iW5f26npRxZBzlv_EgYE9EyRzTBQdKMdjQj-V9HvpLv9DRYa3eQBtPxZSLbO3pOnB5iHNO7fK8D71f-NPH_jhE9dPzcgz32HzQlWeCfr4D1YCIRM3Z4BlDE5xX0Y8yA5_2pqx7knMIE8DDd-oNjiYOIoUpVq5Fga443yMRzWoKgwLeOIwCz6RxQ_AS46W9AGDLtXPyM9lcxXT6y2iK1qW1rh1JYZ-djtP3BuRQsl3oEogywEzpiiCA03325u3isSsb5UxTSSbkxd_FN9KHDBVjn-lphiNMQqJTEPevZwJa3QIuqD22d8CViX9pR8TXiC0agQyaY6aRZZG-UqME0HfvYuNQJqsIvtzwhsDlWnW8',
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
