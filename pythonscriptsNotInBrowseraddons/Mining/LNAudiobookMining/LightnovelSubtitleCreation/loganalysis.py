import os
import re
import tkinter as tk
from tkinter import filedialog

def analyze_mapping_logs(start_directory):
    # Regular expression to extract the method/category from log blocks
    method_pattern = re.compile(r'Method:\s*(FUZZY\s*\(OK\)|LOOP_RECOVERY_FALLBACK|DELETION_STRETCH)')

    print(f"Starting analysis in directory: {os.path.abspath(start_directory)}\n")
    print("=" * 80)

    file_count = 0

    # Recursive traversal of all folders and subfolders
    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if file.endswith('mapping_log.txt'):
                file_count += 1
                file_path = os.path.join(root, file)
                
                # Reset counters for categories
                counts = {
                    'FUZZY (OK)': 0,
                    'LOOP_RECOVERY_FALLBACK': 0,
                    'DELETION_STRETCH': 0
                }
                total_blocks = 0

                # Read and analyze file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            match = method_pattern.search(line)
                            if match:
                                category = match.group(1).strip()
                                # Normalize potential spacing within "FUZZY (OK)"
                                if "FUZZY" in category:
                                    category = 'FUZZY (OK)'
                                counts[category] += 1
                                total_blocks += 1
                except Exception as e:
                    print(f"Error reading file {file}: {e}")
                    continue

                # Relative path output from main folder for better overview
                relative_path = os.path.relpath(file_path, start_directory)
                print(f"\nFile [{file_count}]: {relative_path}")
                print(f"Total blocks found: {total_blocks}")
                print("-" * 40)

                if total_blocks > 0:
                    fuzzy_pct = (counts['FUZZY (OK)'] / total_blocks) * 100
                    loop_pct = (counts['LOOP_RECOVERY_FALLBACK'] / total_blocks) * 100
                    deletion_pct = (counts['DELETION_STRETCH'] / total_blocks) * 100

                    print(f"  FUZZY (OK):              {fuzzy_pct:6.2f}%  ({counts['FUZZY (OK)']} blocks)")
                    print(f"  LOOP_RECOVERY_FALLBACK:  {loop_pct:6.2f}%  ({counts['LOOP_RECOVERY_FALLBACK']} blocks)")
                    print(f"  DELETION_STRETCH:        {deletion_pct:6.2f}%  ({counts['DELETION_STRETCH']} blocks)")

                    # Warning if FUZZY (OK) is below 80%
                    if fuzzy_pct < 80.0:
                        print("\n  [!] WARNING: PLEASE CHECK (FUZZY (OK) is below 80%)")
                else:
                    print("  No matching blocks or categories found in this file.")
                
                print("=" * 80)
                
    if file_count == 0:
        print(f"No files ending with 'mapping_log.txt' found in {start_directory}.")
    else:
        print(f"\nAnalysis completed. Total of {file_count} file(s) processed.")

if __name__ == "__main__":
    # Initialize and hide the root tkinter window
    root = tk.Tk()
    root.withdraw()

    print("Please select the target directory in the Explorer window...")
    target_directory = filedialog.askdirectory(
        title="Select Directory to Analyze"
    )

    if not target_directory:
        print("No directory selected. Program terminated.")
    elif os.path.exists(target_directory):
        analyze_mapping_logs(target_directory)
    else:
        print(f"\n[Error] The directory '{target_directory}' does not exist. Please check the path.")