import os
import sys
from tkinter import Tk, messagebox
from tkinter.filedialog import askopenfilename
from pydub import AudioSegment


def convert_audio():
    # Hide the main Tkinter window
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # Bring file dialog to the front

    # Open file explorer dialog with audio filters
    file_path = askopenfilename(
        title="Select an MP3 or M4A File",
        filetypes=[
            ("Audio Files", "*.mp3 *.m4a"),
            ("MP3 Files", "*.mp3"),
            ("M4A Files", "*.m4a"),
            ("All Files", "*.*"),
        ],
    )

    # Exit if user cancels file selection
    if not file_path:
        print("No file selected. Exiting...")
        return

    # Extract directory, base name, and extension
    file_dir, file_name = os.path.split(file_path)
    base_name, ext = os.path.splitext(file_name)
    ext = ext.lower()

    # Determine target format
    if ext == ".mp3":
        target_format = "m4a"
    elif ext == ".m4a":
        target_format = "mp3"
    else:
        messagebox.showerror(
            "Unsupported Format",
            f"Please select an .mp3 or .m4a file.\nSelected: {ext}",
        )
        return

    output_file = os.path.join(file_dir, f"{base_name}.{target_format}")

    # Check if the output file already exists to avoid accidental overwrites
    if os.path.exists(output_file):
        overwrite = messagebox.askyesno(
            "File Exists",
            f"'{base_name}.{target_format}' already exists in this folder.\nDo you want to overwrite it?",
        )
        if not overwrite:
            print("Conversion canceled by user.")
            return

    # Perform the conversion
    print(f"Converting '{file_name}' to '{target_format.upper()}'...")
    try:
        # Load source file
        audio = AudioSegment.from_file(file_path, format=ext.replace(".", ""))

        # Export to target format
        # Note: ipod/aac codec is standard for m4a files in ffmpeg
        export_format = "ipod" if target_format == "m4a" else target_format
        audio.export(output_file, format=export_format)

        messagebox.showinfo(
            "Success",
            f"Conversion successful!\nSaved to:\n{output_file}",
        )
        print("Done!")

    except Exception as e:
        messagebox.showerror(
            "Conversion Error",
            f"An error occurred during conversion:\n{str(e)}\n\nMake sure FFmpeg is installed and added to PATH.",
        )


if __name__ == "__main__":
    convert_audio()