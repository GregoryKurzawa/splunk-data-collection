# ----------------------------------------------------------------------------------------------
# OCI REST API data collection
# Currently collects only Autonomous Database (ADB) details.
# ----------------------------------------------------------------------------------------------

import lib_oci as loci
import lib_splunk as splunk



# ----------------------------------------------------------------------------------------------
# Fetch the number of sessions metric for an ADB.
# cId: containerId in which the ADB lives.
# rId: Id of the ADB resource.
# returns metrics (m) in JSON format
# ----------------------------------------------------------------------------------------------

def fetch_adb_numSessions_metrics ( auth, cId, rId ):

    endpoint = 'telemetry.us-langley-1.oraclegovcloud.com/20180401/metrics/actions/summarizeMetricsData'

    body = {
      'namespace': 'oci_autonomous_database',
      'query': 'Sessions[3h]{resourceId = "' + rId + '"}.max()',
      'resolution': '3h'
      # "query": 'CpuUtilization[3h].mean()',
      # "startTime": "2026-10-03T00:00:00.000Z",    # defaults to 3 hours ago
      # "endTime": "2026-10-06T00:00:00.000Z",      # defaults to now
    }

    r = loci.post_api_data(auth, endpoint, cId, body).json()

    if (r):

        sessions_3hr = r[0]['aggregatedDatapoints'][0]['value']
        return sessions_3hr

    else:

        print('no metrics')
        return 0



# ----------------------------------------------------------------------------------------------
# Fetch the Session metrics for an ADB.
# cId: containerId in which the ADB lives.
# rId: Id of the ADB resource.
# returns metrics (m) in JSON format
# ----------------------------------------------------------------------------------------------

def fetch_adb_session_metrics ( auth, cId, rId ):

    endpoint = 'telemetry.us-langley-1.oraclegovcloud.com/20180401/metrics/actions/summarizeMetricsData'

    body = {
      'namespace': 'oci_autonomous_database',
      'query': 'SessionUtilization[3h]{resourceId = "' + rId + '"}.mean()',
      'resolution': '3h'
      # "query": 'CpuUtilization[3h].mean()',
      # "startTime": "2026-10-03T00:00:00.000Z",    # defaults to 3 hours ago
      # "endTime": "2026-10-06T00:00:00.000Z",      # defaults to now
    }

    r = loci.post_api_data(auth, endpoint, cId, body).json()

    if (r):

        sessionUtilization_3hr = r[0]['aggregatedDatapoints'][0]['value']
        return sessionUtilization_3hr

    else:

        print('no metrics')
        return 0



# ----------------------------------------------------------------------------------------------
# Fetch the CPU Utilization metrics for an ADB.
# cId: containerId in which the ADB lives.
# rId: Id of the ADB resource.
# returns metrics (m) in JSON format
# ----------------------------------------------------------------------------------------------

def fetch_adb_cpuUtilization_metrics ( auth, cId, rId ):

    endpoint = 'telemetry.us-langley-1.oraclegovcloud.com/20180401/metrics/actions/summarizeMetricsData'

    body = {
      'namespace': 'oci_autonomous_database',
      'query': 'CpuUtilization[3h]{resourceId = "' + rId + '"}.mean()',
      'resolution': '3h'
      # "query": 'CpuUtilization[3h].mean()',
      # "startTime": "2026-10-03T00:00:00.000Z",    # defaults to 3 hours ago
      # "endTime": "2026-10-06T00:00:00.000Z",      # defaults to now
    }

    r = loci.post_api_data(auth, endpoint, cId, body).json()

    if (r):

        cpuUtilization_3hr = r[0]['aggregatedDatapoints'][0]['value']
        return cpuUtilization_3hr

    else:

        print('no metrics')
        return 0




# Using the AWS key here because I didn't want to ask for another HEC key from the Splunk team.
# This is fine because we can change the "source" and "sourcetype" to be whatever we want.

key_for_aws = 'Splunk efdb579f-f40b-42c4-957d-62b8a4773f9d'



# OCI authentication

config, auth = loci.authenticate()



# ----------------------------------------------------------------------------------------------
# Get a list of compartments to search.
# Either build it manually or use a pre-built list.
# ----------------------------------------------------------------------------------------------

cl = []

# rc = 'ocid1.tenancy.oc2..aaaaaaaabyiqtmraqqks242f4jacxlsxg3qdjyzvni32c4a7s67ueye7j2eq'
# cl = loci.get_all_compartments(auth, rc)

print('using pre-existing compartment list (oci_compartments)')
with open('oci_compartments', 'r') as file:
    for c in file:
        cl.append(c.strip())



# ----------------------------------------------------------------------------------------------
# data collection
# search the list of compartments for autonomous database details
# 'adb' is a list of Autonomous DataBase (ADB) details
# ----------------------------------------------------------------------------------------------

adb = []
endpoint = 'database.us-langley-1.oraclegovcloud.com/20160918/autonomousDatabases'

for compartmentId in cl:

    print('looking for ADBs in compartmentId ' + compartmentId)
    r = loci.fetch_api_data( auth, endpoint, compartmentId ).json()

    if ( isinstance(r, list) ):
        for i in r:
            adb.append(i)



# ----------------------------------------------------------------------------------------------
# The JSON for an ADB is large. We don't need all that data; instead of sending it all to
# Splunk we keep only what we want and throw the rest away.
# Also we modify the "source" and "sourcetype" of the results.
# ----------------------------------------------------------------------------------------------

print()
batch_payload = []

for db in adb:

    # For every ADB, collect the CPU utilization metrics
    # and send a payload to Splunk under a different 'sourcetype.'

    metrics_payload = {
        'compartmentId': db['compartmentId'],
        'id': db['id'],
        'dbName': db['dbName'],
        'displayName': db['displayName'],
        'lifecycleState': db['lifecycleState'],
    }

    print(f"fetching adb cpuUtilization metrics for {db['dbName']}")
    metrics_payload['cpuUtilization_3hr'] = fetch_adb_cpuUtilization_metrics( auth, db['compartmentId'], db['id'] )

    print(f"fetching adb session metrics for {db['dbName']}")
    metrics_payload['sessionUtilization_3hr'] = fetch_adb_session_metrics( auth, db['compartmentId'], db['id'] )

    print(f"fetching adb number of session metrics for {db['dbName']}")
    metrics_payload['numSessions_3hr'] = fetch_adb_numSessions_metrics( auth, db['compartmentId'], db['id'] )

    print('session metrics:')
    print(metrics_payload)

    print('shipping adb metrics payload to Splunk')
    splunk.deliver_payload(metrics_payload, 'adb_metrics', key_for_aws, source='OCI')

    selected_fields_db = {}

    selected_fields_db['compartmentId'] = db['compartmentId']
    selected_fields_db['id'] = db['id']
    selected_fields_db['dbName'] = db['dbName']
    selected_fields_db['displayName'] = db['displayName']
    selected_fields_db['dbVersion'] = db['dbVersion']
    selected_fields_db['computeModel'] = db['computeModel']
    selected_fields_db['computeCount'] = db['computeCount']
    selected_fields_db['allocatedStorageSizeInTBs'] = db['allocatedStorageSizeInTBs']
    selected_fields_db['actualUsedDataStorageSizeInTBs'] = db['actualUsedDataStorageSizeInTBs']
    selected_fields_db['dataStorageSizeInGBs'] = db['dataStorageSizeInGBs']
    selected_fields_db['usedDataStorageSizeInGBs'] = db['usedDataStorageSizeInGBs']
    selected_fields_db['isAutoScalingEnabled'] = db['isAutoScalingEnabled']
    selected_fields_db['isAutoScalingForStorageEnabled'] = db['isAutoScalingForStorageEnabled']
    selected_fields_db['isDataGuardEnabled'] = db['isDataGuardEnabled']
    selected_fields_db['lifecycleState'] = db['lifecycleState']
    selected_fields_db['memoryPerComputeUnitInGBs'] = db['memoryPerComputeUnitInGBs']
    selected_fields_db['dataSafeStatus'] = db['dataSafeStatus']
    selected_fields_db['backupConfig'] = db['backupConfig']
    selected_fields_db['backupDestination'] = db['backupDestination']
    selected_fields_db['backupRetentionPeriodInDays'] = db['backupRetentionPeriodInDays']
    selected_fields_db['byolComputeCountLimit'] = db['byolComputeCountLimit']

    batch_payload.append( {'source': 'OCI', 'sourcetype': 'ADB', 'event': selected_fields_db} )



# ----------------------------------------------------------------------------------------------
# Send a batch payload to Splunk.
# ----------------------------------------------------------------------------------------------

print('delivering batch payload to Splunk')
splunk.deliver_batch_payload(batch_payload, key_for_aws)


