import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime

def generate_boomi_map_xml(excel_path, source_col, target_col,
                            from_profile_id, to_profile_id,
                            # component_id="generated-map-id",
                            folder_path="DPW Sub Account 1/ZZZ_Users/Mapping Automation",
                            folder_id="Rjo3NjI1Mzcz",
                            # user_email="you@example.com",
                            map_name="Generated Map from Excel"):

    df = pd.read_excel(excel_path, sheet_name="Field Mapping")
    df = df[[target_col, source_col]].dropna()

    # Root <Component>
    component = Element("bns:Component", {
        "xmlns:bns": "http://api.platform.boomi.com/",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "branchId": "Qjo2OTgxOA",
        "branchName": "main",
        #"componentId": component_id,
        #"createdBy": user_email,
        "createdDate": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "currentVersion": "true",
        "deleted": "false",
        "folderFullPath": folder_path,
        "folderId": folder_id,
        "folderName": folder_path.split("/")[-1],
        #"modifiedBy": user_email,
        "modifiedDate": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "name": map_name,
        "type": "transform.map",
        "version": "1"
    })

    SubElement(component, "bns:encryptedValues")
    SubElement(component, "bns:description").text = "Auto-generated field mapping from Excel"
    obj = SubElement(component, "bns:object")
    map_ = SubElement(obj, "Map", {
        "fromProfile": from_profile_id,
        "toProfile": to_profile_id
    })

    mappings = SubElement(map_, "Mappings")

    for i, row in enumerate(df.itertuples(index=False), 1):
        target, source = row
        mapping = SubElement(mappings, "Mapping", {
            "fromKey": str(i+2),
            "fromKeyPath": f"*[@key='1']/*[@key='2']/*[@key='{i+2}']",
            "fromNamePath": f"Root/Object/{source}",
            "fromType": "profile",
            "toKey": str(i+2),
            "toKeyPath": f"*[@key='1']/*[@key='2']/*[@key='{i+2}']",
            "toNamePath": f"Root/Object/{target}",
            "toType": "profile"
        })

    SubElement(map_, "Functions", {"optimizeExecutionOrder": "true"})
    SubElement(map_, "Defaults")
    SubElement(map_, "DocumentCacheJoins")

    # Pretty print
    xml_str = minidom.parseString(tostring(component)).toprettyxml(indent="  ")
    return xml_str

# Example usage:
xml_output = generate_boomi_map_xml(
    excel_path="/Users/shubham.s/Desktop/mapping_automation_testing/AI_Field_Mapping.xlsx",
    source_col="Source Field (Dropdown)",
    target_col="Target Field",
    from_profile_id="4d8b52d3-64c5-46a3-a037-db4e54feea9f",
    to_profile_id="c6054768-73bb-4d11-bfe6-0b6a5602c5f0",
)

# Save to file or print
with open("/Users/shubham.s/Desktop/mapping_automation_testing/generated_boomi_map.xml", "w") as f:
    f.write(xml_output)

print("Boomi Map XML generated and saved.")
