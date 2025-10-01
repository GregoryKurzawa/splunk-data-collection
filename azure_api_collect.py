import msal
import requests
import json
import os
import argparse
import lib_azure
import lib_splunk
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from rich import print as rprint
from rich import reconfigure
reconfigure(highlight=False)



# ------------------------------------------------
# GLOBALS
# ------------------------------------------------

SPLUNK_KEY_AZURE = 'Splunk 69adf5fe-2496-45b7-85ab-009bf32f7c4e'



# ------------------------------------------------
# argument parsing
# ------------------------------------------------

parser = argparse.ArgumentParser()
# parser.add_argument("--json", action='store_true', help="print json output")
subparsers = parser.add_subparsers(dest='subparser_name')

parser_subs = subparsers.add_parser('subs', help="subscriptions")
parser_subs.add_argument("-p", "--payload", help="send payload to Splunk", action='store_true', default=False, required=False)

parser_rgs = subparsers.add_parser('rgs', help="resource groups")
parser_rgs.add_argument("-s", "--subscription", help="subscription ID", required=True)

parser_vms = subparsers.add_parser('vms', help="virtual machines")
parser_vms.add_argument("-s", "--subscription", help="subscription ID", required=True)

parser_vaults = subparsers.add_parser('vaults', help="list backup vaults by subscription name or id")
parser_vaults.add_argument("-i", "--subscriptionId", help="subscription ID", required=False)
parser_vaults.add_argument("-n", "--subscriptionName", help="subscription NAME", required=False)

parser_stgacts = subparsers.add_parser('stgacts', help="storage accounts")
parser_stgacts.add_argument("-s", "--subscription", help="subscription ID", required=False)

parser_jobs = subparsers.add_parser('jobs', help="list all backup jobs (by subscription if provided)")
parser_jobs.add_argument("-i", "--subscriptionId", help="subscription ID", required=False)
parser_jobs.add_argument("-n", "--subscriptionName", help="subscription NAME", required=False)
parser_jobs.add_argument("-l", "--hours", help="list only the last #hours of jobs", type=int, default=24, required=False)
parser_jobs.add_argument("-p", "--payload", help="send payload to Splunk", action='store_true', default=False, required=False)

parser_tags = subparsers.add_parser('tags', help="create a tags report")
parser_tags.add_argument("-p", "--payload", help="send payload to Splunk", action='store_true', default=False, required=False)

args = parser.parse_args()



# ------------------------------------------------
# global variables
# ------------------------------------------------

# the following 4 variables are required by MSAL:

AUTHORITY="https://login.microsoftonline.us/7c8bb92a-832a-4d12-8e7e-c569d7b232c9"
CLIENT_ID="26c6b700-7a24-4683-925c-4f1553644a68"		# python-backup-data-collection app
CLIENT_SECRET="4TCrvp.MJ~~.nfzf~a9G6q6vSQcKO0LQ1p"		# python-backup-data-collection app secret Id VALUE
SCOPE=["https://management.usgovcloudapi.net/.default"]



# ------------------------------------------------
# generate a report on all vm tags
# the output is written to a csv file
# the data can optionally be sent to Splunk (-p)
# ------------------------------------------------

def generate_tag_report():

    payload = []
    holding_frame = []

    # get all subscriptions
    SUBSCRIPTIONS="https://management.usgovcloudapi.net/subscriptions?api-version=2023-07-01"
    try: r = requests.get(SUBSCRIPTIONS, headers=h).json()
    except: 
        rprint ('[#ff3300]Failure to GET Azure subscriptions list.')
        rprint ('[#ff3300]You might not be connected to Zscaler.')
        exit(0)

    for s in r['value']:

        rprint ('\n[#ff99ff]SUBSCRIPTION: ', end="")
        rprint ('[#ffffff]{} '.format(s['subscriptionId']), end="")
        rprint ('[#ffaabb]{} '.format(s['displayName']), end="")
        rprint ('[#00aa77]{}'.format(s['state']))




        # ------------------------------------------------
        # get all SQL Servers in all subscriptions
        # ------------------------------------------------

        SQL="https://management.usgovcloudapi.net/subscriptions/" + s['subscriptionId'] + "/providers/Microsoft.Sql/servers?api-version=2023-08-01"
        r = requests.get(SQL, headers=h).json()
        rprint ('   [#ff99ff]SQL SERVERS')

        for sqls in r['value']:

            rprint ('   [#66ccff]{} [#ffffff]{}'.format(sqls['type'], sqls['name'])) # sqls['id']

            if 'tags' in sqls: tag_block = sqls['tags']
            else: tag_block = 'none'

            payload.append( {'sourcetype': 'azure_api_collect_tags', 'event': {  'subscription': s['subscriptionId'],
                                                                                    'subscriptionDisplayName': s['displayName'],
                                                                                    'name': sqls['name'],
                                                                                    'type': sqls['type'],
                                                                                    'tags': tag_block
                                                                                 } } )






        # ------------------------------------------------
        # get all vms in all subscriptions
        # ------------------------------------------------

        VMS="https://management.usgovcloudapi.net/subscriptions/" + s['subscriptionId'] + "/providers/Microsoft.Compute/virtualMachines?api-version=2024-11-01"
        r = requests.get(VMS, headers=h).json()
        rprint ('   [#ff99ff]VIRTUAL MACHINES')

        for vm in r['value']:

            tag_string = ''

            json_row = {}
            json_row['subscription'] = s['subscriptionId']
            json_row['subscriptionDisplayName'] = s['displayName']
            json_row['name'] = vm['name']
            json_row['type'] = vm['type']
            rprint ('   [#66ccff]{} [#ffffff]{}'.format(vm['type'], vm['name'])) # vm['id'], vm['properties']['vmId'])) 

            # get all vm tags
            TAGS="https://management.usgovcloudapi.net" + vm['id'] + "?api-version=2024-11-01"
            r = requests.get(TAGS, headers=h).json()

            if 'tags' in r:
               json_row['tags'] = {}
               payload.append( {'sourcetype': 'azure_api_collect_tags', 'event': {  'subscription': s['subscriptionId'],
                                                                                    'subscriptionDisplayName': s['displayName'],
                                                                                    'name': vm['name'],
                                                                                    'type': vm['type'],
                                                                                    'tags': r['tags']
                                                                                 } } )
               for (t,v) in r['tags'].items():
                   tag_string += '{}:{}; '.format(t, v)

            else:
                tag_string = 'none'
                payload.append( {'sourcetype': 'azure_api_collect_tags', 'event': { 'subscription': s['subscriptionId'],
                                                                                    'subscriptionDisplayName': s['displayName'],
                                                                                    'name': vm['name'],
                                                                                    'type': vm['type'],
                                                                                    'tags': 'none' } } )

            json_row['tags'] = tag_string
            holding_frame.append(json_row)

    # ------------------------------------------------
    # pandas DataFrame output to csv
    # ------------------------------------------------

    report = pd.DataFrame(holding_frame)
    report.to_csv('report.csv')

    return payload



# ------------------------------------------------------
# list backups and their status by subscription
# ------------------------------------------------------

def list_jobs_by_subscription( h, s, hours ):

    payload = []

    vaults = azure.list_vaults_by_subscription(h, s)

    _now = datetime.now()
    startTime = ( _now - timedelta(hours=hours) ).strftime("%Y-%m-%d %I:%M:%S %p")		# WORKING
    endTime = ( _now ).strftime("%Y-%m-%d %I:%M:%S %p")						            # WORKING

    rprint('\n[#ff99ff]JOBS[/] ({} hours)'.format(hours))

    for v in vaults['value']:

        # Important note: the filter in this command does not seem correct, but it is.
        # It is correct only because the filters for this API don't work as they should, by
        # Microsoft's admission. We should be able to use startTime "between" <date> and <date>
        # but that doesn't work. The current filter looks for backups that started between 
        # startTime and endTime.
        # Someday try something like this:
        # filter=startTime between '" + startTime + "' and '" + endTime "'

        url = "https://management.usgovcloudapi.net" + v['id'] + "/backupJobs?api-version=2025-02-01&$filter=startTime eq '" + startTime + "' and endTime eq '" + endTime + "'"
        rprint ('jobs in VAULT: [#ffffff]' + v['name'] )
        r = requests.get(url, headers=h).json()

        if 'value' in r:
            for j in r['value']:
                j['subscriptionName'] = s['displayName']
                if 'subscriptionId' not in j: j['subscriptionId'] = s['subscriptionId']
                if 'vault' not in j: j['vault'] = v['name']

                if v['type'] == "Microsoft.DataProtection/backupVaults":
                    j['properties']['friendlyName'] = j['properties']['backupInstanceFriendlyName']

                if v['type'] == "Microsoft.RecoveryServices/vaults":
                    j['properties']['friendlyName'] = j['properties']['entityFriendlyName']

                rprint('[#66ccff]{}[/] [#ffcc99]{}[/] [#ffff99]{}[/] {} {}'.format(
        			j['properties']['startTime'],
        			j['properties']['endTime'],
        			j['properties']['friendlyName'],
        			j['properties']['operation'],
        			j['properties']['status'],
                ))        
                payload.append( {'sourcetype': 'azure_api_collect', 'event': j} )

    return payload



# ------------------------------------------------
# main
# ------------------------------------------------

payload = []

# ------------------------------------------------
# initialize the Microsoft Access Library (MSAL)
# ------------------------------------------------

token_cache = msal.TokenCache()

app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,		        # For Entra ID or External ID
    client_credential=CLIENT_SECRET,	# ENV VAR contains a quotation mark-less string
    token_cache=token_cache,		    # Let this app (re)use an existing token cache.
)

result = app.acquire_token_for_client(scopes=SCOPE)

if "access_token" in result:
    h = {
        'Authorization': 'Bearer ' + result['access_token'],
    }

else:
    print("Token acquisition failed", result)
    exit(0)



if args.subparser_name == 'subs': azure.list_subscriptions(h, args)
if args.subparser_name == 'rgs': azure.list_resource_groups(h, args)
if args.subparser_name == 'vms': azure.list_vms(h, args)
if args.subparser_name == 'vaults': azure.list_vaults(h, args)



if args.subparser_name == 'stgacts':
    if ( args.subscription ):
        payload = azure.list_storage_accounts(h, args.subscription)
    else:
        subs = azure.list_subscriptions(h, args)
        for s in subs:
            payload += azure.list_storage_accounts(h, s)



if args.subparser_name == 'jobs':
    if ( args.subscriptionId ):
        s = azure.get_subscription_by_id(h, args)
        payload = list_jobs_by_subscription(h, s, args.hours)
    elif ( args.subscriptionName ):
        s = azure.get_subscription_by_name(h, args)
        payload = list_jobs_by_subscription(h, s, args.hours)
    else:
        subs = azure.list_subscriptions(h, args)
        for s in subs:
            payload += list_jobs_by_subscription(h, s, args.hours)
            rprint ('[#bbccaa]appended jobs from subscription:[#ffffff]{}[/] [#bbccaa]to payload'.format(s['displayName']) )

    

if args.subparser_name == 'tags':
    # azure.list_tags(h, args)
    payload = generate_tag_report()

    # write payload to file
    with open('tags.output', 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    


if 'payload' in args:
    if args.payload == False:
        rprint ('\n[#99ffcc]skipping payload delivery to Splunk')
    elif payload:
        rprint ('\n[#99ffcc]sending payload to Splunk')
        splunk.deliver_batch_payload(payload, SPLUNK_KEY_AZURE)
    else: rprint ('\n[#ffcccc]no payload to deliver')
else: rprint ('\n[#ffcccc]payload not delivered by default')

