import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
import re


def extract_paths_from_json_profile(profile_xml_path):
    try:
        tree = ET.parse(profile_xml_path)
        root = tree.getroot()
        print(f"Successfully parsed XML file: {profile_xml_path}")
    except Exception as e:
        print(f"Error parsing XML file {profile_xml_path}: {e}")
        return {}

    mappings = {}
    for child in root:
        traverse_and_extract_mappings(child, "", "", mappings)

    print(f"Extracted {len(mappings)} field mappings from {profile_xml_path}")
    return mappings


def traverse_and_extract_mappings(element, parent_name_path, parent_key_path, mappings):
    is_mappable = element.get('isMappable') == 'true'
    element_name = element.get('name')
    element_key = element.get('key')

    current_name_path = parent_name_path
    current_key_path = parent_key_path

    if element_name:
        current_name_path = f"{current_name_path}/{element_name}" if current_name_path else element_name

    if element_key:
        key_part = f"*[@key='{element_key}']"
        current_key_path = f"{current_key_path}/{key_part}" if current_key_path else key_part

    if is_mappable and element_name and element_key:
        mappings[element_name] = {
            "name_path": current_name_path,
            "key_path": current_key_path
        }
        print(f"Found field: {element_name} -> {current_name_path} ({current_key_path})")

    for child in element:
        traverse_and_extract_mappings(child, current_name_path, current_key_path, mappings)


def normalize_field_name(field_name):
    field_name = re.sub(r'\[\*\]', '', field_name)
    if '.' in field_name:
        field_name = field_name.split('.')[-1]
    return field_name.strip()


def extract_final_key(path):
    matches = re.findall(r"\[@key='(\d+)'\]", path)
    return matches[-1] if matches else None


def generate_boomi_map(
    excel_path,
    source_component_xml_path,
    target_component_xml_path,
    source_col,
    target_col,
    from_profile_id,
    to_profile_id,
    folder_path="DPW Sub Account 1/ZZZ_Users/Mapping Automation",
    folder_id="Rjo3NjI1Mzcz",
    map_name="Generated Map from Excel"
):
    try:
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name="Field Mapping")
        df = df[[target_col, source_col]].dropna()
        print(f"Found {len(df)} mapping entries in Excel")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    print(f"Processing source component XML: {source_component_xml_path}")
    source_mappings = extract_paths_from_json_profile(source_component_xml_path)

    print(f"Processing target component XML: {target_component_xml_path}")
    target_mappings = extract_paths_from_json_profile(target_component_xml_path)

    if not source_mappings:
        print("Warning: No mappings found in source component XML")
    if not target_mappings:
        print("Warning: No mappings found in target component XML")

    component = Element("bns:Component", {
        "xmlns:bns": "http://api.platform.boomi.com/",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "branchId": "Qjo2OTgxOA",
        "branchName": "main",
        "createdDate": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": folder_path,
        "folderId": folder_id,
        "folderName": folder_path.split("/")[-1],
        "modifiedDate": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "name": map_name,
        "type": "transform.map",
        "version": "1"
    })

    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description").text = f"Auto-generated field mapping from {excel_path}"
    obj = SubElement(component, "bns:object")
    map_ = SubElement(obj, "Map", {
        "fromProfile": from_profile_id,
        "toProfile": to_profile_id
    })

    mappings_element = SubElement(map_, "Mappings")

    successful_mappings = 0
    for _, row in enumerate(df.itertuples(index=False), 1):
        target_field, source_field = row
        source_field_name = normalize_field_name(source_field)
        target_field_name = normalize_field_name(target_field)

        print(f"Processing mapping: {source_field} -> {target_field}")
        print(f"Normalized: {source_field_name} -> {target_field_name}")

        source_info = source_mappings.get(source_field_name)
        target_info = target_mappings.get(target_field_name)

        if not source_info:
            for field, info in source_mappings.items():
                if field.endswith(source_field_name):
                    source_info = info
                    break

        if not target_info:
            for field, info in target_mappings.items():
                if field.endswith(target_field_name):
                    target_info = info
                    break

        if not source_info:
            print(f"⚠️ Warning: No mapping found for source field: {source_field}")
            continue
        if not target_info:
            print(f"⚠️ Warning: No mapping found for target field: {target_field}")
            continue

        from_key = extract_final_key(source_info["key_path"])
        to_key = extract_final_key(target_info["key_path"])

        if not from_key or not to_key:
            print(f"⚠️ Skipping mapping due to missing key in path: {source_field} -> {target_field}")
            continue

        mapping_attrs = {
            "fromKey": from_key,
            "fromKeyPath": source_info["key_path"],
            "fromNamePath": source_info["name_path"],
            "fromType": "profile",
            "toKey": to_key,
            "toKeyPath": target_info["key_path"],
            "toNamePath": target_info["name_path"],
            "toType": "profile"
        }

        SubElement(mappings_element, "Mapping", mapping_attrs)
        successful_mappings += 1
        print(f"✓ Added mapping: {source_info['name_path']} -> {target_info['name_path']}")

    SubElement(map_, "Functions", {"optimizeExecutionOrder": "true"})
    SubElement(map_, "Defaults")
    SubElement(map_, "DocumentCacheJoins")

    xml_str = minidom.parseString(tostring(component)).toprettyxml(indent="  ")

    print(f"✅ Successfully created {successful_mappings} field mappings out of {len(df)} total.")
    return xml_str


if __name__ == "__main__":
    print("Starting Boomi mapping generation script...")

    xml_output = generate_boomi_map(
        excel_path="/Users/shubham.s/Desktop/mapping_automation_testing/AI_Field_Mapping.xlsx",
        source_component_xml_path="/Users/shubham.s/Desktop/mapping_automation_testing/sourceProfile.xml",
        target_component_xml_path="/Users/shubham.s/Desktop/mapping_automation_testing/destinationProfile.xml",
        source_col="Source Field (Dropdown)",
        target_col="Target Field",
        from_profile_id="4d8b52d3-64c5-46a3-a037-db4e54feea9f",
        to_profile_id="c6054768-73bb-4d11-bfe6-0b6a5602c5f0"
    )

    if xml_output:
        output_path = "/Users/shubham.s/Desktop/mapping_automation_testing/generated_boomi_map.xml"
        with open(output_path, "w") as f:
            f.write(xml_output)
        print(f"✅ Boomi XML generated successfully at {output_path}")
    else:
        print("❌ Failed to generate Boomi XML")