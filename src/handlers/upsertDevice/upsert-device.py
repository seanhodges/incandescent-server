import json
import logging
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

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
    identify_id = get_feature_attrs(feature_set_data, 'identify')
    protection_id = get_feature_attrs(feature_set_data, 'protection')
    switch_id = get_feature_attrs(feature_set_data, 'switch')
    dim_level_id = get_feature_attrs(feature_set_data, 'dimLevel')

    # TODO: Fetch the current table name
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
            'identifyId': identify_id,
            'protectionId': protection_id,
            'switchId': switch_id,
            'dimLevelId': dim_level_id,
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

def get_feature_attrs(data, feature_type):
    search = filter(lambda feature: (feature['type'] == feature_type), data['features'])
    match = next(search, None)
    if match == None:
        return None
    return match['featureId']

def generate_device_ref(zone_name, room_name, device_name, feature_set_name):
    normalise = lambda name: '-'.join(name.split()).lower()
    return '/'.join([
        normalise(zone_name), 
        normalise(room_name), 
        normalise(device_name), 
        normalise(feature_set_name)
        ])