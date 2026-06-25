import json
import requests
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



kion = 'https://cloudtamer.cms.gov/api'



# --------------------------------------------
# load the kion app_api_key from disk
# --------------------------------------------

def load_app_api_key():

    try:
        with open('./kion_app_api_key', 'r') as file:
            token = file.readline().strip()
        return token

    except FileNotFoundError:
        print("Error: The file does not exist.")
        return False




def get_app_api_keys(t):

    urn = '/v3/app-api-key'
    href = kion + urn

    h = {
        'content-type': 'application/json',
        'authorization': 'Bearer ' + t
    }

    r = requests.get(href, headers=h, verify=False).json()

    return r



# -----------------------------------------------
# get the age of a key named "key_name"
# return 0 if the key isn't found
# -----------------------------------------------

# "created_at": "2025-02-24T17:54:12+0000"

def get_key_age(key_name, token):

    keys = get_app_api_keys(token)

    for key in keys['data']:
        if key['name'] == key_name:
            key_creation_date = datetime.strptime( key['created_at'], "%Y-%m-%dT%H:%M:%S+0000" )
            delta = key_creation_date - datetime.now()
            key_age = delta.days
            return key_age

    return 0



def rotate_app_api_key(t):

    urn = '/v3/app-api-key/rotate'
    href = kion + urn

    h = {
        'content-type': 'application/json',
        'authorization': 'Bearer ' + t
    }

    b = {
        'key': t
    }

    r = requests.post(href, headers=h, json=b, verify=False).json()
    newToken = r['data']['key']

    with open('./kion_app_api_key', 'w') as file:
        file.write(newToken)
