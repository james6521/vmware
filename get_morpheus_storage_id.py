import requests
import json
requests.packages.urllib3.disable_warnings() 


MORPHEUS_TOKEN = morpheus['morpheus']['apiAccessToken']
MORPHEUS_HEADERS = {"Authorization": "Bearer " + (MORPHEUS_TOKEN)}
VERIFY_SSL_CERT = False
MORPHEUS_HOST = "192.168.100.240"

MAX_API_RESULTS=1000000
MORPHEUS_DATASTORE_OPTION_LIST_NAME = "Morpheus vCenter Datastores"
DATASTORE_POLICIES_LIST_NAME = "vCenter Storage Policies"
CLOUD_OPTION_LIST_NAME = "VMware Clouds"

def get_morpheus_option_list_data_by_name(option_list_name):
    url = "https://%s/api/library/option-type-lists" % (MORPHEUS_HOST)
    params={"name": option_list_name, "max": MAX_API_RESULTS }
    response = requests.get(url, headers=MORPHEUS_HEADERS, params=params, verify=VERIFY_SSL_CERT)
    
    
    if not response.ok:
        raise Exception("Error retrieving option list from Morpheus: Response code %s: %s" % (response.status_code, response.text))
    
    
    opts = response.json()["optionTypeLists"]
    if len(opts) == 0:
        raise Exception("Option list %s not found in Morpheus: Response code %s: %s" % (option_list_name, response.status_code, response.text))
    
    return opts[0]["initialDataset"]  



def get_datastore_vcenter_name_by_mopheus_id(id, dataset):
    for datastore in dataset:
        if str(datastore["morpheus_id"]) == str(id):
            return datastore["datastore"]
    
    
morpheus_id = morpheus["customOptions"]["morpheusVCDatastore"]
ds_data = get_morpheus_option_list_data_by_name(MORPHEUS_DATASTORE_OPTION_LIST_NAME)
vcenter_ds_name = get_datastore_vcenter_name_by_mopheus_id(morpheus_id, json.loads(ds_data))

print("vCenter Datastore Name: %s" % vcenter_ds_name)