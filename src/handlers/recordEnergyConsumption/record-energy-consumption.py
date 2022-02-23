import logging
import requests
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.resource('cloudwatch')
secrets_manager = boto3.client('secretsmanager', endpoint_url=os.environ['SecretsManagerEndpoint'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

current_power_usage_metric = cloudwatch.Metric('incandescent_device_energy','current_power_usage')
energy_usage_metric = cloudwatch.Metric('incandescent_device_energy','energy_usage')

def lambda_handler(event, context):
    record_energy_consumption()
    
def record_energy_consumption():
    access_token = secrets_manager.get_secret_value(SecretId=os.environ['AccessTokenArn']).get('SecretString')

    # Scan device table
    table = dynamodb.Table(os.environ['DeviceTableName'])

    response = table.scan()
    devices = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        devices.extend(response['Items'])

    for device in devices:
        try:
            device_name = device['deviceName']

            # Update energy values
            current_power_value = get_feature_value(access_token, device['currentPowerId'])
            energy_usage_value = get_feature_value(access_token, device['energyUsageId'])
            # TODO: Store hourly/weekly/monthly/yearly reset metrics in a DB and aggregate for the metric value
            update_current_power_usage(device_name, current_power_value)
            update_energy_usage(device_name, energy_usage_value)
        except ClientError:
            logger.error(f'Server error while processing device {device["deviceName"]}', exc_info=1)
        except Exception:
            logger.error(f'Could not process device {device["deviceName"]}', exc_info=1)

def update_current_power_usage(device_name, current_power_value):
    current_power_usage_metric.put_data(
        MetricData=[
            {
                'MetricName': current_power_usage_metric.metric_name,
                'Value': current_power_value,
                'Unit': 'W',
                'Dimensions': [
                    { 'Name': 'device_name', 'Value': device_name }
                ]
            }
        ]
    )

def update_energy_usage(device_name, energy_usage_value):
    energy_usage_metric.put_data(
        MetricData=[
            {
                'MetricName': energy_usage_metric.metric_name,
                'Value': energy_usage_value,
                'Unit': 'Wh',
                'Dimensions': [
                    { 'Name': 'device_name', 'Value': device_name }
                ]
            }
        ]
    )

def get_feature_value(access_token, feature_id):
    logger.debug(f'Getting feature value for {feature_id}')

    headers = {
        'authorization': 'bearer %s' % access_token,
        'content-type': 'application/json'
    }
    r = requests.get(f'https://publicapi.lightwaverf.com/v1/feature/{feature_id}', headers=headers)
    result_body = r.json()['value']
    
    if r.status_code == 400:
        raise BadInputError(result_body.get('message') if 'message' in result_body else 'Invalid request body')
    elif r.status_code >= 401:
        logger.error(result_body)
        raise Exception(result_body.get('message') if 'message' in result_body else '')
    return result_body
