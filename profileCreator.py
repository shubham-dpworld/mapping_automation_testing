import json
from xml.etree.ElementTree import Element, SubElement, tostring  # For building XML
from xml.dom.minidom import parseString  # For pretty printing the XML
from collections import OrderedDict  # To preserve JSON key order


def process_obj(obj_elem, data, key_counter):
    for field_name, value in data.items():
        key_counter[0] += 1
        field_key = str(key_counter[0])

        if isinstance(value, bool):
            # Boolean entry (no format element inside DataFormat)
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "boolean",
                "isMappable": "true",
                "isNode": "true",
                "key": field_key,
                "name": field_name
            })
            SubElement(entry, "DataFormat")  # leave empty for boolean

        elif isinstance(value, (int, float)):
            # Number entry with number format
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "number",
                "isMappable": "true",
                "isNode": "true",
                "key": field_key,
                "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileNumberFormat", {"numberFormat": ""})

        elif isinstance(value, str):
            # Character (string) entry
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character",
                "isMappable": "true",
                "isNode": "true",
                "key": field_key,
                "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

        elif isinstance(value, dict):
            # Nested object
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character",
                "isMappable": "true",
                "isNode": "true",
                "key": field_key,
                "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")
            key_counter[0] += 1
            inner_obj = SubElement(entry, "JSONObject", {
                "isMappable": "false",
                "isNode": "true",
                "key": str(key_counter[0]),
                "name": "Object"
            })
            process_obj(inner_obj, value, key_counter)

        elif isinstance(value, list):
            # Array of objects
            entry = SubElement(obj_elem, "JSONObjectEntry", {
                "dataType": "character",
                "isMappable": "true",
                "isNode": "true",
                "key": field_key,
                "name": field_name
            })
            df = SubElement(entry, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

            key_counter[0] += 1
            array = SubElement(entry, "JSONArray", {
                "elementType": "repeating",
                "isMappable": "false",
                "isNode": "true",
                "key": str(key_counter[0]),
                "name": "Array"
            })

            key_counter[0] += 1
            element = SubElement(array, "JSONArrayElement", {
                "dataType": "character",
                "isMappable": "true",
                "isNode": "true",
                "key": str(key_counter[0]),
                "maxOccurs": "-1",
                "minOccurs": "0",
                "name": "ArrayElement1"
            })
            df = SubElement(element, "DataFormat")
            SubElement(df, "ProfileCharacterFormat")

            key_counter[0] += 1
            inner_obj = SubElement(element, "JSONObject", {
                "isMappable": "false",
                "isNode": "true",
                "key": str(key_counter[0]),
                "name": "Object"
            })

            # Process only first item in array (Boomi-style)
            if value:
                process_obj(inner_obj, value[0], key_counter)

def generate_xml(json_data):
    # Create the root <Component> with Boomi metadata attributes
    component = Element("bns:Component", {
        "xmlns:bns": "http://api.platform.boomi.com/",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "branchId": "Qjo2OTgxOA",
        "branchName": "main",
        # "componentId": "a486e148-1e20-4de1-8dc7-e3a265ac0d7e",
        # "createdBy": "ankit.raj@dpworld.com",
        # "createdDate": "2025-04-10T06:01:48Z",
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": "DPW Sub Account 1/ZZZ_Users/Mapping Automation",
        "folderId": "Rjo3NjI1Mzcz",
        "folderName": "Automation",
        # "modifiedBy": "ankit.raj@dpworld.com",
        # "modifiedDate": "2025-04-10T06:19:25Z",
        "name": "destinationProfile",
        "type": "profile.json",
        "version": "1"
    })

    # Required static fields
    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description")

    # Start of actual profile definition
    bns_object = SubElement(component, "bns:object")
    profile = SubElement(bns_object, "JSONProfile", {"strict": "false"})
    data_elements = SubElement(profile, "DataElements")

    # Define the root of JSON
    root = SubElement(data_elements, "JSONRootValue", {
        "dataType": "character",
        "isMappable": "true",
        "isNode": "true",
        "key": "1",
        "name": "Root"
    })

    # Root data format
    SubElement(root, "DataFormat").append(Element("ProfileCharacterFormat"))

    # Root JSONObject wrapper
    obj = SubElement(root, "JSONObject", {
        "isMappable": "false",
        "isNode": "true",
        "key": "2",
        "name": "Object"
    })

    # Recursive function to process objects and nested structures

    # Kick off processing with key counter starting at 2
    process_obj(obj, json_data, [2])

    # Append required closing tags
    qualifiers = SubElement(root, "Qualifiers")
    SubElement(qualifiers, "QualifierList")
    SubElement(profile, "tagLists")

    # Convert to pretty printed XML string
    return parseString(tostring(component, encoding="utf-8")).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")


if __name__ == "__main__":
    # Load JSON file and preserve key order
    with open("/Users/shubham.s/Desktop/mapping_automation_testing/destinationJson.json", "r") as f:
        json_obj = json.load(f, object_pairs_hook=OrderedDict)
        print(json_obj)

    # Generate XML
    xml_output = generate_xml(json_obj)

    # Write to file
    with open("/Users/shubham.s/Desktop/mapping_automation_testing/destinationProfile.xml", "w") as f:
        f.write(xml_output)

    print("Boomi XML generated to output.xml ✅")
 