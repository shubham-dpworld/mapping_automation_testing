import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
import re


def extract_paths_from_json_profile(profile_xml_path):
    """
    Extract field name paths and key paths from a Boomi JSON profile XML.
    Returns a dictionary mapping field names to their corresponding paths.
    """
    try:
        tree = ET.parse(profile_xml_path)
        root = tree.getroot()
        print(f"Successfully parsed XML file: {profile_xml_path}")
    except Exception as e:
        print(f"Error parsing XML file {profile_xml_path}: {e}")
        return {}
    
    # Find all mappable elements in the JSON profile
    mappings = {}
    
    # Define XML namespaces
    ns = {'bns': 'http://api.platform.boomi.com/'}
    
    # Use recursive function to build paths during traversal
    traverse_and_extract_mappings(root, "", "", mappings)
    
    print(f"Extracted {len(mappings)} field mappings from {profile_xml_path}")
    return mappings


def traverse_and_extract_mappings(element, parent_name_path, parent_key_path, mappings):
    """
    Recursively traverse the XML tree to extract mappable elements and their paths.
    """
    # Check if the current element is mappable and has a name attribute
    is_mappable = element.get('isMappable') == 'true'
    element_name = element.get('name')
    element_key = element.get('key')
    
    # Build current path components
    current_name_path = parent_name_path
    current_key_path = parent_key_path
    
    if element_name:
        # Build name path with / separator as shown in the sample
        if current_name_path:
            current_name_path = f"{current_name_path}/{element_name}"
        else:
            current_name_path = element_name
    
    if element_key:
        # Build key path in the format *[@key='X']/*[@key='Y'] as shown in the sample
        key_part = f"*[@key='{element_key}']"
        if current_key_path:
            current_key_path = f"{current_key_path}/{key_part}"
        else:
            current_key_path = key_part
    
    # If the element is mappable and has both name and key, add it to mappings
    if is_mappable and element_name and element_key:
        field_name = element_name
        mappings[field_name] = {
            "name_path": current_name_path,
            "key_path": current_key_path
        }
        print(f"Found field: {field_name} -> {current_name_path} ({current_key_path})")
    
    # Recursively process child elements
    for child in element:
        traverse_and_extract_mappings(child, current_name_path, current_key_path, mappings)


def normalize_field_name(field_name):
    """Normalize a field name by removing array notation and extracting just the field name."""
    # Remove array notation [*]
    field_name = re.sub(r'\[\*\]', '', field_name)
    
    # Get the last part of the path if it contains dots
    if '.' in field_name:
        field_name = field_name.split('.')[-1]
    
    return field_name.strip()


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
    """
    Generate a Boomi map component XML based on Excel mappings and component XMLs.
    Uses existing mappings from component XMLs to determine the correct paths.
    """
    # Read the Excel file
    try:
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name="Field Mapping")
        df = df[[target_col, source_col]].dropna()
        print(f"Found {len(df)} mapping entries in Excel")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None
    
    # Extract path information from source and target component XMLs
    print(f"Processing source component XML: {source_component_xml_path}")
    source_mappings = extract_paths_from_json_profile(source_component_xml_path)
    
    print(f"Processing target component XML: {target_component_xml_path}")
    target_mappings = extract_paths_from_json_profile(target_component_xml_path)
    
    if not source_mappings:
        print("Warning: No mappings found in source component XML")
    if not target_mappings:
        print("Warning: No mappings found in target component XML")
    
    # Create the base XML structure
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
    
    # Add component elements
    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description").text = f"Auto-generated field mapping from {excel_path}"
    obj = SubElement(component, "bns:object")
    map_ = SubElement(obj, "Map", {
        "fromProfile": from_profile_id,
        "toProfile": to_profile_id
    })
    
    mappings_element = SubElement(map_, "Mappings")
    
    # Track used keys to ensure uniqueness
    used_keys = set()
    next_key = 3  # Starting key number, based on the sample
    
    # Process each mapping row from Excel
    successful_mappings = 0
    for _, row in enumerate(df.itertuples(index=False), 1):
        target_field, source_field = row
        
        # Normalize field names to extract just the base field name
        source_field_name = normalize_field_name(source_field)
        target_field_name = normalize_field_name(target_field)
        
        print(f"Processing mapping: {source_field} -> {target_field}")
        print(f"Normalized field names: {source_field_name} -> {target_field_name}")
        
        # Look up paths in the extracted mappings
        source_info = None
        target_info = None
        
        # Try to find exact field name match
        if source_field_name in source_mappings:
            source_info = source_mappings[source_field_name]
        
        if target_field_name in target_mappings:
            target_info = target_mappings[target_field_name]
        
        # If not found, try to find a field with the same base name
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
        
        # Skip if we couldn't find mapping information
        if not source_info:
            print(f"⚠️ Warning: No mapping found for source field: {source_field}")
            continue
        
        if not target_info:
            print(f"⚠️ Warning: No mapping found for target field: {target_field}")
            continue
        
        # Find an unused key
        while str(next_key) in used_keys:
            next_key += 1
        
        key = str(next_key)
        used_keys.add(key)
        next_key += 1
        
        # Add the mapping to XML
        mapping_attrs = {
            "fromKey": key,
            "fromKeyPath": source_info["key_path"],
            "fromNamePath": source_info["name_path"],
            "fromType": "profile",
            "toKey": key,
            "toKeyPath": target_info["key_path"],
            "toNamePath": target_info["name_path"],
            "toType": "profile"
        }
        
        SubElement(mappings_element, "Mapping", mapping_attrs)
        successful_mappings += 1
        print(f"✓ Added mapping: {source_info['name_path']} -> {target_info['name_path']}")
    
    # Complete the XML structure
    SubElement(map_, "Functions", {"optimizeExecutionOrder": "true"})
    SubElement(map_, "Defaults")
    SubElement(map_, "DocumentCacheJoins")
    
    # Convert to pretty XML string
    xml_str = minidom.parseString(tostring(component)).toprettyxml(indent="  ")
    
    print(f"✅ Successfully created {successful_mappings} field mappings out of {len(df)} total.")
    return xml_str


if __name__ == "__main__":
    # Add more verbose output to help diagnose issues
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