"""
Anaplan Integration Python Library - authentication.py

Module creates a Login class and accepts basic, certificate or OAuth2.0 credentials
The login class abstracts away needing to generate tokens separately

"""

import json
from base64 import b64encode
from datetime import datetime, timedelta
import os
import requests
from OpenSSL import crypto
from dotenv import load_dotenv, set_key


class AnaplanAuth:
    """
    Represents a login object for authenticating with the Anaplan platform.

    The `AnaplanAuth` class is used to encapsulate authentication credentials and provide a 
    way to authenticate with the Anaplan API. It securely stores the necessary information for
    authenticating with Anaplan, such as the username, and password and refresh tokens

    Attributes:
        via (str): must be basic, certificate or oauth_refresh
        *creds (str): depending on type of authentication
            basic: provide username and password in un:pw notation
            certificate: provide the public cert and private key files
            oauth_refresh: pass in the dot_env variable

    Example:
        ```python
        login = AnaplanAuth('basic', 'username@company.com:Password123')
        login.get_token()
        ```
    """

    def __init__(self, via, *creds):
        self.via = via
        if via == 'basic':
            self.creds = creds[0]
            self.b64creds = b64encode(
                (self.creds).encode('utf-8')).decode('utf-8')
        elif via == 'certificate':
            self.public = creds[0]
            self.private = creds[1]
        elif via == 'oauth_refresh':
            self.file_env = creds[0]
        self._token = None
        self._expires_at = None

    def get_token(self):
        """
        Function that generates a token based on the class instance
        It also validates the token against the Anaplan validation API
        """

        if self.via == 'basic':
            with requests.post(
                url='https://auth.anaplan.com/token/authenticate',
                headers={'Authorization': 'Basic ' + self.b64creds},
                timeout=10
            ) as req:
                j = json.loads(req.text)
            self._token = self.validate(j)
            self._expires_at = datetime.utcnow() + timedelta(minutes=35)
            return self._token

        elif self.via == 'certificate':
            j = self.cert_token(self.public, self.private)
            self._token = self.validate(j)
            self._expires_at = datetime.utcnow() + timedelta(minutes=35)
            return self._token

        elif self.via == 'oauth_refresh':
            j = self.oauth_refresh(self.file_env)
            self._token = 'AnaplanAuthToken ' + j['access_token']
            self._expires_at = datetime.utcnow() + timedelta(minutes=35)
            return self._token

        else:
            return "Invalid authentication method; please select basic, certificate or oauth type"

    @property
    def token(self):
        """Property of a class instance that gives the token that was generated before"""
        return self._token

    @property
    def expires_at(self):
        """
        Property of a class instance that gives the time the instance's current token expires
        Returns a datetime object. Wrap it around `str` for human readable time
        """
        return self._expires_at

    def refresh(self):
        """
        Function that accepts a still valid token and generates a new token
        Also updates the expires at property
        """
        refresh_url = 'https://auth.anaplan.com/token/refresh'
        header = {'Authorization': self._token}

        request = requests.post(refresh_url, headers=header, timeout=10)
        full_token_json = json.loads(request.text)
        self._token = 'AnaplanAuthToken ' + \
            full_token_json['tokenInfo']['tokenValue']
        self._expires_at = datetime.utcnow() + timedelta(minutes=35)
        return self._token

    @staticmethod
    def cert_token(pub_cert, priv_key):
        """
        Internal Function that accepts a public certificate and private key file
        Requires the OpenSSL library. Passes to API service public certificate value
        And a signed private key based on a random string
        """
        st_cert = open(pub_cert, 'rt').read()
        st_key = open(priv_key, 'rt').read()

        key = crypto.load_privatekey(crypto.FILETYPE_PEM, st_key)
        random_str = os.urandom(100)
        signed_str = crypto.sign(key, random_str, "sha512")

        st_cert = (st_cert.replace("\n", "").replace(
            "-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", ""))

        auth_headers = {'AUTHORIZATION': 'CACertificate ' + st_cert}

        encodedstr = b64encode(random_str)
        signedstr = b64encode(signed_str)

        body = {'encodedData': encodedstr.decode("utf-8"),
                'encodedSignedData': signedstr.decode("utf-8")}

        body = json.dumps(body)

        anaplan_url = 'https://auth.anaplan.com/token/authenticate'
        req = requests.post(
            url=anaplan_url, headers=auth_headers, data=body, timeout=10)
        j = json.loads(req.text)
        return j

    @staticmethod
    def oauth_refresh(file_env):
        """
        Internal Function that accepts an environment file containing the attr `refresh_token`
        Generates an authentication token based on the refresh token, then rotates the 
        refresh token in the env file. For best results set refresh tokens on Anaplan to be >30days.
        Else this authentication method will require rotation
        """
        load_dotenv(file_env)

        token_url = 'https://us1a.app.anaplan.com/oauth/token'
        header = {'Content-Type': 'application/json'}

        body = {
            'refresh_token': os.environ.get('refresh_token'),
            'client_id': os.environ.get('client_id'),
            'grant_type': 'refresh_token'
        }

        req = requests.post(token_url, headers=header, json=body, timeout=10)
        j = json.loads(req.text)
        new_refresh_token = j['refresh_token']
        set_key(file_env, 'refresh_token', new_refresh_token)
        return j

    @staticmethod
    def validate(token):
        """
        Internal Function that validates a given token and ensures the validation service
        has passed the token
        """
        if token['status'] == 'FAILURE_BAD_CREDENTIAL':
            raise SystemError()

        token_value = 'AnaplanAuthToken ' + \
            token['tokenInfo']['tokenValue']
        with requests.get(url='https://auth.anaplan.com/token/validate',
                          headers={'Authorization': token_value}, timeout=10) as req:
            j = json.loads(req.text)
        if j['statusMessage'] == 'Token validated':
            return token_value
