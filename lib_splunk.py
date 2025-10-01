import sys
import json
import requests
import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



# --------------------------------------------------------------------------------
# Packages a single Cohesity JSON stanza into a Splunk Event.
# Sends to Splunk.
# the key looks like 'Splunk <key>'
# --------------------------------------------------------------------------------

def deliver_payload(p, sourcetype, key):

    url = "https://dlpvpsp023.cacheeast.internal.cms.gov:8088/services/collector"

    h = {
            'accept': 'application/json',
            'Authorization': key
    }

    # The below is what the most basic Splunk payload looks like.
    # payload = '{ "sourcetype": "testing", "event": "Testing event payload delivery via script." }'

    payload = {}
    payload['sourcetype'] = sourcetype
    payload['event'] = p

    s = requests.Session()
    r = s.post(url, headers=h, json=payload, verify=False).json()

    # print (r)



# --------------------------------------------------------------------------------
# Accepts a JSON block containing any number of Events.
# the key looks like 'Splunk <key>'
# --------------------------------------------------------------------------------

def deliver_batch_payload(payload, key):

    url = "https://dlpvpsp023.cacheeast.internal.cms.gov:8088/services/collector"

    h = {
            'accept': 'application/json',
            'Authorization': key
    }

    s = requests.Session()
    r = s.post(url, headers=h, json=payload, verify=False).json()

    print (r)
