#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config2.py - Overwrites expression NIDs inside prepare_data.py using config2.txt
"""

import json
import os
import re
import sys

CONFIG_FILENAME = "config2.txt"
TARGET_SCRIPT = "prepare_data.py"


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(base_dir, CONFIG_FILENAME)
    target_path = os.path.join(base_dir, TARGET_SCRIPT)

    # Validate files exist
    if not os.path.exists(cfg_path):
        print(f"[ERROR] Could not find configuration file: {cfg_path}")
        sys.exit(1)

    if not os.path.exists(target_path):
        print(f"[ERROR] Could not find target script: {target_path}")
        sys.exit(1)

    # Load NIDs from config2.txt
    with open(cfg_path, "r", encoding="utf-8") as f:
        try:
            nids_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed parsing JSON from {cfg_path}: {e}")
            sys.exit(1)

    koto_nid = str(nids_data.get("こと", ""))
    tokoro_nid = str(nids_data.get("ところ", ""))
    mono_nid = str(nids_data.get("もの", ""))
    ue_nid = str(nids_data.get("上", ""))
    sou_nid = str(nids_data.get("そう", ""))
    kagiri_nids = [str(x) for x in nids_data.get("限り", [])]

    if not all([koto_nid, tokoro_nid, mono_nid, ue_nid, sou_nid]) or len(kagiri_nids) != 3:
        print("[ERROR] config2.txt does not contain all required Note IDs.")
        sys.exit(1)

    # Read prepare_data.py
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex block replacement pattern
    block_pattern = (
        r'(#\s*If the row matches specific expression tags, also add the corresponding master NID\s*\n)'
        r'(\s*if\s+"ことexpressions"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.add\()"[0-9]+"(\)\s*\n)'
        r'(\s*elif\s+"ところexpressions"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.add\()"[0-9]+"(\)\s*\n)'
        r'(\s*elif\s+"ものexpressions"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.add\()"[0-9]+"(\)\s*\n)'
        r'(\s*elif\s+"上expressions"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.add\()"[0-9]+"(\)\s*\n)'
        r'(\s*elif\s+"そうexpressions"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.add\()"[0-9]+"(\)\s*\n)'
        r'(\s*elif\s+"限り"\s*in\s*tags_str:\s*\n\s*pattern_to_nids\[pat\]\.update\(\[\s*\n)'
        r'(?:\s*"[0-9]+",?\s*\n)+'
        r'(\s*\]\))'
    )

    new_kagiri_block = ',\n'.join([f'                    "{nid}"' for nid in kagiri_nids])

    def replacer(m):
        return (
            f'{m.group(1)}'
            f'{m.group(2)}"{koto_nid}"{m.group(3)}'
            f'{m.group(4)}"{tokoro_nid}"{m.group(5)}'
            f'{m.group(6)}"{mono_nid}"{m.group(7)}'
            f'{m.group(8)}"{ue_nid}"{m.group(9)}'
            f'{m.group(10)}"{sou_nid}"{m.group(11)}'
            f'{m.group(12)}'
            f'{new_kagiri_block}\n'
            f'{m.group(13)}'
        )

    new_content, count = re.subn(block_pattern, replacer, content)

    if count == 0:
        print("[ERROR] Could not find the matching code snippet inside prepare_data.py to replace.")
        sys.exit(1)

    # Write modified content back to prepare_data.py
    with open(target_path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)

    print(f"[SUCCESS] Updated {TARGET_SCRIPT} successfully with Note IDs from {CONFIG_FILENAME}!")


if __name__ == "__main__":
    main()