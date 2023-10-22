"""
Anaplan Integration Python Library - dictionary.py

Module connects to Anaplan to the specified workspace ID and model ID
Core module that automates away looking at item IDs, can run imports, processes, uploads,
dump error logs, directly view data in a module as well as write to cells in a line item

Additionally, by accepting an AnaplanAuth login object as an argument, this module abstracts
away needing to login and generate tokens

"""

import json
from pathlib import Path
import requests

class AnaplanModel:
    """
    Represents a connection to an Anaplan model.

    The `AnaplanModel` class is a one stop shop to run most integration related APIs

    Attributes:
        login (class): must be AnaplanAuth class instantiated correctly
        ws_id (str): must be a valid Anaplan Workspace ID that the login user has access to
        model_id (str): must be a valid Anaplan Model ID that the login user has access to

    Example:
        ```python
        login = AnaplanAuth('basic', 'username@company.com:Password123')
        conn = AnaplanModel(login, ws_id, model_id)
        conn.run('118000000000')
        ```
    """

    def __init__(self, login, ws_id, model_id):
        self.login = login
        self._token_value = login.get_token()
        self.expires_at = login.expires_at
        self.ws_id = ws_id
        self.model_id = model_id
        self.header = {'Authorization': self._token_value}
        self.url = f'https://api.anaplan.com/2/0/workspaces/{self.ws_id}/models/{self.model_id}/'
        self.task_header = {'Authorization': self._token_value,
                            'Content-Type': 'application/json'}
        self.json_header = {'Authorization': self._token_value,
                            'Accept': 'application/json'}
        self.task_body = {'localeName': 'en_US'}
        self.file_header = {'Authorization': self._token_value,
                            'Content-Type': 'application/octet-stream'}
        self.chunk_size = 50 * 1048576

    def get_token(self):
        """
        Refreshes token on demand and updates class token value and expires at time
        """
        self._token_value = self.login.get_token()
        self.expires_at = self.login.expires_at

    @property
    def imports(self):
        """
        Locates all import 112 IDs and returns a json object
        """
        with requests.get(url=self.url + 'imports', headers=self.header) as r:
            j = json.loads(r.text)
        return j['imports']

    @property
    def actions(self):
        """
        Locates all action 117 IDs and returns a json object
        """
        with requests.get(url=self.url + 'actions', headers=self.header) as r:
            i = json.loads(r.text)
        return i['actions']

    @property
    def processes(self):
        """
        Locates all process 118 IDs and returns a json object
        """
        with requests.get(url=self.url + 'processes', headers=self.header) as r:
            i = json.loads(r.text)
        return i['processes']

    @property
    def files(self):
        """
        Locates all file 113 IDs and returns a json object
        """
        with requests.get(url=self.url + 'files', headers=self.header) as r:
            i = json.loads(r.text)
        return i['files']

    @property
    def line_items(self):
        """
        Locates all line item 221 IDs and returns a json object
        """
        with requests.get(url=self.url + 'lineItems', headers=self.header) as r:
            i = json.loads(r.text)
        return i['items']

    @property
    def views(self):
        """
        Locates all module view 102 and saved view 222 IDs and returns a json object
        """
        with requests.get(url=self.url + 'views', headers=self.header) as r:
            i = json.loads(r.text)
        return i['views']

    def run(self, action_id):
        """
        Catchall function that runs any valid task in Anaplan
        Passes the action ID to an internal function to receive the keyword for the req URL
        Returns the API response
        """
        url = self.url + self.parse_action_id(action_id) + '/tasks'
        with requests.post(url, headers=self.task_header, json=self.task_body) as r:
            return json.loads(r.text)

    def monitor(self, action_id):
        """
        Catchall function that monitors any valid task in Anaplan
        Passes the action ID to an internal function to receive the keyword for the req URL
        Monitoring the errors requires passing a task ID to the API service. Instead of storing 
        task ID; first this function requests API service for all the task IDs against that action
        Then pops the last and latest task and passes that through for monitoring
        Returns API response; query the `localMessageText` within the response for error message
        """
        url = self.url + self.parse_action_id(action_id)
        url = url + '/tasks'
        with requests.get(url, headers=self.task_header) as r:
            req = json.loads(r.text)
            tasks = req['tasks']
        latest_task = tasks[-1]['taskId']
        url = url + f'/{latest_task}'
        with requests.get(url, headers=self.task_header) as r:
            req = json.loads(r.text)
        return req['task']

    def status(self, action_id):
        """
        The monitor request returns a large json object that also contains the current taskState
        Instead of querying for status separately, reuse monitor function here
        use this function as a loop function that checks the status of an action until it is marked
        COMPLETE
        """
        task = self.monitor(action_id)
        return task['taskState']

    def read_view(self, view_id):
        """
        Point to any module or saved view in Anaplan and receive a JSON object with the live
        data within that view. Prefer JSON to CSV as it's easier to query even though 
        it is not human readable
        """
        url = self.url + 'views/' + view_id + '/data?format=v1'
        with requests.get(url, headers=self.json_header) as r:
            return json.loads(r.text)

    def write_cells(self, module_id, body):
        """
        Write to cells within Anaplan. Supports only 1000 cells per call (API itself is rate limited)
        accepts a module ID and list of lists as argument. Look at official API docs for full explanation
        """
        final_body = []
        for item in body:
            final_body.append(
                {
                    "lineItemId": item[0],
                    "dimensions": item[1],
                    "value": item[2]
                }
            )
        url = self.url + 'modules/' + module_id + '/data'
        with requests.post(url, headers=self.json_header, json=final_body) as r:
            return json.loads(r.text)

    def upload(self, file_id, file):
        """
        Uploads a file to Anaplan. Chunks are considered best practice. Anaplan supports max
        50MB chunks. Requests at beginning and end to mark upload as started and ended respectively
        """
        file_size = Path(file).stat().st_size
        upload_file_url = self.url + 'files/' + file_id
        body_begin = {'id': file_id,
                     'chunkCount': -1}

        body_complete = {'id': file_id,
                        'chunkCount': file_size / self.chunk_size}

        begin_upload_request = requests.post(
            upload_file_url, headers=self.task_header, json=body_begin)

        if begin_upload_request.ok:
            chunk_num = 0
            with open(file, 'rt') as f:
                chunked_data = f.readlines(self.chunk_size)
                while chunked_data:
                    upload_data = ''

                    for line in chunked_data:
                        upload_data += line

                    requests.put(upload_file_url + '/chunks/' + str(chunk_num),
                                 headers=self.file_header, data=upload_data.encode('utf-8'))
                    chunked_data = f.readlines(self.chunk_size)
                    chunk_num += 1

            with requests.post(upload_file_url + '/complete', 
                               headers=self.task_header, json=body_complete) as r:
                return json.loads(r.text)
        else:
            return 'Unable to upload, please check fileID and metadata'

    @staticmethod
    def parse_action_id(action_id):
        """
        Internal Function to return keyword for URLs
        """
        if action_id[:3] == '112':
            task = 'imports'
        elif action_id[:3] == '116':
            task = 'exports'
        elif action_id[:3] == '117':
            task = 'actions'
        elif action_id[:3] == '118':
            task = 'processes'
        else:
            return 'Invalid task provided, please provide valid task'

        return f'{task}/{action_id}'
