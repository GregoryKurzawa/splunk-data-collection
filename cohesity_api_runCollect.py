#!/opt/scripts/.venv/bin/python3.11

# --------------------------------------------------------
# Poll a Cohesity REST API to capture data.
# Load that data to Splunk for indexing.
# --------------------------------------------------------

import os
import json
import time
import statics
import argparse
import lib_cohesity
import lib_splunk



# ------------------------------------------------
# time variable preparation
# converts current time and 1h ago time to usecs
# ------------------------------------------------

ti_now = int(time.time()) * 1000000
ti_m_1h = ( int(time.time()) - 3600 ) * 1000000
ti_m_3h = ( int(time.time()) - 3600*3 ) * 1000000
ti_m_4h = ( int(time.time()) - 3600*4 ) * 1000000
ti_m_6h = ( int(time.time()) - 3600*6 ) * 1000000
ti_m_12h = ( int(time.time()) - 43200 ) * 1000000
ti_m_16h = ( int(time.time()) - 3600*16 ) * 1000000
ti_m_24h = ( int(time.time()) - 3600*24 ) * 1000000
ti_m_48h = ( int(time.time()) - 172800 ) * 1000000
ti_m_2d = ( int(time.time()) - 86400*2 ) * 1000000
ti_m_3d = ( int(time.time()) - 86400*3 ) * 1000000
ti_m_1w = ( int(time.time()) - 86400*7 ) * 1000000



# ------------------------------------------------
# payload delivery to Splunk
# IF a subField is provided, it will be mined.
# This is needed because not all JSON returned
# by Cohesity is structured the same:
# sometimes it has a subfield, sometimes not.
# ------------------------------------------------

def make_batch_payload(r, c, *subField):

    b = []

    if ( subField ):

        for i in r[ subField[0] ]:
            i['cluster'] = c
            i['urn'] = baseurn
            b.append( {'sourcetype': 'cohesity', 'event': i} )

    else:

        for i in r:
            i['cluster'] = c
            i['urn'] = baseurn
            b.append( {'sourcetype': 'cohesity', 'event': i} )


    return b



# ------------------------------------------------
# argument parsing
# ------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--cluster",
        choices=['x86dataprotecteast', 'x86dataprotectwest'],
        help="Cohesity Cluster",
        required=True)
parser.add_argument("-t", "--tenantId",
        help="ID of tenant for which to harvest data.",
        required=False)
parser.add_argument("-p", "--print",
        action='store_true',
        help="Print collected data.")
parser.add_argument("-s", "--splunk",
        action='store_true',
        help="Send data to Splunk.")
parser.parse_args()
args = parser.parse_args()

baseurn = '/irisservices/api/v1/public/protectionRuns'
urn = baseurn + '?startTimeUsecs=' + str(ti_m_24h)



# ------------------------------------------------
# introductions and formalities
# ------------------------------------------------

print ('Cohesity Run Harvesting and Splunk Ingestion')
print ('cluster: ' + args.cluster)



# ------------------------------------------------
# refresh the Cohesity access token if necessary 
# ------------------------------------------------

cohesity.validate_token(args)



# ------------------------------------------------
# fetch URN data from the Cohesity API
# ------------------------------------------------

# If a tenantId was NOT provided as an arg, fetch a list of all tenants.
# If a tenantId WAS provided as an arg (-t | --tenantId)
# we will fetch data for that tenantId only.
 
if ( not args.tenantId ):
    r = cohesity.fetch_api_data('/irisservices/api/v1/public/tenants', args)

else:
    r = [ {'tenantId':args.tenantId} ]

# get run data for each tenant (or the provided tenantId):

for t in r:

    if ( args.print ):
        print (t)

    print ('fetching data for tenantId: ' + t['tenantId'])
    d = cohesity.fetch_api_data(urn, args, tenant=t['tenantId'])

    # ------------------------------------------------
    # data massaging and payload to Splunk
    # ------------------------------------------------

    # for each JOB:

    for j in d:

        if ( args.print ):
            # print (j)
            print ( 'JOB: ' + str(j['jobId']) + ':' + str(j['jobName']) + ':' + j['backupRun']['status'] )

        # for each BACKUP within each Job:

        if ( j['backupRun'].get('sourceBackupStatus') ):

            sbList = j['backupRun']['sourceBackupStatus']

            for sb in sbList:

                # sb['tenantId'] = args.tenantId
                sb['tenantId'] = t['tenantId']
                sb['jobId'] = j['jobId']
                sb['jobName'] = j['jobName']
                sb['level'] = 'source'

                if ( args.print ):
                    print ('   SOURCE: ' + str(sb['tenantId']) + ':' + str(sb['source']['id']) + ':' + sb['source']['name'] + ':' + sb['status'] )


            # The following section is only for shipping SOURCE events to Splunk.

            if ( args.splunk ):

                print ('forwarding SOURCE backupData to Splunk.')
                b = make_batch_payload(sbList, args.cluster)
                splunk.deliver_batch_payload(b)


        # The following section is only for shipping the JOB event to Splunk.

        if ( args.splunk ):

            print ('forwarding JOB backupData to Splunk.')
            j['cluster'] = args.cluster
            # j['tenantId'] = args.tenantId
            j['tenantId'] = t['tenantId']
            j['urn'] = baseurn
            j['level'] = 'job'

            # Remove cumbersome details ('copySnapshotTasks') from the copyRun field.

            if ( j.get('copyRun') ):

                for cr in j['copyRun']:
                    if cr.get('copySnapshotTasks'):
                        cr.pop('copySnapshotTasks')

            # Remove cumbersome details ('sourceBackupStatus') from the backupRun field.

            if ( j['backupRun'].get('sourceBackupStatus') ):
                j['backupRun'].pop('sourceBackupStatus')

            splunk.deliver_payload(j)



exit(0)
