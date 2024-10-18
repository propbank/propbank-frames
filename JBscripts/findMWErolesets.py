import os
import xml.etree.ElementTree as ET

# Path to the repository containing the XML files
REPOSITORY_PATH = "C:/Users/littl/OneDrive/Documents/GitHub/PROPBANK-FRAMES/frames"

def extract_rolesets_with_alias_pos_m(repository_path):
    rolesets_with_m_aliases = []

    # Loop through all files in the repository
    for root_dir, _, files in os.walk(repository_path):
        for file_name in files:
            if file_name.endswith(".xml"):
                file_path = os.path.join(root_dir, file_name)
                print(f"Processing file: {file_path}")  # Debugging line
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    # Iterate through all rolesets in the XML file
                    rolesets = root.findall(".//roleset")
                    print(f"Found {len(rolesets)} rolesets in {file_name}")  # Debugging line
                    for roleset in rolesets:
                        roleset_id = roleset.get("id")
                        roleset_name = roleset.get("name")
                        aliases = []
                        has_m_alias = False

                        # Iterate through all aliases in the roleset
                        for alias in roleset.findall(".//alias"):
                            pos = alias.get("pos")
                            alias_name = alias.text
                            aliases.append((alias_name, pos))
                            if pos == "m":
                                has_m_alias = True

                        # If any alias has pos="m", add to the result
                        if has_m_alias:
                            rolesets_with_m_aliases.append({
                                "roleset_id": roleset_id,
                                "roleset_name": roleset_name,
                                "aliases": aliases
                            })
                except ET.ParseError as e:
                    print(f"Error parsing file {file_path}: {e}")  # Handle parsing errors

    return rolesets_with_m_aliases

# Extract rolesets and print them
rolesets = extract_rolesets_with_alias_pos_m(REPOSITORY_PATH)
for roleset in rolesets:
    print(f"Roleset ID: {roleset['roleset_id']}")
    print(f"Roleset Name: {roleset['roleset_name']}")
    print("Aliases:")
    for alias_name, pos in roleset['aliases']:
        print(f"  Alias: {alias_name}, POS: {pos}")
    print()