# --------------------------------------------------------
# OCI REST API Library.
# --------------------------------------------------------

import os
import json
import argparse
import requests

from oci.config import from_file
from oci.signer import Signer



# -----------------------------------------------------------------------------
# authenticates with OCI
# -----------------------------------------------------------------------------

def authenticate():

    config = from_file()

    auth = Signer(
    tenancy=config['tenancy'],
    user=config['user'],
    fingerprint=config['fingerprint'],
    private_key_file_location=config['key_file'],
    pass_phrase=config['pass_phrase'] )

    print('\nAuthentication Configuration')
    print('tenancy: ' + config['tenancy'])
    print('user: ' + config['user'])
    print('fingerprint: ' + config['fingerprint'])
    print('key_file: ' + config['key_file'])
    try: print('pass_phrase: ' + config['pass_phrase'])
    except: print('pass_phrase: None')
    print('\n')

    return config, auth





# -----------------------------------------------------------------------------
# Recursively delves into the compartments API to return
# a list of all child/sub compartments off the provided compartment (c).
# -----------------------------------------------------------------------------

def get_all_compartments(auth, c):

    cl = []

    uri = 'https://identity.us-langley-1.oraclegovcloud.com/20160918/compartments?compartmentId=' + c
    r = requests.get(uri, auth=auth).json()

    for d in r:
        print('found cId: ' + d['id'], flush=True)
        cl.append(d['id'])
        cl = cl + get_all_compartments(auth, d['id'])

    return cl



# -----------------------------------------------------------------------------
# Takes an endpoint (dp) and a compartmentId (cId).
# Returns raw JSON.
# -----------------------------------------------------------------------------

def fetch_api_data( auth, ep, cId ):

    endpoint = 'https://' + ep + '?compartmentId=' + cId
    r = requests.get(endpoint, auth=auth)

    return r



# -----------------------------------------------------------------------------
# Posts data to an OCI endpoint.
# -----------------------------------------------------------------------------

def post_api_data ( auth, ep, cId, b ):

    endpoint = 'https://' + ep + '?compartmentId=' + cId
    r = requests.post(endpoint, auth=auth, json=b)

    return r
