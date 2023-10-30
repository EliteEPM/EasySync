"""
Run this script as permanently alive to login to Anaplan and constantly check for 
new integration requests. If request is detected, use the anaplan library to upload, monitor
and close out the request

Visit https://github.com/EliteEPM/EasySync for a full How-To guide
"""

from time import sleep
from datetime import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from anaplan import AnaplanAuth, AnaplanModel

ENV = 'creds.env'
load_dotenv(ENV)

# Uncomment the type of login you want to use
# Basic authentication
un = os.environ.get('un')
pw = os.environ.get('pw')

login = AnaplanAuth('basic', f'{un}:{pw}')

# Certificate authentication
# pub_cert = os.environ.get('pub_cert')
# priv_key = os.environ.get('priv_key')

# login = AnaplanAuth('certificate', pub_cert, priv_key)

# OAuth Device authentication
# login = AnaplanAuth('oauth_refresh', env_filename)

ws_id = ''
model_id = ''
conn = AnaplanModel(login, ws_id, model_id)
conn_expire_time = conn.expires_at

if not os.path.exists('log'):
    os.mkdir('log')

# File 1 set parameters
int_module_id = ''  # integration module name where user has access
file_view_id = '' # saved view in integration module with request parameters
file_user_init = ''  # line item where user begins pull
file_sys_init_1 = ''  # Bool to mark integration process has begun
file_sys_init_2 = ''  # Bool to mark download from source has begun
# Bool to mark file uploaded into Anaplan and processing
file_sys_init_3 = ''
file_sys_time = ''  # Text on Anaplan to update latest run time
file_upload_file = ''  # ID of file to be uploaded
file_upload_proc = ''  # Process to load the file

files_dim_name = 'File List'  # Name of the dimension carrying integration files
file_name = 'File 1'  # Name of the file itself

dimension = [{"dimensionName": files_dim_name, "itemName": file_name}]

# begin neverending loop
while True:

    # Refresh token if time's up
    if datetime.now() > conn_expire_time:
        conn.get_token()
        conn_expire_time = conn.expires_at

    user_req = conn.read_view(file_view_id)
    user_init = user_req['rows'][0]['cells'][0]
    req_month = user_req['rows'][0]['cells'][1]

    if user_init == 'true':

        # Inform Anaplan that request is being processed by flipping a boolean
        # the data that is passed in must be a list of lists with line item name
        # dimension dict and value to be changed to
        data = [[file_sys_init_1, dimension, True]]
        # Write to Anaplan
        conn.write_cells(int_module_id, data)

        # Following code should be customized to trigger any Rest API to download from source system
        # Here we are creating a temporary file specifically to be uploaded after
		# limiting the data to a specific month then we delete the temporary file

        full_file = pd.read_csv('core_file.csv')
        sleep(10)  # Demo purpose only, delete this line in production

        data = [[file_sys_init_2, dimension, True]]
        conn.write_cells(int_module_id, data)

        filtered = full_file.query(f"Month == '{req_month}'")
        filtered.to_csv('download.csv', encoding='utf-8')
        sleep(12)  # Demo purpose only, delete this line in production

        data = [[file_sys_init_3, dimension, True]]
        conn.write_cells(int_module_id, data)

        conn.upload(file_upload_file, 'download.csv')
        conn.run(file_upload_proc)
        upload_time = str(datetime.now().replace(second=0, microsecond=0))

        # Code for failure/success logging goes here
        status = ''
        while status != 'COMPLETE':
            status = conn.status(file_upload_proc)
            sleep(2)

        with open(f'log/{upload_time} - {file_upload_proc} results.json', 'w') as f:
            f.write(str(conn.monitor(file_upload_proc)))

        # Code for upload to S3 bucket for long term tracking goes here
        # Code for history logging upload file creation and upload to Anaplan goes here

        # Inform Anaplan that integration is done and ready for the next run

        data = [
            [file_sys_init_1, dimension, False],
            [file_user_init, dimension, False],
            [file_sys_init_2, dimension, False],
            [file_sys_init_3, dimension, False],
            [file_sys_time, dimension, upload_time],
        ]

        conn.write_cells(int_module_id, data)

        os.remove('download.csv')
        # Print to console for logging
        print(f'Uploaded {file_name} at {upload_time} for month {req_month}')

    sleep(5)
