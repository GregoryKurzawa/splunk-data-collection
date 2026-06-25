#!./venv/bin/python3

import boto3
import time
import datetime
import json
import subprocess
import lib_splunk as splunk
import lib_kion as kion



ctkey = './ctkey-linux'
key_for_aws = 'Splunk efdb579f-f40b-42c4-957d-62b8a4773f9d'
refreshed_keys = []



# ----------------------------------------
# converts datetime fields to strings
# why do this? I can't remember ...
# ----------------------------------------

def convert_datetime_to_string(bj):

    bj['CreationDate'] = bj['CreationDate'].isoformat()
    if 'CompletionDate' in bj:
        bj['CompletionDate'] = bj['CompletionDate'].isoformat()
    if 'ExpectedCompletionDate' in bj:
        bj['ExpectedCompletionDate'] = bj['ExpectedCompletionDate'].isoformat()
    if 'StartBy' in bj:
        bj['StartBy'] = bj['StartBy'].isoformat()
    if 'InitiationDate' in bj:
        bj['InitiationDate'] = bj['InitiationDate'].isoformat()



# --------------------------------------------------------
# refresh the account key via ctkey if needed
# --------------------------------------------------------

def refresh_account_key_if_needed(a, r, p):

    account = '--account=' + a
    role = '--cloud-access-role=' + r
    profile = a + '_gss-operations-admin'

    if a not in refreshed_keys:

        try:
            ctkey_out = subprocess.check_output([ctkey, "savecreds", "--url=https://cloudtamer.cms.gov", "--app-api-key=" + TOKEN, account, role])

        except:
            print ('could not refresh key; skipping account {}'.format(a))
            return False

        else:
            refreshed_keys.append(a)
            return True



# ---------------------------------------------
# get BackupPlan name of a BackupJob
# ---------------------------------------------

def get_backup_plan_name(bj):

    account_id = bj['AccountId']

    role = '--cloud-access-role=gss-operations-admin'
    account = '--account=' + bj['AccountId']
    profile = account_id + '_gss-operations-admin'

    # refresh account key if needed
    refresh_account_key_if_needed(bj['AccountId'], role, profile)

    # get BackupPlan details
    print ('getting BackupPlan details for AccountId:{} BackupJob:{}'.format(bj['AccountId'], bj['BackupJobId']))

    if 'CreatedBy' in bj:

        boto3.setup_default_session( profile_name=profile, region_name='us-east-1' )
        c = boto3.client('backup')

        try:
            bp = c.get_backup_plan( BackupPlanId=bj['CreatedBy']['BackupPlanId'] )

        except:
            print ('cannot locate BackupJob:{} plan; skipping'.format(bj['BackupJobId']))

        else: # there were no exceptions
            print ('BackupPlanName: {}'.format(bp['BackupPlan']['BackupPlanName']))
            return bp['BackupPlan']['BackupPlanName']



# -------------------------------------------------------------
# get all BackupPlan names in an account
# takes an account number (a) and an account name (n)
# -------------------------------------------------------------

def get_plan_names(a, n):

    role = 'gss-operations-admin'
    profile = a + '_gss-operations-admin'

    if ( refresh_account_key_if_needed(a, role, profile) ):

        # get BackupPlan details
        boto3.setup_default_session( profile_name=profile, region_name='us-east-1' )
        c = boto3.client('backup')

        backup_plans = c.list_backup_plans()

        print ('BackupPlans for account:{}'.format(a))
        for bp in backup_plans['BackupPlansList']:

            print ('{};{};{}'.format(n, bp['BackupPlanName'], bp['CreationDate']))
            print ('{};{};{}'.format(n, bp['BackupPlanName'], bp['CreationDate']), file=f)



# ----------------------------------------
# go through all pages of BackupJobs
# ----------------------------------------

def build_payload(page_iterator):

    payload = []

    for page in page_iterator:

        for bj in page['BackupJobs']:

            convert_datetime_to_string(bj)

            # get the BackupPlanName by more API calls to the proper account
            # this works, but is it really what we want to do for every BackupJob?
            # backup_plan_name = get_backup_plan_name(bj)

            # insert BackupPlanName into BackupJob details
            # bj['CreatedBy']['BackupPlanName'] = backup_plan_name

            # append BackupJob to payload
            payload.append( {'sourcetype': 'aws_backup_gather', 'event': bj} )

    return payload



# ------------
# MAIN
# ------------

TOKEN = kion.load_app_api_key()
print ('kion token loaded')

key_age = kion.get_key_age('python_api_key', TOKEN)
print ('python_api_key is {} days old'.format( abs(key_age) ))

if abs(key_age) >= 5:
    print ('refreshing key')
    TOKEN = kion.rotate_app_api_key(TOKEN)

boto3.setup_default_session( profile_name='849406929254_governance20-application-admin',
			     region_name='us-east-1' )




# --------------------------------------------------------------------------------------
# prepare kion environment
# --------------------------------------------------------------------------------------

kion_url = '--url=https://cloudtamer.cms.gov'
cloudAccessRole = '--cloud-access-role=governance20-application-admin'
account = '--account=849406929254'

print ('fetching new key (via ctkey-linux) for integrated AccountId:849406929254')
subprocess.run([ctkey, "savecreds", kion_url, "--app-api-key=" + TOKEN, account, cloudAccessRole])



# --------------------------------------------------------------------------------------
# get a list and details on all accounts in the org
# --------------------------------------------------------------------------------------

# client = boto3.client('organizations')
# 
# accounts = []
# NextToken = None
# 
# while True:
#     if NextToken:
#         print ('getting next page')
#         r = client.list_accounts(NextToken=NextToken)
#     else:
#         print ('getting first page')
#         r = client.list_accounts()
#     accounts = accounts + r['Accounts']
#     try: NextToken = r['NextToken']
#     except:
#         break
# 
# print ('accounts: {}'.format( len(accounts) ))
# 
# exit(0)



# --------------------------------------------------------------------------------------
# list the BACKUP VAULTS
# because a vault is in an account; you have to login to the account first
# --------------------------------------------------------------------------------------

# client = boto3.client('backup')

# for a in accounts:
#     print ('account: {} {}'.format(a['Id'], a['Name']))
#     # make a function to get vault details

# exit(0)



# --------------------------------------------------------------------------------------
# list the BACKUP PLANS for every account in 'accounts'
# --------------------------------------------------------------------------------------

# f = open('/home/gkurz/scripts/account_backup_plans.csv', 'w+')
# 
# client = boto3.client('backup')
# 
# for a in accounts:
#     print ('account: {} {}'.format(a['Id'], a['Name']))
#     # This takes a long time.
#     # get_plan_names( a['Id'], a['Name'] )



# --------------------------------------------------------------------------------------
# this block gets the details of a single BACKUP JOB
# --------------------------------------------------------------------------------------

# r = client.describe_backup_job(BackupJobId='B055C0E1-4CBF-8780-C770-74BFA91B9C4D')
# exit(0)



# --------------------------------------------------------------------------------------
# this block lists BACKUP JOBS across ALL accounts
# over a certain time period
# --------------------------------------------------------------------------------------

# if we don't -5 to the hours we get skewed results; something to do with tz; fix later
hoursBack = 6
# hoursBack = 24
# t = datetime.datetime.now() - datetime.timedelta(hours=(hoursBack-5))
t = datetime.datetime.now() - datetime.timedelta(hours=(hoursBack))

client = boto3.client('backup')
paginator = client.get_paginator('list_backup_jobs')
page_iterator = paginator.paginate(ByAccountId='*', ByCreatedAfter=t)

# some other search options:
# page_iterator = paginator.paginate(ByAccountId='116915543549')
# page_iterator = paginator.paginate(ByAccountId='116915543549', ByResourceArn='arn:aws:elasticfilesystem:us-east-1:116915543549:file-system/fs-033af280')
# page_iterator = paginator.paginate(ByAccountId='*', ByState='COMPLETED')






# print ('fetching new key (via ctkey-linux) for integrated AccountId:849406929254')
# kion = '--url=https://cloudtamer.cms.gov'
# cloudAccessRole = '--cloud-access-role=governance20-application-admin'
# account = '--account=849406929254'
# subprocess.run([ctkey, "savecreds", kion, "--app-api-key=" + TOKEN, account, cloudAccessRole])

payload = build_payload(page_iterator)

# x = 1 
# for bj in payload:
#     print('{} CreationDate:{}'.format(x, bj['event']['CreationDate']))
#     x = x+1

# print (json.dumps(payload, indent=4, default=str))
# for j in payload:
#     print ('BackupJobId:{}; CreationDate:{}'.format(j['event']['BackupJobId'], j['event']['CreationDate']))
# print ('total jobs: {}'.format(len(payload)))
splunk.deliver_batch_payload(payload, key_for_aws)

# Send an event to Splunk indicating that the script completed successfully.
payload = { 'status': 'aws_backup_gather script completed' }
splunk.deliver_payload(payload, 'aws_backup_gather', key_for_aws)

