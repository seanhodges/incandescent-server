import json
import logging
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('Received %s records' % len(event.get('Records')))
    for record_json in event.get('Records'):
        record = json.loads(record_json['body'])
        zone_data = record['zoneData']
        room_data = record['roomData']
        device_data = record['deviceData']
        feature_set_data = record['featureSetData']
        upsert_device(zone_data, room_data, device_data, feature_set_data)
    
def upsert_device(zone_data, room_data, device_data, feature_set_data):
    user_id = 'seanhodges'
    zone_id, zone_name = get_zone_attrs(zone_data)
    room_id, room_name = get_room_attrs(room_data)
    device_id, device_name, device_type = get_device_attrs(device_data)
    feature_set_id, feature_set_name = get_feature_set_attrs(feature_set_data)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('test-stack-DeviceTable-MGKXW4KKJRMR')
    table.put_item(
       Item={
            'userId': user_id,
            'deviceRef': generate_device_ref(zone_name, room_name, device_name, feature_set_name),
            'zoneName': zone_name,
            'zoneId': zone_id,
            'roomName': room_name,
            'roomId': room_id,
            'deviceName': device_name,
            'deviceType': device_type,
            'deviceId': device_id,
            'featureSetName': feature_set_name,
            'featureSetId': feature_set_id,
        }
    )

def get_zone_attrs(data):
    return data['groupId'], data['name']

def get_room_attrs(data):
    return data['groupId'], data['name']

def get_device_attrs(data):
    return data['deviceId'], data['name'], data['type']

def get_feature_set_attrs(data):
    return data['featureSetId'], data['name']

def generate_device_ref(zone_name, room_name, device_name, feature_set_name):
    normalise = lambda name: '-'.join(name.split()).lower()
    return '/'.join([
        normalise(zone_name), 
        normalise(room_name), 
        normalise(device_name), 
        normalise(feature_set_name)
        ])