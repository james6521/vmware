import json
import requests
import sys
requests.packages.urllib3.disable_warnings()


MORPHEUS_TOKEN = morpheus['morpheus']['apiAccessToken']
VCENTER_HEADERS = {"Content-Type": "application/json"}
VCENTER_HOST = "192.168.100.200"
VCENTER_USER = sys.argv[1]
VCENTER_PASSWORD = sys.argv[2]
VCENTER_TOKEN = ""
VCENTER_URL = "https://" + VCENTER_HOST + "/rest/vcenter"
VERIFY_SSL_CERT = False
MORPHEUS_HOST = "192.168.100.161"
MORPHEUS_HEADERS = {"Authorization": "Bearer " + (MORPHEUS_TOKEN)}
MAX_API_RESULTS=1000000
DATASTORE_OPTION_LIST_NAME = "VMware Datastores"
DATASTORE_POLICIES_LIST_NAME = "VMware Storage Policies"


def get_vcenter_auth_token(uid, pwd):
    url = "https://" + VCENTER_HOST + "/rest/com/vmware/cis/session"
    response = requests.post(url, auth=(uid, pwd), verify=VERIFY_SSL_CERT)

    if not response.ok:
        raise Exception("Error creating new vCenter auth session: Response code %s: %s" % (response.status_code, response.text))

    return response.json()["value"]



def get_datastores():
    url = VCENTER_URL + "/datastore"
    VCENTER_HEADERS["Authorization"] = "Bearer " + VCENTER_TOKEN
    cookies = {"vmware-api-session-id": VCENTER_TOKEN}
    response = requests.get(url, headers=VCENTER_HEADERS, verify=VERIFY_SSL_CERT, cookies=cookies)

    if not response.ok:
        raise Exception("Error getting datastores from vCenter: Response code %s: %s" % (response.status_code, response.text))

    return response.json()



def get_storage_policies():
    url = VCENTER_URL + "/storage/policies"
    VCENTER_HEADERS["Authorization"] = "Token " + VCENTER_TOKEN
    cookies = {"vmware-api-session-id": VCENTER_TOKEN}
    response = requests.get(url, headers=VCENTER_HEADERS, verify=VERIFY_SSL_CERT, cookies=cookies)
 
    if not response.ok:
        raise Exception("Error getting Policies from vCenter: Response code %s: %s" % (response.status_code, response.text))

    return response.json()



def add_storage_compaitibility(datastore_ids, policy):
    url = VCENTER_URL + "/storage/policies/" + policy["policy"] + "?action=check-compatibility"
    print(url)
    VCENTER_HEADERS["Authorization"] = "Token " + VCENTER_TOKEN
    cookies = {"vmware-api-session-id": VCENTER_TOKEN}
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
        


def get_option_list_id_by_name(option_list_name):
    url = "https://%s/api/library/option-type-lists" % (MORPHEUS_HOST)
    params={"name": option_list_name, "max": MAX_API_RESULTS }
    response = requests.get(url, headers=MORPHEUS_HEADERS, params=params, verify=VERIFY_SSL_CERT)

 
    if not response.ok:
        raise Exception("Error retrieving option list from Morpheus: Response code %s: %s" % (response.status_code, response.text))

 
    opts = response.json()["optionTypeLists"]
    if len(opts) == 0:
        raise Exception("Option list %s not found in Morpheus: Response code %s: %s" % (option_list_name, response.status_code, response.text))

    return opts[0]["id"]  


def update_option_list(option_list_id,initial_data):
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
VCENTER_TOKEN = get_vcenter_auth_token(VCENTER_USER, VCENTER_PASSWORD)
#print(VCENTER_TOKEN)
datastores = get_datastores()

#print(json.dumps(datastores, indent=4))
policies = get_storage_policies()


datastore_ids = []
for datastore in datastores["value"]:
    datastore_ids.append(datastore["datastore"])
    
for policy in policies["value"]:
    add_storage_compaitibility(datastore_ids, policy)


for datastore in datastores["value"]:
    datastore["compatible_policies"]=[]
    for policy in policies["value"]:
        if datastore["datastore"] in policy["compatible_datastores"]:
            datastore["compatible_policies"].append(policy["policy"])
    
    
    
print(json.dumps(policies, indent=4))

ds_opts_id=get_option_list_id_by_name(DATASTORE_OPTION_LIST_NAME)

update_option_list(ds_opts_id, json.dumps(datastores["value"]))

policy_opts_id=get_option_list_id_by_name(DATASTORE_POLICIES_LIST_NAME)

update_option_list(policy_opts_id, json.dumps(policies["value"]))