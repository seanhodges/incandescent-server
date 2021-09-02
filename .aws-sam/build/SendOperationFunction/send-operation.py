import json
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BadInputError(Exception):
    pass

def lambda_handler(event, context):
    try:
        device = event.get('device') # TODO: lookup the feature from the device and operation
        operation = event.get('operation')
        value = event.get('value')
    
        return toggle_switch(device, operation, value)
    except BadInputError as e:
        api_error = {
            'errorType': e.__class__.__name__,
            'errorMessage': str(e)
        }
        raise Exception(json.dumps(api_error))
    
def toggle_switch(device, operation, value):
    logger.info(f'Setting {device} {operation} to {value}')
    feature_id = device # TODO: lookup the feature from the device and operation
        
    if feature_id == None or len(feature_id) < 3:
        raise BadInputError(f'Invalid feature id: {feature_id}')
            
    headers = {
        'authorization': 'bearer eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiI0NmFiOWY2ZTc1OWFkZmUxOTEyYSIsImlzcyI6Imh0dHBzOi8vYXV0aC5saWdodHdhdmVyZi5jb20iLCJzdWIiOiJjNTJiNDA4MS00MTA5LTQ4MTctOTE1NS1jNmY1YjBmMjdlYWQiLCJhdWQiOiI0OWQ2N2NmZC00YzVjLTQ5MDQtYjcyNi04NWFjMzRhYmY2ODAiLCJleHAiOjE2Mjk3NjMzMzQsImlhdCI6MTYyOTcyNzMzNCwic2NvcGUiOiJsd3B1YmxpYyJ9.zdr9pqGlU46lDeYdZALY9K6LgH_A8wJwL6P2FOxSduw59ay-bCpun8NKnSqshkt_LUVYnpepm5GrhiQ_9-lr0vAN9x83EDO87SRETN-UtBnjBoMAQ2gkOHeRhyBNAaZpMOlk9huip9aiAOa7DzjYQJxgj5PA2VDCVxTLZ8T4icX6HEfcHF5-thEh-Tf1YLZImISqTpTkQjYQeqMgurWeFhgIfKJDg6U5_RHrdt7BHoLjBwTN83BD7vSmGqKv0lzwB0L2IDghbCfRfe3updCihx3nBI26TXb6bRvUOZxCi1jZXq8mdVAmaFrJ5PZO5RlxZilaXTtcdssEXIGIlyNIxS7sNAw7QBgQNw9B7yaG5KcP7LMpEeApgDw65NkhFqlIf2uknF9_Q3ZN746PAVwKeAV_KL83GvS-S1M-iAORYhav1cSNnp4ubu1kdFqQWjsdRAVfNDa8h9xwr0W3mQp0T5QGndbiQDH08IpQl4R1u7e3p8rxyZ2caD3CEJ31bH0dU6p3PCGjv0zl3yzx0fKD3c3ulkRm5SJCZWM4fPXl_ky3FBTciM9jU8cPTTPQ4GpOtNOt3KLXlhcSBlD_Ls2anB3EckciLh45VgIrHX1ile4fuzroqU_ueid95nZ-vCZee_m3j__BGyuSgfvB_9tlOHTzWNyJtRkKBJqGdqX8hEw',
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
