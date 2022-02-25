import logging
import requests
import boto3
import os

secrets_manager = boto3.client('secretsmanager', endpoint_url=os.environ['SecretsManagerEndpoint'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']
    process_command(arn, token, step)

def process_command(arn, token, step):
    metadata = secrets_manager.describe_secret(SecretId=arn)
    if not metadata['RotationEnabled']:
        logger.error(f'Secret {arn} is not enabled for rotation')
        raise ValueError(f'Secret {arn} is not enabled for rotation')
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error(f'Secret version {token} has no stage for rotation of secret {arn}.')
        raise ValueError(f'Secret version {token} has no stage for rotation of secret {arn}.')
    if 'AWSCURRENT' in versions[token]:
        logger.info(f'Secret version {token} already set as AWSCURRENT for secret {arn}.')
        return
    elif 'AWSPENDING' not in versions[token]:
        logger.error(f'Secret version {token} not set as AWSPENDING for rotation of secret {arn}.')
        raise ValueError(f'Secret version {token}s not set as AWSPENDING for rotation of secret {arn}.')

    if step == 'createSecret':
        return create_secret(secrets_manager, arn, token)
    elif step == 'finishSecret':
        return finish_secret(secrets_manager, arn, token)
    elif step in ['setSecret', 'testSecret']:
        return # NOOP
    else:
        raise ValueError(f'Invalid step parameter: {step}')

def create_secret(secrets_manager, arn, token):
    # Make sure the current secret exists
    secrets_manager.get_secret_value(SecretId=arn, VersionStage='AWSCURRENT')

    # Now try to get the secret version, if that fails, update the secrets
    try:
        secrets_manager.get_secret_value(SecretId=arn, VersionId=token, VersionStage='AWSPENDING')
        logger.info(f'createSecret: Successfully retrieved secret for {arn}')
    except secrets_manager.exceptions.ResourceNotFoundException:
        client_auth_token = secrets_manager.get_secret_value(SecretId=os.environ['ClientAuthTokenArn']).get('SecretString')
        refresh_token = secrets_manager.get_secret_value(SecretId=os.environ['RefreshTokenArn']).get('SecretString')
        new_secrets = refresh_tokens(client_auth_token, refresh_token)

        # Update both the access token (versioned) and the refresh token
        secrets_manager.put_secret_value(SecretId=arn, ClientRequestToken=token, SecretString=new_secrets['access_token'], VersionStages=['AWSPENDING'])
        secrets_manager.put_secret_value(SecretId=os.environ['RefreshTokenArn'], ClientRequestToken=token, SecretString=new_secrets['refresh_token'])
        logger.info(f'createSecret: Successfully put secret for ARN {arn} and version {token}.')

def refresh_tokens(client_auth_token, refresh_token):
    url = 'https://auth.lightwaverf.com/token'
    values = {
        'grant_type': 'refresh_token', 
        'refresh_token': refresh_token
    }

    headers = {
        'authorization': f'basic {client_auth_token}',
        'content-type': 'application/json'
    }
    response = requests.post(url, json=values, headers=headers)
    return response.json()

def finish_secret(secrets_manager, arn, token):
    # First describe the secret to get the current version
    metadata = secrets_manager.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata['VersionIdsToStages']:
        if 'AWSCURRENT' in metadata['VersionIdsToStages'][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info(f'finishSecret: Version {version} already marked as AWSCURRENT for {arn}')
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    secrets_manager.update_secret_version_stage(SecretId=arn, VersionStage='AWSCURRENT', MoveToVersionId=token, RemoveFromVersionId=current_version)
    logger.info(f'finishSecret: Successfully set AWSCURRENT stage to version {token} for secret {arn}.')