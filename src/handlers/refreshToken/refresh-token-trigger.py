import logging
import boto3
import os

secrets_manager = boto3.client('secretsmanager', endpoint_url=os.environ['SecretsManagerEndpoint'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    secret_id = os.environ['SecretId']
    rotation_lambda_arn = os.environ['RotationLambdaARN']
    logger.info(f'Rotating secret {secret_id}')
    secrets_manager.rotate_secret(
        SecretId=secret_id,
        RotationLambdaARN=rotation_lambda_arn
    )
