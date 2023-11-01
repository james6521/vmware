import json
import requests
import sys
requests.packages.urllib3.disable_warnings()


VCENTER_HEADERS = {"Content-Type": "application/json"}
VCENTER_HOST = "192.168.100.200"
VCENTER_USER = sys.argv[1]
VCENTER_PASSWORD = sys.argv[2]
VCENTER_TOKEN = ""
VCENTER_URL = "https://" + VCENTER_HOST + "/rest/vcenter"
VERIFY_SSL_CERT = False
MAX_API_RESULTS=1000000
DATASTORE_OPTION_LIST_NAME = "vCenter Datastores"
DATASTORE_POLICIES_LIST_NAME = "vCenter Storage Policies"


def get_vcenter_auth_token(uid, pwd):
    url = "https://" + VCENTER_HOST + "/rest/com/vmware/cis/session"
    response = requests.post(url, auth=(uid, pwd), verify=VERIFY_SSL_CERT)

    if not response.ok:
        raise Exception("Error creating new vCenter auth session: Response code %s: %s" % (response.status_code, response.text))

    return response.json()["value"]



def set_datastores_policy(vm_id, storagepolicy_id):
    url = VCENTER_URL + "/vm/%s/storage/policy" %(vm_id)
    VCENTER_HEADERS["vmware-api-session-id"] = VCENTER_TOKEN
  
    body = {
        "spec": {
            "disks": [],
            "vm_home": {
                "policy": storagepolicy_id,
                "type": "USE_SPECIFIED_POLICY"
            }
        }
    }
    
    for volume in morpheus["instance"]["containers"][0]["server"]["volumes"]:
        body["spec"]["disks"].append(
            {
               "key": volume["externalId"],
                "value": {
                    "policy": storagepolicy_id,
                    "type": "USE_SPECIFIED_POLICY"
                }
            }
        )
    
 
    response = requests.patch(url, data=json.dumps(body), headers=VCENTER_HEADERS, verify=VERIFY_SSL_CERT)
	
 	
    if not response.ok:
        raise Exception("Error Setting Policy for datastore %s: %s" % (response.status_code, response.text))



### MAIN ###
VCENTER_TOKEN = get_vcenter_auth_token(VCENTER_USER, VCENTER_PASSWORD)
vm_id = morpheus["server"]["externalId"]
##datastore_id= morpheus["input"]["config"]["customOptions"]["vcenterDatastores"]
storagepolicy_id= morpheus["input"]["config"]["customOptions"]["vcenterPolicy"]
vmpolicy=set_datastores_policy(vm_id, storagepolicy_id)