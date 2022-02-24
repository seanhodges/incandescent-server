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

    response = table.scan(
        FilterExpression='attribute_exists(currentPowerId) OR attribute_exists(energyUsageId)',
        ProjectionExpression='deviceRef,deviceName,currentPowerId,energyUsageId'
    )
    devices = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression='attribute_exists(currentPowerId) OR attribute_exists(energyUsageId)',
            ProjectionExpression='deviceRef,deviceName,currentPowerId,energyUsageId',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        devices.extend(response['Items'])

    logger.info(f'Found {len(devices)} devices with energy stats')

    for device in devices:
        update_metrics(access_token, device)


def update_metrics(access_token, device):
        try:
            metric_data = []
            device_name = device['deviceName']
            device_ref = device['deviceRef']
            
            logger.info(f'Recording energy stats for {device_ref}')

            # Update energy values
            # TODO: Store hourly/weekly/monthly/yearly reset metrics in a DB and aggregate for the metric value
            if device['currentPowerId']:
                current_power_value = get_feature_value(access_token, device['currentPowerId'])
                metric_data.append({
                        'MetricName': current_power_usage_metric.metric_name,
                        'Value': current_power_value,
                        'Dimensions': [
                            { 'Name': 'device_name', 'Value': device_name },
                            { 'Name': 'device_ref', 'Value': device_ref }
                        ]
                })

            if device['energyUsageId']:
                energy_usage_value = get_feature_value(access_token, device['energyUsageId'])
                metric_data.append({
                    'MetricName': energy_usage_metric.metric_name,
                    'Value': energy_usage_value,
                    'Dimensions': [
                        { 'Name': 'device_name', 'Value': device_name },
                        { 'Name': 'device_ref', 'Value': device_ref }
                    ]
                })
            
            if len(metric_data) > 0:
                energy_usage_metric.put_data(MetricData=metric_data)
        except ClientError:
            logger.error(f'Server error while processing device {device["deviceRef"]}', exc_info=1)
        except Exception:
            logger.error(f'Could not process device {device["deviceRef"]}', exc_info=1)


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
