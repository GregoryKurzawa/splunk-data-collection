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
ti_m_6h = ( int(time.time()) - 21600 ) * 1000000
ti_m_12h = ( int(time.time()) - 43200 ) * 1000000
ti_m_24h = ( int(time.time()) - 86400 ) * 1000000
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

# protRuns_1h will not yet return a complete set of data (does not return TENANT data); please do not use.

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--cluster", choices=['x86dataprotecteast', 'x86dataprotectwest'], help="Cohesity Cluster", required=True)
parser.add_argument("-t", "--type", choices=[   'statsProtectionRuns',
                                                'statsReplicationRuns',
                                                'protectionRuns',
                                                'replicationRuns',
                                                'alerts',
                                                'nodes',
                                                'storage',
                                                'viewBoxes',
                                                'tenant',
                                                'summary',
                                                'vaults',
                                                'auditActions',
                                                'protRuns_1h',
                                                'protRuns_24h'], help="Type of data to harvest")
parser.add_argument("-p", "--print", action='store_true', help="Print collected data")
parser.add_argument("-s", "--splunk", action='store_true', help="Send data to Splunk")
parser.parse_args()
args = parser.parse_args()



if ( args.type == 'statsProtectionRuns' ):
    baseurn = '/irisservices/api/v1/public/stats/consumers?consumerType=kProtectionRuns'
    urn = baseurn
elif ( args.type == 'statsReplicationRuns' ):
    baseurn = '/irisservices/api/v1/public/stats/consumers?consumerType=kReplicationRuns'
    urn = baseurn
elif ( args.type == 'alerts' ):
    baseurn = '/irisservices/api/v1/public/alerts'
    urn = baseurn + '?startDateUsecs=' + str(ti_m_1h)
elif ( args.type == 'nodes' ):
    baseurn = '/irisservices/api/v1/public/cluster/status'
    urn = baseurn
elif ( args.type == 'storage' ):
    baseurn = '/irisservices/api/v1/public/stats/storage'
    urn = baseurn
elif ( args.type == 'viewBoxes' ):
    baseurn = '/irisservices/api/v1/public/stats/viewBoxes'
    urn = baseurn
elif ( args.type == 'tenant' ):
    baseurn = '/irisservices/api/v1/public/stats/tenants'
    urn = baseurn
elif ( args.type == 'summary' ):
    baseurn = '/irisservices/api/v1/public/stats/protectionSummary'
    urn = baseurn
elif ( args.type == 'vaults' ):
    baseurn = '/irisservices/api/v1/public/stats/vaults'
    urn = baseurn
elif ( args.type == 'auditActions' ):
    baseurn = '/irisservices/api/v1/public/auditLogs/cluster'
    urn = baseurn + '?startTimeUsecs=' + str(ti_m_1h) + '&endTimeUsecs=' + str(ti_now)
elif ( args.type == 'protRuns_1h' ):
    baseurn = '/irisservices/api/v1/public/protectionRuns'
    urn = baseurn + '?startTimeUsecs=' + str(ti_m_1h) + '&endTimeUsecs=' + str(ti_now)
elif ( args.type == 'protRuns_24h' ):
    baseurn = '/irisservices/api/v1/public/stats/protectionRuns/lastRun'
    urn = baseurn + '?toTimeUsecs=' + str(ti_now)



# ------------------------------------------------
# introductions and formalities
# ------------------------------------------------

print ('Cohesity Harvesting and Splunk Ingestion')
print ('cluster: ' + args.cluster)
print ('urn: ' + urn)



# ------------------------------------------------
# test the age of the access token
# refresh if necessary 
# ------------------------------------------------

cohesity.validate_token(args)

# file_path = os.path.realpath(__file__)
# dirname, fname = os.path.split(file_path)
# tokenfile = dirname + "/" + "token_cohesity_" + args.cluster

# m_ti = os.path.getmtime(tokenfile)
# epoch_ti = int(time.time())

# if ( m_ti <= (epoch_ti - 3600) ):
#     print ('token needs to be refreshed')
#     cohesity.refresh_token(args.cluster, tokenfile)
# else:
#     print ('token is still good')



# ------------------------------------------------
# fetch URN data from the Cohesity API
# ------------------------------------------------

# r = cohesity.fetch_api_data(urn, args, tokenfile)
r = cohesity.fetch_api_data(urn, args)



# ------------------------------------------------
# data display
# ------------------------------------------------

if (args.print):
    print ('Cohesity API Data')
    statics.print_indented_json (r)



# ------------------------------------------------
# payload delivery to Splunk
# ------------------------------------------------

if (args.splunk):
    print ('forwarding data to Splunk.')

    if ( args.type == 'statsProtectionRuns' or args.type == 'statsReplicationRuns' or args.type == 'tenant' or args.type == 'viewBoxes' ):
        b = make_batch_payload(r, args.cluster, 'statsList')
        splunk.deliver_batch_payload(b)

    elif ( args.type == 'protRuns_1h' or args.type == 'alerts' ):
        b = make_batch_payload(r, args.cluster)
        splunk.deliver_batch_payload(b)

    elif ( args.type == 'nodes' ):
        b = make_batch_payload(r, args.cluster, 'nodeStatuses')
        splunk.deliver_batch_payload(b)

    elif ( args.type == 'protRuns_24h' or args.type == 'summary' ):
        b = make_batch_payload(r, args.cluster, 'statsByEnv')
        splunk.deliver_batch_payload(b)

    elif ( args.type == 'auditActions' ):
        b = make_batch_payload(r, args.cluster, 'clusterAuditLogs')
        splunk.deliver_batch_payload(b)

    elif (args.type == 'storage' or args.type == 'vaults'):
        r['cluster'] = args.cluster
        r['urn'] = baseurn
        splunk.deliver_payload(r)



exit(0)
