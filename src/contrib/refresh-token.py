import requests
import json

url = 'https://auth.lightwaverf.com/token'
values = {
  'grant_type': 'refresh_token', 
  'refresh_token': '<Initial refresh token>'
}

headers = {
  'authorization': 'basic <Client Auth Token>',
  'content-type': 'application/json'
}
response = requests.post(url, json=values, headers=headers)

print(response.json())