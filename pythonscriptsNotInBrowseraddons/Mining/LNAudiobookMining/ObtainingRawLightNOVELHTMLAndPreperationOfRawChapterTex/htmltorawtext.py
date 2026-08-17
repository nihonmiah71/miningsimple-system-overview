import os
import re
import tkinter as tk
from tkinter import filedialog

# Initialize and hide the root tkinter window
root = tk.Tk()
root.withdraw()

# 1. Select input file via File Explorer
print("Please select the input file in the Explorer window...")
input_file = filedialog.askopenfilename(
    title="Select Input File",
    filetypes=[("Text Files", "*.txt"), ("HTML/XML Files", "*.html;*.xml"), ("All Files", "*.*")]
)

if not input_file:
    print("No input file selected. Program terminated.")
else:
    # 2. Select output file destination via File Explorer
    print("Please choose where to save the output file...")
    
    # Pre-populate with a suggested filename and directory
    base_name, ext = os.path.splitext(input_file)
    default_filename = f"{os.path.basename(base_name)}_cleaned.txt"
    initial_dir = os.path.dirname(input_file)

    output_file = filedialog.asksaveasfilename(
        title="Save Output File As",
        initialdir=initial_dir,
        initialfile=default_filename,
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("HTML/XML Files", "*.html;*.xml"), ("All Files", "*.*")]
    )

    if not output_file:
        print("No output file destination selected. Program terminated.")
    else:
        pattern = r'<p(?: class="middle-block")?>(.+?)</p>'

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()

            matches = re.findall(pattern, text, re.DOTALL)

            with open(output_file, 'w', encoding='utf-8') as f_out:
                for match in matches:
                    # 1. Completely remove furigana (<rt>...</rt>) including content
                    match = re.sub(r'<rt>.*?</rt>', '', match, flags=re.DOTALL)
                    
                    # (Optional) Remove <rp> tags if the source file contains any
                    match = re.sub(r'<rp>.*?</rp>', '', match, flags=re.DOTALL)

                    # 2. Only now remove the remaining HTML tags (like <ruby>, </ruby>)
                    clean_text = re.sub(r'<.*?>', '', match).strip()
                    
                    if clean_text:
                        f_out.write(clean_text + '\n')

            print(f"Success! {len(matches)} matches saved to: {output_file}")

        except FileNotFoundError:
            print("Error: File not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")