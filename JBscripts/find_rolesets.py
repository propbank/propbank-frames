import os
import xml.etree.ElementTree as ET

# Path to the repository containing the XML files
REPOSITORY_PATH = "C:/Users/littl/OneDrive/Documents/GitHub/PROPBANK-FRAMES/frames"

# List of roleset names to search for
TARGET_ROLESETS = [
    "full-steam-ahead.04", "bark_up_wrong_tree.02", "bite_dust.02", "bite_bullet.03", "shed_blood.05", "break_heart.31", "clean_clock.05", "come_out.10", "cut_to_chase.16", "cut_corners.17", "cut_and_dry.18", "cut_it.19", "cut_cheese.20", "cut_slack.21", "cut_fine_figure.22", "cut_rug.23", "cut_and_run.24", "fish_or_cut_bait.25", "cut_off_nose_to_spite_face.27", "drag_feet.03", "get_even.16", "keep_eye_out.02", "open_eyes.03", "eye_on_ball.04", "have_eye_on.05", "lose_face.04", "save_face.05", "follow_suit.06", "come_to_grips.03", "in_ones_hands.07", "out_of_hands.08", "out_of_hands.09", "out_of_hand.10", "out_of_hand.11", "blood_on_hands.12", "play_into_ones_hands.13", "at_hand.14", "on_hand.15", "give_hand.16", "have_hand_in.17", "take_to_heart.02", "hit_nail_on_head.08", "jump_on_bandwagon.09", "jump_gun.10", "jump_shark.11", "kick_bucket.05", "shed_light.10", "out_of_line.05", "draw_line.07", "toe_line.08", "read_between_lines.09", "cut_loose.06", "path.01", "pinch.04", "line_pocket.02", "out_of_pocket.04", "out_of_pocket.05", "in_ones_pocket.06", "point_finger.06", "hair-raising.05", "route.03", "cut_and_run.27", "short.02", "steer_clear.02", "step_aside.05", "step_back.07", "take_stock.03", "take_with_grain_of_salt.36", "come_to_terms.03", "touch_base.08", "up_creek-13", "wear_heart_on_sleave.07", "come_to_blows.15", "break_ground.28", "have_clue.01", "edge_out.02", "in_ones_hands.04", "change_hands.06", "right.08"
]

def extract_target_rolesets(repository_path, target_rolesets):
    rolesets_found = []

    # Loop through all files in the repository
    for root_dir, _, files in os.walk(repository_path):
        for file_name in files:
            if file_name.endswith(".xml"):
                file_path = os.path.join(root_dir, file_name)
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    # Iterate through all rolesets in the XML file
                    rolesets = root.findall(".//roleset")
                    for roleset in rolesets:
                        roleset_id = roleset.get("id")
                        if roleset_id in target_rolesets:
                            roleset_str = ET.tostring(roleset, encoding='unicode')
                            rolesets_found.append(roleset_str)
                except ET.ParseError as e:
                    print(f"Error parsing file {file_path}: {e}")  # Handle parsing errors

    return rolesets_found

# Extract rolesets and write them to an output file
output_file_path = "C:/Users/littl/OneDrive/Documents/GitHub/PROPBANK-FRAMES/JBscripts/rolesets_output.txt"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    rolesets = extract_target_rolesets(REPOSITORY_PATH, TARGET_ROLESETS)
    for roleset in rolesets:
        output_file.write(roleset)
        output_file.write("\n----------------------------------------\n")