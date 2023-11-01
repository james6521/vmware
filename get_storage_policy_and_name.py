import json
import requests
import sys
from urllib.parse import urlparse
requests.packages.urllib3.disable_warnings()
    
 
MORPHEUS_TOKEN = morpheus['morpheus']['apiAccessToken']
VCENTER_HEADERS = {"Content-Type": "application/json"}
VCENTER_HOST = "192.168.100.200"
VCENTER_USER = sys.argv[1]
VCENTER_PASSWORD = sys.argv[2]
VERIFY_SSL_CERT = False
MORPHEUS_HOST = "192.168.100.161"
MORPHEUS_HEADERS = {"Authorization": "Bearer " + (MORPHEUS_TOKEN)}
MAX_API_RESULTS=1000000
MORPHEUS_DATASTORE_OPTION_LIST_NAME = "VMware Datastores"
DATASTORE_POLICIES_LIST_NAME = "VMware Storage Policies"
CLOUD_OPTION_LIST_NAME = "VMware Clouds"
    
 
 
def get_morpheus_enabled_vcenter_clouds():
 
    url = "https://%s/api/zones" % (MORPHEUS_HOST)
    params={"max": MAX_API_RESULTS }
    response = requests.get(url, headers=MORPHEUS_HEADERS, params=params, verify=VERIFY_SSL_CERT)
    
    if not response.ok:
        raise Exception("Error retrieving vCenter clouds from Morpheus: Response code %s: %s" % (response.status_code, response.text))
    
    rtn = []
    for zone in response.json()["zones"]:
        if zone["zoneType"]["code"] == "vmware" and zone["enabled"] == True:
            print("Adding cloud of type: " + zone["zoneType"]["code"] + ", with name " + zone["name"])
            rtn.append(zone)
 
    return rtn
 
 
 
def get_vcenter_auth_token(vcenter_host, uid, pwd):
    url = "https://" + vcenter_host + "/rest/com/vmware/cis/session"
    response = requests.post(url, auth=(uid, pwd), verify=VERIFY_SSL_CERT)
    
    if not response.ok:
        raise Exception("Error creating new vCenter auth session: Response code %s: %s" % (response.status_code, response.text))
    
    return response.json()["value"]
    
    
    
def get_vcenter_datastores(vcenter_host, vcenter_token, morpheus_datastores):
    url = "https://" + vcenter_host + "/rest/vcenter/datastore"
    VCENTER_HEADERS["Authorization"] = "Bearer " + vcenter_token
    cookies = {"vmware-api-session-id": vcenter_token}
    response = requests.get(url, headers=VCENTER_HEADERS, verify=VERIFY_SSL_CERT, cookies=cookies)
    
    if not response.ok:
        raise Exception("Error getting datastores from vCenter: Response code %s: %s" % (response.status_code, response.text))
    
    vc_dss = response.json()["value"]
    for ds in vc_dss:
        if ds["name"] in morpheus_datastores:
            ds["morpheus_id"] = morpheus_datastores[ds["name"]]["id"]
        else:
            print("Datastore %s not found in Morpheus" % (ds["name"]))
    
    return vc_dss
 
 
 
def get_morpheus_datastores(zone_id):
 
    url = "https://%s/api/zones/%s/data-stores" % (MORPHEUS_HOST, zone_id)
    params={"max": MAX_API_RESULTS }
    response = requests.get(url, headers=MORPHEUS_HEADERS, params=params, verify=VERIFY_SSL_CERT)
    
    if not response.ok:
        raise Exception("Error retrieving datastores from Morpheus for cloud id %s: Response code %s: %s" % (response.status_code, response.text, zone_id))
    
    rtn = {}
    for ds in response.json()["datastores"]:
        rtn[ds["name"]] = ds
 
    return rtn
 
 
    
def get_vcenter_storage_policies(vcenter_host, vcenter_token):
    url = "https://" + vcenter_host + "/rest/vcenter/storage/policies"
    VCENTER_HEADERS["Authorization"] = "Token " + vcenter_token
    cookies = {"vmware-api-session-id": vcenter_token}
    response = requests.get(url, headers=VCENTER_HEADERS, verify=VERIFY_SSL_CERT, cookies=cookies)
    
    if not response.ok:
        raise Exception("Error getting Policies from vCenter: Response code %s: %s" % (response.status_code, response.text))
    
    return response.json()["value"]
    
    
    
def add_vcenter_storage_compaitibility(vcenter_host, vcenter_token, datastore_ids, policy):
    url = "https://" + vcenter_host + "/rest/vcenter/storage/policies/" + policy["policy"] + "?action=check-compatibility"
    VCENTER_HEADERS["Authorization"] = "Token " + vcenter_token
    cookies = {"vmware-api-session-id": vcenter_token}
    params = { "action": "check-compaitibility"}
    body = {
        "datastores": datastore_ids
    }
    
    response = requests.post(url, data=json.dumps(body), headers=VCENTER_HEADERS, params=params, verify=VERIFY_SSL_CERT, cookies=cookies)
    
    if not response.ok:
        raise Exception("Error checking compatability of Datastore %s against Policy %s: Response code %s: %s" % (json.dumps(datastore_ids), json.dumps(policy), response.status_code, response.text))
    
    policy["compatible_datastores"] = []
    compatible_datastores = response.json()["value"]["compatible_datastores"]
    for ds in compatible_datastores:
        policy["compatible_datastores"].append(ds["datastore"])
        
    
    
def get_morpheus_option_list_id_by_name(option_list_name):
    url = "https://%s/api/library/option-type-lists" % (MORPHEUS_HOST)
    params={"name": option_list_name, "max": MAX_API_RESULTS }
    response = requests.get(url, headers=MORPHEUS_HEADERS, params=params, verify=VERIFY_SSL_CERT)
    
    
    if not response.ok:
        raise Exception("Error retrieving option list from Morpheus: Response code %s: %s" % (response.status_code, response.text))
    
    
    opts = response.json()["optionTypeLists"]
    if len(opts) == 0:
        raise Exception("Option list %s not found in Morpheus: Response code %s: %s" % (option_list_name, response.status_code, response.text))
    
    return opts[0]["id"]  
    
    
def update_morpheus_option_list(option_list_id, initial_data):
    url = "https://%s/api/library/option-type-lists/%s" % (MORPHEUS_HOST, option_list_id)
    body={
        "optionTypeList": {
            "initialDataset": initial_data
        }
    }
    response = requests.put(url, headers=MORPHEUS_HEADERS, data=json.dumps(body), verify=VERIFY_SSL_CERT)
    
    
    if not response.ok:
        raise Exception("Unable to update Option list %s in Morpheus: Response code %s: %s" % (option_list_id, response.status_code, response.text))
    
    
    
    
### MAIN ###
 
#print(VCENTER_TOKEN)
 
all_datastores = []
vcenter_clouds = get_morpheus_enabled_vcenter_clouds()
for cloud in vcenter_clouds:
    host = urlparse(cloud["config"]["apiUrl"]).netloc
    vcenter_token = get_vcenter_auth_token(host, VCENTER_USER, VCENTER_PASSWORD)
    
    morpheus_datastores = get_morpheus_datastores(cloud["id"])
    vc_datastores = get_vcenter_datastores(host, vcenter_token, morpheus_datastores)
    vc_policies = get_vcenter_storage_policies(host, vcenter_token)
    
    
    datastore_ids = []
    for datastore in vc_datastores:
        datastore_ids.append(datastore["datastore"])
    
    for policy in vc_policies:
        add_vcenter_storage_compaitibility(host, vcenter_token, datastore_ids, policy)
    
    
    for datastore in vc_datastores:
        datastore["cloud_id"] = cloud["id"]
        datastore["compatible_policies"]=[]
        for policy in vc_policies:
            if datastore["datastore"] in policy["compatible_datastores"]:
                datastore["compatible_policies"].append(policy["policy"])
        all_datastores.append(datastore)
 
    
 
 
ds_opts_id = get_morpheus_option_list_id_by_name(MORPHEUS_DATASTORE_OPTION_LIST_NAME)
update_morpheus_option_list(ds_opts_id, json.dumps(all_datastores))
    
policy_opts_id = get_morpheus_option_list_id_by_name(DATASTORE_POLICIES_LIST_NAME)
update_morpheus_option_list(policy_opts_id, json.dumps(vc_policies))
 
cloud_opts_id = get_morpheus_option_list_id_by_name(CLOUD_OPTION_LIST_NAME)
update_morpheus_option_list(cloud_opts_id, json.dumps(vcenter_clouds))