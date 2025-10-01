import requests
import json
from rich import print as rprint
from rich import reconfigure
reconfigure(highlight=False)



# --------------------------------------------------------------------------
# GETs and returns an entire SUBSCRIPTION block.
# --------------------------------------------------------------------------

def get_subscription_by_id(h, args):

    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + args.subscriptionId + "?api-version=2016-06-01"
    r = requests.get(ENDPOINT, headers=h).json()
    return r

    rprint('[#ff9999]no subscription with that id')
    exit(0)



# --------------------------------------------------------------------------
# GETs and returns an entire SUBSCRIPTION block given a subscription NAME 
# --------------------------------------------------------------------------

def get_subscription_by_name(h, args):

    subs = list_subscriptions(h, args)

    for s in subs:
        if s['displayName'] == args.subscriptionName:
            ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + s['subscriptionId'] + "?api-version=2016-06-01"
            r = requests.get(ENDPOINT, headers=h).json()
            return r

    rprint('[#ff9999]no subscription by that name found')
    exit(0)



# --------------------------------------------------------------------------
# returns an array of SUBSCRIPTION json blocks
# --------------------------------------------------------------------------

def list_subscriptions(h, args):

    ENDPOINT="https://management.usgovcloudapi.net/subscriptions?api-version=2023-07-01"
    r = requests.get(ENDPOINT, headers=h).json()
    rprint ('[#ff99ff]SUBSCRIPTIONS')
    for d in r['value']:
        rprint ('[#ffffff]{} [#ffaabb]{} [#00aa77]{}'.format(d['subscriptionId'], d['displayName'], d['state']))

    return r['value']



def list_resource_groups(h, args):

    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + args.subscription + "/resourceGroups?api-version=2024-11-01"
    r = requests.get(ENDPOINT, headers=h).json()
    rprint ('[#ff99ff]RESOURCE GROUPS')
    for d in r['value']:
        rprint ('[#ffaabb]{} [#ffffff]{}'.format(d['id'], d['name']))



def list_vms(h, args):

    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + args.subscription + "/providers/Microsoft.Compute/virtualMachines?api-version=2024-11-01"
    r = requests.get(ENDPOINT, headers=h).json()
    rprint ('[#ff99ff]VIRTUAL MACHINES')
    for d in r['value']:
        rprint ('[#ffffff]{} [#ffaabb]{}'.format(d['name'], d['id'])) # d['properties']['vmId']))



def list_storage_accounts(h, subscription):

    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + subscription + "/providers/Microsoft.Storage/storageAccounts?api-version=2024-01-01"
    r = requests.get(ENDPOINT, headers=h).json()
    rprint ('[#ff99ff]STORAGE ACCOUNTS')
    for d in r['value']:
        rprint ('[#ffaabb]{} [#ffffff]{}'.format(d['type'], d['name']))

    return r



# --------------------------------------------------------------------------
# There are two kinds of Azure Vaults:
#     Recovery Services Vaults
#     Backup Vaults
# This procedure takes the full JSON block a Subscription and 
# returns all the json for BOTH kinds of vaults in that Subscription.
# --------------------------------------------------------------------------

def list_vaults_by_subscription(h, s):

    # Recovery Services Vaults
    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + s['subscriptionId'] + "/providers/Microsoft.RecoveryServices/vaults?api-version=2025-02-01"
    recovery_services_vaults = requests.get(ENDPOINT, headers=h).json()
    rprint ('\n[#ff99ff]RECOVERY SERVICES VAULTS')
    for d in recovery_services_vaults['value']:
        rprint ('[#ffccff]{} [#ffffff]{} [#6699ff]{}'.format(d['type'], d['name'], d['location']))

    # Backup Vaults
    ENDPOINT="https://management.usgovcloudapi.net/subscriptions/" + s['subscriptionId'] + "/providers/Microsoft.DataProtection/backupVaults?api-version=2025-07-01"
    backup_vaults = requests.get(ENDPOINT, headers=h).json()
    rprint ('\n[#ff99ff]BACKUP VAULTS')
    for d in backup_vaults['value']:
        rprint ('[#ffccff]{} [#ffffff]{} [#6699ff]{}'.format(d['type'], d['name'], d['location']))

    all_vaults = {}
    all_vaults['value'] = recovery_services_vaults['value'] + backup_vaults['value']
    # print ( json.dumps(all_vaults, indent=2) )
    return all_vaults
        


# -------------------------------------------------------------------------------------------------------
# Given the args provided, will lists all the Backup Vaults by Subscription Name or Id.
# If no subscription is given in the args, it will list all Backup Vaults in all subscriptions.
# -------------------------------------------------------------------------------------------------------

def list_vaults(h, args):

    if args.subscriptionId:
        s = get_subscription_by_id(h, args)
        list_vaults_by_subscription(h, s)
    elif args.subscriptionName:
        s = get_subscription_by_name(h, args)
        list_vaults_by_subscription(h, s)
    else: 
        subs = list_subscriptions(h, args)
        for s in subs:
            list_vaults_by_subscription(h, s)
        


def list_tags(h, args):

    # print ( json.dumps(r, indent=2) )
    # rprint ('[#ffffff]{} [#ffaabb]{}'.format(d['name'], d['id']))

    if 'tags' in r:
       for (t,v) in r['tags'].items():
           print ('tag: ' + t + '; value: ' + v) 




