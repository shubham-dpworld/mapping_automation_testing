import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from collections import OrderedDict

folder_id = 'Rjo3NjQ3ODEx'
folder_path = 'DPW Sub Account 1/ZZZ_Users/Mapping Automation'
branch_id = 'Qjo2OTgxOA'
branch_name = 'main'
boomi_component_bns_url = 'http://api.platform.boomi.com/'
boomi_component_xsi_url = 'http://www.w3.org/2001/XMLSchema-instance'

def process_obj(obj_elem, data, key_counter):
    for field_name, value in data.items():
        key_counter[0] += 1
        field_key = str(key_counter[0])

        if isinstance(value, bool):
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "boolean", "isMappable": "true", "isNode": "true",
                "key": field_key, "name": field_name
            })
            SubElement(entry, "DataFormat")

        elif isinstance(value, (int, float)):
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "number", "isMappable": "true", "isNode": "true",
                "key": field_key, "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileNumberFormat", {"numberFormat": ""})

        elif isinstance(value, str):
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character", "isMappable": "true", "isNode": "true",
                "key": field_key, "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

        elif isinstance(value, dict):
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character", "isMappable": "true", "isNode": "true",
                "key": field_key, "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

            key_counter[0] += 1
            inner_obj = SubElement(entry, "JSONObject", {
                "isMappable": "false", "isNode": "true",
                "key": str(key_counter[0]), "name": "Object"
            })
            process_obj(inner_obj, value, key_counter)

        elif isinstance(value, list):
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character", "isMappable": "true", "isNode": "true",
                "key": field_key, "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

            key_counter[0] += 1
            array = SubElement(entry, "JSONArray", {
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

            if value and isinstance(value[0], dict):
                key_counter[0] += 1
                inner_obj = SubElement(element, "JSONObject", {
                    "isMappable": "false", "isNode": "true",
                    "key": str(key_counter[0]), "name": "Object"
                })
                process_obj(inner_obj, value[0], key_counter)


def generate_profile_xml(json_data,isSource=True):
    component = Element("bns:Component", {
        "xmlns:bns": boomi_component_bns_url,
        "xmlns:xsi": boomi_component_xsi_url,
        "branchId": branch_id,
        "branchName": branch_name,
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": folder_path,
        "folderId": folder_id,
        "folderName": folder_path.split("/")[-1],
        "name": "sourceProfile" if isSource else "destinationProfile",
        "type": "profile.json",
        "version": "1"
    })

    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description")
    bns_object = SubElement(component, "bns:object")
    profile = SubElement(bns_object, "JSONProfile", {"strict": "false"})
    data_elements = SubElement(profile, "DataElements")

    root = SubElement(data_elements, "JSONRootValue", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": "1", "name": "Root"
    })
    SubElement(root, "DataFormat").append(Element("ProfileCharacterFormat"))

    key_counter = [1]  # start at 1 to match Root's key

    if isinstance(json_data, list):
        key_counter[0] += 1
        array = SubElement(root, "JSONArray", {
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

        if json_data and isinstance(json_data[0], dict):
            key_counter[0] += 1
            obj = SubElement(element, "JSONObject", {
                "isMappable": "false", "isNode": "true",
                "key": str(key_counter[0]), "name": "Object"
            })
            process_obj(obj, json_data[0], key_counter)

    else:
        # Not expected, but fallback for object root
        key_counter[0] += 1
        obj = SubElement(root, "JSONObject", {
            "isMappable": "false", "isNode": "true",
            "key": str(key_counter[0]), "name": "Object"
        })
        process_obj(obj, json_data, key_counter)

    qualifiers = SubElement(root, "Qualifiers")
    SubElement(qualifiers, "QualifierList")
    SubElement(profile, "tagLists")

    return parseString(tostring(component, encoding="utf-8")).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")


if __name__ == "__main__":
    with open("/Users/ankit.raj/Developer/mapping_automation_testing/Imporntant/jsonProfileSample.json", "r") as f:
        json_obj = json.load(f, object_pairs_hook=OrderedDict)

    # json_data = json.loads(json_obj)
    xml_output = generate_profile_xml(json_obj)

    with open("/Users/ankit.raj/Developer/mapping_automation_testing/Imporntant/jsonProfileXml.xml", "w") as f:
        f.write(xml_output)

    print("✅ Boomi XML generated successfully.")
