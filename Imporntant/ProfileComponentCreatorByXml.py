import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

folder_id = 'Rjo3NjQ3ODEx'
folder_path = 'DPW Sub Account 1/ZZZ_Users/Mapping Automation'
branch_id = 'Qjo2OTgxOA'
branch_name = 'main'
boomi_component_bns_url = 'http://api.platform.boomi.com/'
boomi_component_xsi_url = 'http://www.w3.org/2001/XMLSchema-instance'


def process_xml_element(obj_elem, element, key_counter):
    key_counter[0] += 1
    field_key = str(key_counter[0])

    # Create the XMLElement for the current tag
    entry = SubElement(obj_elem, "XMLElement", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": field_key, "name": element.tag,
        "maxOccurs": "1", "minOccurs": "0", "useNamespace": "-1"
    })

    df = SubElement(entry, "DataFormat")
    SubElement(df, "ProfileCharacterFormat")

    # ✅ Handle XML attributes if present
    for attr_name in element.attrib:
        key_counter[0] += 1
        attr_key = str(key_counter[0])
        attr_elem = SubElement(entry, "XMLAttribute", {
            "dataType": "character", "isMappable": "true", "isNode": "true",
            "key": attr_key, "name": attr_name, "required": "false", "useNamespace": "-1"
        })
        df_attr = SubElement(attr_elem, "DataFormat")
        SubElement(df_attr, "ProfileCharacterFormat")

    # Process child elements
    for child in element:
        process_xml_element(entry, child, key_counter)

def generate_boomi_xml_from_xml(xml_data):
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
        "name": "sourceProfile",
        "type": "profile.xml",
        "version": "1"
    })

    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description")
    bns_object = SubElement(component, "bns:object")
    profile = SubElement(bns_object, "XMLProfile", {"modelVersion": "2", "strict": "true"})

    profile_properties = SubElement(profile, "ProfileProperties")
    SubElement(profile_properties, "XMLGeneralInfo")

    xmlo_options = SubElement(profile_properties, "XMLOptions", {
        "encoding": "utf8", "implicitElementOrdering": "true", "parseRespectMaxOccurs": "true",
        "respectMinOccurs": "false", "respectMinOccursAlways": "false"
    })

    data_elements = SubElement(profile, "DataElements")

    root_element = ET.fromstring(xml_data)

    root_key_counter = [1]  # Start at 1 for root
    root = SubElement(data_elements, "XMLElement", {
        "dataType": "character", "isMappable": "true", "isNode": "true", "key": str(root_key_counter[0]), "name": root_element.tag,
        "maxOccurs": "1", "minOccurs": "1", "useNamespace": "-1"
    })

    # Add DataFormat to root element
    df = SubElement(root, "DataFormat")
    SubElement(df, "ProfileCharacterFormat")

    for child in root_element:
        process_xml_element(root, child, root_key_counter)

    namespaces = SubElement(profile, "Namespaces")
    xml_namespace = SubElement(namespaces, "XMLNamespace", {"key": "-1", "name": "Empty Namespace"})
    SubElement(xml_namespace, "Types")

    SubElement(profile, "tagLists")

    return parseString(tostring(component, encoding="utf-8")).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")


if __name__ == "__main__":
    xml_data = '''<Company>
        <Department name="Engineering">
            <Employee>
                <ID>101</ID>
                <Name>John Doe</Name>
                <Role>Software Developer</Role>
                <Salary>80000</Salary>
            </Employee>
        </Department>
    </Company>'''

    boomi_xml_output = generate_boomi_xml_from_xml(xml_data)

    with open("boomi_xml_output.xml", "w") as f:
        f.write(boomi_xml_output)

    print("✅ Boomi XML generated successfully.")
