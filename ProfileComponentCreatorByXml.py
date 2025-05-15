import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# Constants
BOOMI_COMPONENT_BNS_URL = 'http://api.platform.boomi.com/'
BOOMI_COMPONENT_XSI_URL = 'http://www.w3.org/2001/XMLSchema-instance'
FOLDER_ID = 'Rjo3NjQ3ODEx'
FOLDER_PATH = 'DPW Sub Account 1/ZZZ_Users/Mapping Automation'
BRANCH_ID = 'Qjo2OTgxOA'
BRANCH_NAME = 'main'


def add_data_format(parent):
    df = SubElement(parent, "DataFormat")
    SubElement(df, "ProfileCharacterFormat")


def add_xml_attribute(parent, attr_name, key_counter):
    key_counter[0] += 1
    attr_elem = SubElement(parent, "XMLAttribute", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": str(key_counter[0]), "name": attr_name,
        "required": "false", "useNamespace": "-1"
    })
    add_data_format(attr_elem)


def process_xml_element(obj_elem, element, key_counter):
    key_counter[0] += 1
    entry = SubElement(obj_elem, "XMLElement", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": str(key_counter[0]), "name": element.tag,
        "maxOccurs": "1", "minOccurs": "0", "useNamespace": "-1"
    })
    add_data_format(entry)

    for attr_name in element.attrib:
        add_xml_attribute(entry, attr_name, key_counter)

    for child in element:
        process_xml_element(entry, child, key_counter)


def create_component_root(component_name):

    component = Element("bns:Component", {
        "xmlns:bns": BOOMI_COMPONENT_BNS_URL,
        "xmlns:xsi": BOOMI_COMPONENT_XSI_URL,
        "branchId": BRANCH_ID,
        "branchName": BRANCH_NAME,
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": FOLDER_PATH,
        "folderId": FOLDER_ID,
        "folderName": FOLDER_PATH.split("/")[-1],
        "name": component_name,
        "type": "profile.xml", #need change
        "version": "1"
    })

    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description")
    return component


def build_xml_profile_structure(component, root_element, key_counter):

    bns_object = SubElement(component, "bns:object")
    profile = SubElement(bns_object, "XMLProfile", {
        "modelVersion": "2", "strict": "true"
    })

    profile_props = SubElement(profile, "ProfileProperties")
    SubElement(profile_props, "XMLGeneralInfo")
    SubElement(profile_props, "XMLOptions", {
        "encoding": "utf8", "implicitElementOrdering": "true",
        "parseRespectMaxOccurs": "true", "respectMinOccurs": "false",
        "respectMinOccursAlways": "false"
    })

    data_elements = SubElement(profile, "DataElements")

    root = SubElement(data_elements, "XMLElement", {
        "dataType": "character", "isMappable": "true", "isNode": "true",
        "key": str(key_counter[0]), "name": root_element.tag,
        "maxOccurs": "1", "minOccurs": "1", "useNamespace": "-1"
    })
    add_data_format(root)

    for child in root_element:
        process_xml_element(root, child, key_counter)

    namespaces = SubElement(profile, "Namespaces")
    xml_namespace = SubElement(namespaces, "XMLNamespace", {
        "key": "-1", "name": "Empty Namespace"
    })
    SubElement(xml_namespace, "Types")

    SubElement(profile, "tagLists")


def generate_boomi_xml_from_xml(xml_data, component_name="sourceProfile"):
    try:
        root_element = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"❌ Failed to parse input XML: {e}")
        raise

    component = create_component_root(component_name)
    key_counter = [1]
    build_xml_profile_structure(component, root_element, key_counter)

    return parseString(tostring(component, encoding="utf-8")).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")


def main():
    print("🚀 Starting Boomi XML profile generation from input XML")

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

    try:
        output = generate_boomi_xml_from_xml(xml_data)
        with open("boomi_xml_output.xml", "w") as f:
            f.write(output)
        print("✅ Boomi XML profile written to boomi_xml_output.xml")

    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
