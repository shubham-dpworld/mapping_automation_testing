import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from collections import OrderedDict
from copy import deepcopy

# Constants
FOLDER_ID = 'Rjo3NjQ3ODEx'
FOLDER_PATH = 'DPW Sub Account 1/ZZZ_Users/Mapping Automation'
BRANCH_ID = 'Qjo2OTgxOA'
BRANCH_NAME = 'main'
BOOMI_COMPONENT_BNS_URL = 'http://api.platform.boomi.com/'
BOOMI_COMPONENT_XSI_URL = 'http://www.w3.org/2001/XMLSchema-instance'

# --------------------------- Core XML Builders ---------------------------

def create_component_root(is_source=True):
    component =  Element("bns:Component", {
        "xmlns:bns": BOOMI_COMPONENT_BNS_URL,
        "xmlns:xsi": BOOMI_COMPONENT_XSI_URL,
        "branchId": BRANCH_ID,
        "branchName": BRANCH_NAME,
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": FOLDER_PATH,
        "folderId": FOLDER_ID,
        "folderName": FOLDER_PATH.split("/")[-1],
        "name": "sourceProfile" if is_source else "destinationProfile",
        "type": "profile.json", #need change
        "version": "1"
    })
    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description")
    return component


def create_root_profile_structure(component_elem):
    bns_object = SubElement(component_elem, "bns:object")
    profile = SubElement(bns_object, "JSONProfile", {"strict": "false"})
    data_elements = SubElement(profile, "DataElements")

    root = SubElement(data_elements, "JSONRootValue", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": "1", "name": "Root"
    })
    SubElement(root, "DataFormat").append(Element("ProfileCharacterFormat"))

    SubElement(root, "Qualifiers").append(Element("QualifierList"))
    SubElement(profile, "tagLists")

    return profile, root

# --------------------------- Recursive Processing ---------------------------

def process_object_entries(obj_elem, data, key_counter):
    for field_name, value in data.items():
        key_counter[0] += 1
        field_key = str(key_counter[0])

        entry = SubElement(obj_elem, "JSONObjectEntry", {
            "dataType": get_data_type(value),
            "isMappable": "true", "isNode": "true",
            "key": field_key, "name": field_name
        })

        df = SubElement(entry, "DataFormat")
        add_format(df, value)

        if isinstance(value, dict):
            key_counter[0] += 1
            inner_obj = SubElement(entry, "JSONObject", {
                "isMappable": "false", "isNode": "true",
                "key": str(key_counter[0]), "name": "Object"
            })
            process_object_entries(inner_obj, value, key_counter)

        elif isinstance(value, list):
            process_array(entry, value, key_counter)

def process_array(parent_elem, array_value, key_counter):
    key_counter[0] += 1
    array = SubElement(parent_elem, "JSONArray", {
        "elementType": "repeating", "isMappable": "false", "isNode": "true",
        "key": str(key_counter[0]), "name": "Array"
    })

    key_counter[0] += 1
    element = SubElement(array, "JSONArrayElement", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": str(key_counter[0]), "maxOccurs": "-1", "minOccurs": "0", "name": "ArrayElement1"
    })
    df = SubElement(element, "DataFormat")
    SubElement(df, "ProfileCharacterFormat")

    if array_value and isinstance(array_value[0], dict):
        key_counter[0] += 1
        inner_obj = SubElement(element, "JSONObject", {
            "isMappable": "false", "isNode": "true",
            "key": str(key_counter[0]), "name": "Object"
        })
        process_object_entries(inner_obj, array_value[0], key_counter)

# --------------------------- Helpers ---------------------------

def get_data_type(value):
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, (int, float)):
        return "number"
    return "character"

def add_format(df_elem, value):
    if isinstance(value, bool):
        return  # boolean: do not add <ProfileBooleanFormat/>
    elif isinstance(value, (int, float)):
        SubElement(df_elem, "ProfileNumberFormat", {"numberFormat": ""})
    else:
        SubElement(df_elem, "ProfileCharacterFormat")

# --------------------------- Main Generator ---------------------------

def generate_profile_xml(raw_json, is_source=True):
    json_data = json.loads(raw_json, object_pairs_hook=OrderedDict)

    component = create_component_root(is_source)
    profile, root = create_root_profile_structure(component)

    key_counter = [1]

    if isinstance(json_data, list):
        process_array(root, json_data, key_counter)
    elif isinstance(json_data, dict):
        key_counter[0] += 1
        obj = SubElement(root, "JSONObject", {
            "isMappable": "false", "isNode": "true",
            "key": str(key_counter[0]), "name": "Object"
        })
        process_object_entries(obj, json_data, key_counter)

    return parseString(tostring(component, encoding="utf-8")).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")

# --------------------------- Main Entry ---------------------------

def main():
    # ✅ Raw JSON string input
    raw_json = '''
    [
      {
            "name":"shubham",
            "discrepancyTypeCode": "string",
            "visitStatusCode": "string",
            "shortlandCount": "integer",
            "docTypeCode": "string",
            "bolUserDefinedCode3": "string",
            "qty": "integer",
            "tests": {
                  "test1": "this is test1",
                  "test2": "this is test2"
            },
            "testArray": [
                  {
                        "name": "value"
                  },
                  {
                        "name":""
                  }
            ]
        }
    ]
    '''

    # Parse raw JSON string to OrderedDict to preserve key order

    # Assuming this function is defined elsewhere
    xml_output = generate_profile_xml(raw_json)

    with open("sourceProfile.xml", "w") as f:
        f.write(xml_output)

    print("✅ Boomi XML generated successfully.")


    
    
    
    
def get_most_complete_object(objects):
    """
    From a list of dicts, return the one with the most keys (i.e., most complete).
    """
    if not objects:
        return []
    
    max_len = max(len(obj.keys()) for obj in objects if isinstance(obj, dict))
    return [obj for obj in objects if isinstance(obj, dict) and len(obj.keys()) == max_len]


def clean_json(obj):
    """
    Recursively walk the JSON and clean lists of dicts to keep only the most complete ones.
    """
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if all(isinstance(item, dict) for item in obj):
            return get_most_complete_object(obj)
        else:
            return obj  # don't modify lists of primitives
    else:
        return obj




if __name__ == "__main__":
    incorrect_json = {
  "Company": {
    "Teams": [
      {
        "TeamName": "Alpha",
        "Members": [
          { "ID": 1, "Name": "Tom" },
          { "ID": 2, "Name": "Jerry", "Role": "Tester" }
        ]
      },
      {
        "TeamName": "Beta",
        "Members": [
          { "ID": 3 },
          { "ID": 4, "Name": "Spike", "Role": "Developer", "Experience": 3 }
        ]
      }
    ]
  }
}
    
    
    

    cleaned = clean_json(incorrect_json)
    print(json.dumps(cleaned, indent=4))

    # main()
    