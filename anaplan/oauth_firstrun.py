"""
Anaplan Integration Python Library - oauth_firstrun.py

Module to capture refresh token for OAuth verification

"""

from time import sleep
import json
import requests
from dotenv import set_key


def oauth_device_firstrun(client_id, file_env):
    """
    Anaplan Integration Python Library - oauth_firstrun.py

    Contains code to make generation of refresh token easy

    Steps:
    1. Enable a Device Code client on Anaplan
    2. Note down the client ID and feed that to this function
    3. Also feed in a dot_env environment file
    4. Run this function and wait for the prompt in terminal
    5. Go the URL https://iam.anaplan.com/activate and input the device code within 60 seconds
    6. Login and this application will be authorized
    7. Note: this application can work ONLY as long as the refresh token remains unexpired, so
    fresh refresh token might need to be generated

    Supports only device code flow

    """

    token_url = 'https://us1a.app.anaplan.com/oauth/device/code'
    header = {'Content-Type' : 'application/json'}

    body = {
        'client_id' : client_id,
        'scope' : 'openid profile email offline_access'
    }

    # give the user 60 seconds to manually authorize the application
    request = requests.post(token_url, headers=header, json=body, timeout=10)
    full_token = json.loads(request.text)
    print(f"Go to this URL in an Incognito/Private and authorize within 60 seconds. \
          Enter this code: {full_token['user_code']} at the prompt")
    print(full_token['verification_uri'])
    sleep(60)

    token_url = 'https://us1a.app.anaplan.com/oauth/token'

    # if successfully authorized, pass the below body to receieve the authentication token
    body = {
        'grant_type' : 'urn:ietf:params:oauth:grant-type:device_code',
        'client_id' : client_id,
        'device_code' : full_token['device_code']
    }


    request = requests.post(token_url, headers = header, json=body, timeout=10)
    j = json.loads(request.text)
    refresh_token = j['refresh_token']
    set_key(file_env, 'client_id', client_id)
    set_key(file_env, 'refresh_token', refresh_token)
    