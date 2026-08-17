import os
import re
import csv
import random
import shutil
import string
import subprocess
import tkinter as tk
from tkinter import filedialog
import pysrt
from pydub import AudioSegment
from datetime import datetime
from difflib import SequenceMatcher

# Try loading OpenCV for frame-accurate screenshots
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# ---- CONFIGURATION ----
WORD_COLUMN_NAME = "Word"
SENTENCE_COLUMN_NAME = "SentencePlain"
DEFINITION_COLUMN_NAME = "Correct English Definition"
AUDIO_FRONT_COLUMN = "SoundFront"
AUDIO_BACK_COLUMN = "SoundBack"
IMAGE_COLUMN_NAME = "Picture"

MATCH_THRESHOLD = 0.45
CONFIG_FILE_NAME = "paths.txt"

# Positions for the 3-Block ASS layout
Y_PREV = 180
Y_ACTIVE = 440
Y_NEXT = 700
Y_TIMER = 420
Y_DEFINITION = 340
# -----------------------

def get_config_file_path():
    """Returns the absolute path to paths.txt in the script directory"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base_dir = os.getcwd()
    return os.path.join(base_dir, CONFIG_FILE_NAME)

def load_paths_config():
    """Loads and validates paths from paths.txt"""
    config_path = get_config_file_path()
    if not os.path.exists(config_path):
        return None

    paths = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    paths[key.strip().upper()] = val.strip()

        media_dir = paths.get("MEDIA_OUTPUT_DIR") or paths.get("AUDIO_OUTPUT_DIR", "")
        backup_dir = paths.get("BACKUP_DIR", "")

        if not media_dir and not backup_dir:
            return None

        return {
            "MEDIA_OUTPUT_DIR": media_dir if media_dir else None,
            "BACKUP_DIR": backup_dir if backup_dir else None
        }
    except Exception as e:
        print(f"Warning: Failed to read {CONFIG_FILE_NAME}: {e}")
        return None

def save_paths_config(media_dir, backup_dir):
    """Saves configured paths to paths.txt"""
    config_path = get_config_file_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"MEDIA_OUTPUT_DIR={media_dir or ''}\n")
            f.write(f"BACKUP_DIR={backup_dir or ''}\n")
        print(f"\n[CONFIG] Paths successfully saved to {config_path}")
        return True
    except Exception as e:
        print(f"\n[CONFIG ERROR] Failed to save {config_path}: {e}")
        return False

def configure_paths_interactive():
    """Prompts the user via Tkinter to set and save hardcoded paths"""
    print("\n" + "=" * 60)
    print(" CONFIGURE HARDCODED PATHS (TKINTER)")
    print("=" * 60)
    
    print("Please select the Media Output Directory in the window...")
    media_dir = filedialog.askdirectory(title="Select Default Media Output Directory")
    if media_dir:
        print(f"Media Output Directory set to: {media_dir}")
    else:
        print("Media Output Directory skipped.")

    print("\nPlease select the Subtitle Backup Directory in the window...")
    backup_dir = filedialog.askdirectory(title="Select Default Subtitle Backup Directory")
    if backup_dir:
        print(f"Subtitle Backup Directory set to: {backup_dir}")
    else:
        print("Subtitle Backup Directory skipped.")

    if media_dir or backup_dir:
        save_paths_config(media_dir, backup_dir)
        return {
            "MEDIA_OUTPUT_DIR": media_dir if media_dir else None,
            "BACKUP_DIR": backup_dir if backup_dir else None
        }
    else:
        print("\nNo paths were configured.")
        return None

def generate_random_name(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def clean_text_temporary(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'（.*?）', '', text)
    text = re.sub(r'「.*?」', '', text)
    text = re.sub(r'^[A-Za-z0-9_À-ÿ\s]+:\s*', '', text)
    text = re.sub(r'[\s\t\n\r\.,\?\!。、？！…♪～\-—「」\(\)（）"’]+', '', text)
    return text.strip().lower()

def generiere_lueckenlose_teilstrings(text):
    laenge = len(text)
    teilstrings = []
    for fenster_groesse in range(laenge, 1, -1):
        for start_pos in range(laenge - fenster_groesse + 1):
            unterstring = text[start_pos : start_pos + fenster_groesse]
            if unterstring not in teilstrings:
                teilstrings.append(unterstring)
    return teilstrings

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '░' * (length - filled_length)
    sys_write = f'\r{prefix} [{bar}] {percent}% {suffix}'
    print(sys_write, end='\r')
    if iteration == total:
        print()

def clean_text_subs(text):
    if not text:
        return ""
    text = re.sub(r"\{[^}]+\}", "", text)
    text = text.replace(r"\N", "").replace(r"\n", "")
    text = re.sub(r"[\s●③②①④⑤⑥⑦⑧⑨⓪①-⑨\.。,、 („)“、「」『』？?！!！？\-=_+*⑨<>█░…·•\"\'’()（）]", "", text)
    return text

def get_clean_map(original_text):
    clean_chars = []
    mapping = []
    i = 0
    n = len(original_text)
    while i < n:
        if original_text[i] == '{':
            end = original_text.find('}', i)
            if end != -1:
                i = end + 1
                continue
        if i + 1 < n and original_text[i] == '\\' and original_text[i+1].lower() == 'n':
            i += 2
            continue
        
        clean_chars.append(original_text[i])
        mapping.append(i)
        i += 1
        
    return "".join(clean_chars), mapping

def window_search_match(tsv_text, ass_text, min_ratio=0.55):
    if not tsv_text or not ass_text:
        return False
    if len(ass_text) <= len(tsv_text):
        return SequenceMatcher(None, tsv_text, ass_text).ratio() >= MATCH_THRESHOLD

    window_size = len(tsv_text)
    best_ratio = 0.0
    for i in range(len(ass_text) - window_size + 1):
        sub_str = ass_text[i:i+window_size]
        ratio = SequenceMatcher(None, tsv_text, sub_str).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            if best_ratio >= 0.80:
                return True
    return best_ratio >= min_ratio

def generate_bright_ass_color():
    b = random.randint(120, 255)
    g = random.randint(120, 255)
    r = random.randint(120, 255)
    return f"{b:02X}{g:02X}{r:02X}"

# --- SEARCH LOGIC (SLIDING SUBSTRING MATCH) ---
def find_timestamps_and_text_gleitend(srt_subs, target_sentence, start_index=0, delay_ms=0):
    cleaned_target = clean_text_temporary(target_sentence)
    if not cleaned_target:
        return None, None, start_index

    such_begriffe = generiere_lueckenlose_teilstrings(cleaned_target)
    total_subs = len(srt_subs)

    for begriff in such_begriffe:
        for i in range(start_index, total_subs):
            sub_text_cleaned = clean_text_temporary(srt_subs[i].text)
            
            if begriff in sub_text_cleaned:
                start_block_idx = i
                end_block_idx = i
                current_combined_cleaned = sub_text_cleaned
                
                # 1. BACKWARD SCAN
                for prev_j in range(i - 1, max(-1, start_index - 1, i - 11), -1):
                    prev_cleaned = clean_text_temporary(srt_subs[prev_j].text)
                    if not prev_cleaned:
                        continue
                    potential_match = prev_cleaned + current_combined_cleaned
                    if prev_cleaned in cleaned_target and potential_match in cleaned_target:
                        start_block_idx = prev_j
                        current_combined_cleaned = potential_match
                    else:
                        break
                
                # 2. FORWARD SCAN
                for next_j in range(i + 1, min(total_subs, i + 11)):
                    next_cleaned = clean_text_temporary(srt_subs[next_j].text)
                    if not next_cleaned:
                        continue
                    potential_match = current_combined_cleaned + next_cleaned
                    if next_cleaned in cleaned_target and (potential_match in cleaned_target or cleaned_target.endswith(next_cleaned)):
                        end_block_idx = next_j
                        current_combined_cleaned = potential_match
                    else:
                        break
                
                start_time = srt_subs[start_block_idx].start
                end_time = srt_subs[end_block_idx].end
                
                start_ms = (start_time.hours * 3600 + start_time.minutes * 60 + start_time.seconds) * 1000 + start_time.milliseconds
                end_ms = (end_time.hours * 3600 + end_time.minutes * 60 + end_time.seconds) * 1000 + end_time.milliseconds
                
                start_ms += delay_ms
                end_ms += delay_ms
                
                if start_ms < 0: start_ms = 0
                if end_ms < 0: end_ms = 0
                
                return start_ms, end_ms, end_block_idx + 1

    if start_index > 0:
        return find_timestamps_and_text_gleitend(srt_subs, target_sentence, start_index=0, delay_ms=delay_ms)
                
    return None, None, start_index

def get_process_type():
    print("=" * 60)
    print(" CHOOSE PROCESSING TYPE")
    print("=" * 60)
    print(" [1] Batch Process (Scan directory for matching triples)")
    print(" [2] Single File Process (Manual file selection)")
    print(" [3] Configure Default Paths (Media & Backup directories)")
    print("=" * 60)
    while True:
        choice = input("Please select an option (1-3): ").strip()
        if choice in ["1", "2", "3"]:
            return choice
        print("Invalid input. Please enter 1, 2, or 3.")

def get_execution_mode():
    print("=" * 60)
    print(" CHOOSE EXECUTION MODE")
    print("=" * 60)
    print(" [1] Full Process (Audio/Image Extraction & Subtitle Formatting)")
    print(" [2] Media Extraction Only (Cut Audio & Screenshots)")
    print(" [3] Subtitle Formatting Only (Format 3-Block ASS)")
    print("=" * 60)
    
    while True:
        choice = input("Please select a mode (1-3): ").strip()
        if choice in ["1", "2", "3"]:
            return choice
        print("Invalid input. Please enter a number from 1 to 3.")

def get_audio_quality_settings():
    print("=" * 60)
    print(" CHOOSE AUDIO QUALITY")
    print("=" * 60)
    print(" [1] Best Quality (320k MP3)")
    print(" [2] High Quality (192k MP3)")
    print(" [3] Good Quality (128k MP3)")
    print(" [4] Low Quality (64k Mono MP3)")
    print("=" * 60)
    
    while True:
        choice = input("Select quality (1-4): ").strip()
        if choice in ["1", "2", "3", "4"]:
            break

    if choice == "1":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "320k", "format": "mp3"}
    elif choice == "2":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "192k", "format": "mp3"}
    elif choice == "3":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "128k", "format": "mp3"}
    elif choice == "4":
        return {"channels": 1, "frame_rate": 22050, "bitrate": "64k", "format": "mp3"}

def convert_time_to_ass(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int(round((seconds % 1) * 100))
    if centiseconds == 100:
        centiseconds = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def wrap_text_ass(text, max_chars=40):
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        current = []
        count = 0
        for char in line:
            current.append(char)
            count += 1
            if count >= max_chars:
                lines.append("".join(current))
                current = []
                count = 0
        if current:
            lines.append("".join(current))
    return r"\N".join(lines)

def convert_srt_to_ass(srt_path, output_ass_path):
    print(f"Creating 3-Block ASS Subtitle: {os.path.basename(srt_path)}...")
    subs = pysrt.open(srt_path)
    
    raw_blocks = []
    for sub in subs:
        start_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds) * 1000 + sub.start.milliseconds
        end_ms = (sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds) * 1000 + sub.end.milliseconds
        raw_blocks.append({
            "start": start_ms,
            "end": end_ms,
            "text": sub.text.replace('\n', ' ')
        })

    blocks = []
    for i in range(0, len(raw_blocks), 3):
        group = raw_blocks[i:i+3]
        combined_text = " ".join([b["text"] for b in group])
        combined_start = group[0]["start"]
        combined_end = group[-1]["end"]
        blocks.append({
            "start": combined_start,
            "end": combined_end,
            "text": combined_text
        })

    ass_content = [
        "[Script Info]",
        "Title: 3-Block Left Aligned",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Text,MS Gothic,38,&H00000000,&H000000FF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,8,0,7,20,20,20,1",
        f"Style: Timer,MS Gothic,42,&H00000000,&H000000FF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,8,0,7,20,20,20,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    pos_tag = r"{\pos"

    for i in range(len(blocks)):
        current = blocks[i]
        start_ass = convert_time_to_ass(current["start"] / 1000)
        end_ass = convert_time_to_ass(current["end"] / 1000)
        duration = int((current["end"] - current["start"]) / 1000)

        if i - 1 >= 0:
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{pos_tag}(120,{Y_PREV})}}{wrap_text_ass(blocks[i-1]["text"])}')
        
        current_text = wrap_text_ass(current["text"])
        ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{pos_tag}(120,{Y_ACTIVE})}}●{current_text}')
        
        if i + 1 < len(blocks):
            ass_content.append(f'Dialogue: 0,{start_ass},{end_ass},Text,,0,0,0,,{pos_tag}(120,{Y_NEXT})}}{wrap_text_ass(blocks[i+1]["text"])}')

        for sec in range(duration):
            t_start = convert_time_to_ass((current["start"] / 1000) + sec)
            t_end = convert_time_to_ass((current["start"] / 1000) + sec + 1)
            remaining = duration - sec
            ass_content.append(f'Dialogue: 5,{t_start},{t_end},Timer,,0,0,0,,{{\\pos(1750,{Y_TIMER})}}{remaining}')

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_content))

def extract_video_frame(video_path, timestamp_ms, output_path):
    if not OPENCV_AVAILABLE:
        return False
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        success, frame = cap.read()
        if success:
            cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            cap.release()
            return True
        cap.release()
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
    return False

def process_single_triple(table_path, sub_path, media_path, mode, quality, want_screenshots, output_dir, backup_dir):
    """Core logic to process a single triple of (TSV, SRT, Media)"""
    run_media = (mode in ["1", "2"])
    run_subs = (mode in ["1", "3"])

    base_name = os.path.splitext(os.path.basename(table_path))[0]
    orig_dir = os.path.dirname(table_path)

    subs_pysrt = pysrt.open(sub_path) if sub_path and os.path.exists(sub_path) else None

    # Read table file
    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        delimiter = "\t" if "\t" in sample else (";" if ";" in sample else ",")

    table_rows = []
    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            table_rows.append({k.strip(): v.strip() if v else "" for k, v in row.items() if k})

    # --- PART 1: AUDIO & SCREENSHOT EXTRACTION ---
    if run_media and media_path and subs_pysrt:
        if AUDIO_FRONT_COLUMN not in fieldnames: fieldnames.append(AUDIO_FRONT_COLUMN)
        if AUDIO_BACK_COLUMN not in fieldnames: fieldnames.append(AUDIO_BACK_COLUMN)
        if want_screenshots and IMAGE_COLUMN_NAME not in fieldnames: fieldnames.append(IMAGE_COLUMN_NAME)

        print(f"\n[PART 1] Starting media processing for {base_name}...")
        full_audio = AudioSegment.from_file(media_path)
        audio_duration_ms = len(full_audio)

        extracted_map = {}
        last_srt_index = 0

        for row in table_rows:
            raw_sentence = row.get(SENTENCE_COLUMN_NAME, "")
            cleaned_sentence = clean_text_temporary(raw_sentence)

            if not cleaned_sentence: continue

            if cleaned_sentence in extracted_map:
                r_name = extracted_map[cleaned_sentence]
                sound_tag = f"[sound:{r_name}.mp3]"
                row[AUDIO_FRONT_COLUMN] = sound_tag
                row[AUDIO_BACK_COLUMN] = sound_tag
                if want_screenshots: row[IMAGE_COLUMN_NAME] = f'<img src="{r_name}.jpg">'
                continue

            # Sliding substring search matching
            start_ms, end_ms, next_index = find_timestamps_and_text_gleitend(subs_pysrt, raw_sentence, last_srt_index)

            if start_ms is not None:
                last_srt_index = next_index
                r_name = generate_random_name()
                extracted_map[cleaned_sentence] = r_name

                # PADDING & MINIMUM DURATION LOGIC (MIN. 15 SECONDS EQUALLY PADDED)
                audio_start_ms = max(0, start_ms - 2000)
                audio_end_ms = min(audio_duration_ms, end_ms + 2000)

                current_duration = audio_end_ms - audio_start_ms
                MIN_DURATION_MS = 15000  # 15 Seconds

                if current_duration < MIN_DURATION_MS:
                    needed_extra = MIN_DURATION_MS - current_duration
                    pad_left = needed_extra // 2
                    pad_right = needed_extra - pad_left
                    
                    audio_start_ms -= pad_left
                    audio_end_ms += pad_right

                    if audio_start_ms < 0:
                        audio_end_ms = min(audio_duration_ms, audio_end_ms + abs(audio_start_ms))
                        audio_start_ms = 0

                    if audio_end_ms > audio_duration_ms:
                        audio_start_ms = max(0, audio_start_ms - (audio_end_ms - audio_duration_ms))
                        audio_end_ms = audio_duration_ms

                output_audio_path = os.path.join(output_dir, f"{r_name}.mp3")
                
                # Export audio clip
                audio_segment = full_audio[audio_start_ms:audio_end_ms]
                audio_segment = audio_segment.set_channels(quality["channels"]).set_frame_rate(quality["frame_rate"])
                audio_segment.export(output_audio_path, format=quality["format"], bitrate=quality["bitrate"])

                sound_tag = f"[sound:{r_name}.mp3]"
                row[AUDIO_FRONT_COLUMN] = sound_tag
                row[AUDIO_BACK_COLUMN] = sound_tag

                # Export screenshot (without padding)
                if want_screenshots:
                    output_image_path = os.path.join(output_dir, f"{r_name}.jpg")
                    if extract_video_frame(media_path, start_ms, output_image_path):
                        row[IMAGE_COLUMN_NAME] = f'<img src="{r_name}.jpg">'

        print(f"Media extraction finished for {base_name}.")

    # --- SAVE UPDATED OUTPUT TSV WITH SUFFIX _output ---
    output_tsv_path = os.path.join(orig_dir, f"{base_name}_output.tsv")
    with open(output_tsv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(table_rows)
    print(f"New output TSV created: {output_tsv_path}")

    # --- PART 2: 3-BLOCK ASS SUBTITLE CREATION & HIGHLIGHTING ---
    if run_subs and sub_path:
        print(f"\n[PART 2] Generating and Formatting ASS subtitles for {base_name}...")
        ass_path = os.path.splitext(sub_path)[0] + ".ass"
        
        # 1. Base Conversion
        convert_srt_to_ass(sub_path, ass_path)
        
        # 2. Highlighting & Definitions from Table
        print("\nApplying color highlights and definitions from table...")
        row_colors = {}
        for row in table_rows:
            word = row.get(WORD_COLUMN_NAME, "")
            sentence = row.get(SENTENCE_COLUMN_NAME, "")
            if word and sentence:
                entry_key = (word, sentence)
                if entry_key not in row_colors:
                    row_colors[entry_key] = generate_bright_ass_color()

        with open(ass_path, mode="r", encoding="utf-8") as f:
            ass_lines = f.readlines()

        new_ass_lines = []
        total_lines = len(ass_lines)
        unmatched_subs_count = 0
        matched_table_indices = set()

        print_progress_bar(0, total_lines, prefix='Subtitle Progress:', suffix=f'(0/{total_lines} lines)', length=40)

        for line_idx, line in enumerate(ass_lines):
            if not line.startswith("Dialogue:"):
                new_ass_lines.append(line)
                print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)
                continue

            parts = line.split(",", 9)
            if len(parts) < 10:
                new_ass_lines.append(line)
                print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)
                continue

            prefix = parts[:9]
            text_part = parts[9].rstrip("\r\n")
            
            style = prefix[3].strip()
            if style != "Text":
                new_ass_lines.append(line)
                print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)
                continue

            is_active_block = "●" in text_part

            bullet_idx = text_part.find("●")
            if bullet_idx != -1:
                prefix_part = text_part[:bullet_idx + 1]
                text_to_process = text_part[bullet_idx + 1:]
            else:
                prefix_part = ""
                text_to_process = text_part

            cleaned_ass_text = clean_text_subs(text_to_process)
            clean_text_for_locating, mapping = get_clean_map(text_to_process)

            matched_items = []
            for t_idx, row in enumerate(table_rows):
                word = row.get(WORD_COLUMN_NAME, "")
                sentence_plain = row.get(SENTENCE_COLUMN_NAME, "")

                if not word or not sentence_plain:
                    continue

                cleaned_sentence = clean_text_subs(sentence_plain)

                if word in clean_text_for_locating:
                    if cleaned_sentence in cleaned_ass_text or cleaned_ass_text in cleaned_sentence:
                        if row not in matched_items:
                            matched_items.append(row)
                        matched_table_indices.add(t_idx)
                    elif window_search_match(cleaned_sentence, cleaned_ass_text, min_ratio=0.55) or \
                         window_search_match(cleaned_ass_text, cleaned_sentence, min_ratio=0.55):
                        if row not in matched_items:
                            matched_items.append(row)
                        matched_table_indices.add(t_idx)

            if not matched_items:
                new_ass_lines.append(line)
                print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)
                continue

            if is_active_block:
                intervals = []
                for item in matched_items:
                    word = item[WORD_COLUMN_NAME]
                    color = row_colors[(word, item[SENTENCE_COLUMN_NAME])]
                    
                    start_pos = 0
                    while True:
                        idx = clean_text_for_locating.find(word, start_pos)
                        if idx == -1:
                            break
                        intervals.append({
                            'start': idx,
                            'end': idx + len(word),
                            'word': word,
                            'color': color,
                            'length': len(word)
                        })
                        start_pos = idx + 1

                style_at_clean = [None] * len(clean_text_for_locating)
                for j in range(len(clean_text_for_locating)):
                    covering = [inv for inv in intervals if inv['start'] <= j < inv['end']]
                    if covering:
                        covering.sort(key=lambda x: x['length']) 
                        style_at_clean[j] = covering[0]

                orig_style = {}
                for j, orig_idx in enumerate(mapping):
                    orig_style[orig_idx] = style_at_clean[j]

                reconstructed = []
                current_style = None
                k = 0
                n_orig = len(text_to_process)

                while k < n_orig:
                    if k in orig_style:
                        target_style = orig_style[k]
                        if target_style != current_style:
                            if target_style is None:
                                reconstructed.append(r"{\b0\c&H000000&}")
                            else:
                                reconstructed.append(f"{{\\b1\\c&H{target_style['color']}&}}")
                            current_style = target_style

                    if text_to_process[k] == '{':
                        end = text_to_process.find('}', k)
                        if end != -1:
                            reconstructed.append(text_to_process[k:end+1])
                            k = end + 1
                            continue

                    if k + 1 < n_orig and text_to_process[k] == '\\' and text_to_process[k+1].lower() == 'n':
                        reconstructed.append(text_to_process[k:k+2])
                        k += 2
                        continue

                    reconstructed.append(text_to_process[k])
                    k += 1

                if current_style is not None:
                    reconstructed.append(r"{\b0\c&H000000&}")

                updated_text_part = prefix_part + "".join(reconstructed)

                matched_items_sorted_by_appearance = sorted(
                    matched_items, 
                    key=lambda r: clean_text_for_locating.find(r[WORD_COLUMN_NAME])
                )

                defs_to_render = []
                for item in matched_items_sorted_by_appearance:
                    word = item[WORD_COLUMN_NAME]
                    definition = item.get(DEFINITION_COLUMN_NAME, "")
                    sentence_plain = item[SENTENCE_COLUMN_NAME]
                    color = row_colors[(word, sentence_plain)]
                    if definition:
                        defs_to_render.append(f"{{\\c&H{color}&}}{definition}")

                pos_match = re.search(r"\{\\pos\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\}", text_part)
                
                if not pos_match and defs_to_render:
                    x_coord = 120
                    y_new = Y_DEFINITION
                    pos_match = True
                elif pos_match:
                    x_coord = int(pos_match.group(1))
                    y_coord = int(pos_match.group(2))
                    y_new = y_coord - 100

                if pos_match and defs_to_render:
                    def_combined_text = "    ".join(defs_to_render)
                    def_text_part = f"{{\\pos({x_coord},{y_new})}}{def_combined_text}"
                    def_line = ",".join(prefix) + "," + def_text_part + "\n"
                    new_ass_lines.append(def_line)

                modified_main_line = ",".join(prefix) + "," + updated_text_part + "\n"
                new_ass_lines.append(modified_main_line)
            else:
                new_ass_lines.append(line)
            
            print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)

        # Create a backup
        if backup_dir:
            try:
                os.makedirs(backup_dir, exist_ok=True)
                ass_base_name = os.path.basename(ass_path)
                name_parts = os.path.splitext(ass_base_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{name_parts[0]}_backup_{timestamp}{name_parts[1]}"
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy2(ass_path, backup_path)
                print(f"\n[BACKUP] Safety copy of ASS file created at: {backup_path}")
            except Exception as backup_error:
                print(f"\n[BACKUP WARNING] Failed to create safety copy: {backup_error}")

        with open(ass_path, mode="w", encoding="utf-8") as f:
            f.writelines(new_ass_lines)

        print(f"ASS subtitle modification complete. Unmapped table entries: {unmatched_subs_count}")

    # --- RENAME PREP INPUT TSV WITH SUFFIX _processed ---
    processed_tsv_path = os.path.join(orig_dir, f"{base_name}_processed.tsv")
    try:
        if os.path.exists(processed_tsv_path):
            os.remove(processed_tsv_path)
        os.rename(table_path, processed_tsv_path)
        print(f"Renamed prep file: '{os.path.basename(table_path)}' -> '{os.path.basename(processed_tsv_path)}'")
    except Exception as e:
        print(f"Error renaming prep file: {e}")

    print(f"=== FINISHED PROCESSING TRIPLE: {base_name} ===")

def scan_batch_triples(selected_dir):
    """Scans the directory tree for matching TSV, SRT, and Video/Media triples"""
    valid_triples = []
    orphans = []
    
    media_extensions = ('.mp4', '.mkv', '.m4a', '.mp3', '.wav', '.avi', '.webm')

    for root, dirs, files in os.walk(selected_dir):
        tsv_map = {}
        srt_map = {}
        media_map = {}

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            base = os.path.splitext(f)[0]

            # Ignore previously processed/output files
            if ext in ['.tsv', '.csv']:
                if base.endswith('_processed') or base.endswith('_output') or base.startswith('output_'):
                    continue
                tsv_map[base] = os.path.join(root, f)
            elif ext == '.srt':
                srt_map[base] = os.path.join(root, f)
            elif ext in media_extensions:
                media_map[base] = os.path.join(root, f)

        tsv_set = set(tsv_map.keys())
        srt_set = set(srt_map.keys())
        media_set = set(media_map.keys())

        matched_bases = tsv_set.intersection(srt_set).intersection(media_set)

        for base in matched_bases:
            valid_triples.append({
                'base': base,
                'tsv_path': tsv_map[base],
                'srt_path': srt_map[base],
                'media_path': media_map[base],
                'folder': root
            })

        # Track incomplete files for warnings
        all_found = tsv_set.union(srt_set).union(media_set)
        for base in all_found - matched_bases:
            missing = []
            if base not in tsv_set: missing.append("TSV")
            if base not in srt_set: missing.append("SRT")
            if base not in media_set: missing.append("Media")
            orphans.append(f"Incomplete matching for '{base}' in '{root}' (Missing: {', '.join(missing)})")

    return valid_triples, orphans

def main():
    root = tk.Tk()
    root.withdraw()

    # Step 1: Check paths.txt configuration at startup
    paths_config = load_paths_config()
    if paths_config is None:
        print("=" * 60)
        print(" PATH CONFIGURATION")
        print("=" * 60)
        print("No valid paths found in paths.txt.")
        choice = input("Would you like to configure default hardcoded paths now? (y/n): ").strip().lower()
        if choice == 'y':
            paths_config = configure_paths_interactive()
    else:
        print("=" * 60)
        print(" LOADED PATHS FROM paths.txt")
        print("=" * 60)
        print(f" Media Output Dir: {paths_config.get('MEDIA_OUTPUT_DIR') or 'Not configured'}")
        print(f" Subtitle Backup:  {paths_config.get('BACKUP_DIR') or 'Not configured'}")
        print("=" * 60)

    # Step 2: Main loop for process selection / path configuration
    while True:
        process_type = get_process_type()
        if process_type == "3":
            paths_config = configure_paths_interactive()
            continue
        break

    mode = get_execution_mode()
    
    run_media = (mode in ["1", "2"])
    run_subs = (mode in ["1", "3"])

    # Step 3: Handle Media Output Directory
    output_dir = None
    if paths_config and paths_config.get("MEDIA_OUTPUT_DIR"):
        output_dir = paths_config["MEDIA_OUTPUT_DIR"]

    quality = None
    want_screenshots = False

    if run_media:
        if not output_dir:
            print("\nPlease select the target folder for Anki media...")
            output_dir = filedialog.askdirectory(title="Select Output Folder for Anki Media")
            if not output_dir:
                print("No output folder selected. Operation cancelled.")
                return
        else:
            print(f"\nUsing configured destination folder: {output_dir}")

        os.makedirs(output_dir, exist_ok=True)
        quality = get_audio_quality_settings()

        if OPENCV_AVAILABLE:
            screenshot_input = input("Extract screenshots? (y/n): ").strip().lower()
            if screenshot_input == 'y':
                want_screenshots = True

    # Step 4: Handle Subtitle Backup Directory
    backup_dir = None
    if paths_config and paths_config.get("BACKUP_DIR"):
        backup_dir = paths_config["BACKUP_DIR"]

    if run_subs:
        if not backup_dir:
            print("\nPlease select the backup directory for ASS subtitles...")
            backup_dir = filedialog.askdirectory(title="Subtitle Backup Directory")
            if not backup_dir:
                print("No backup folder selected. Operation cancelled.")
                return
        else:
            print(f"Using configured subtitle backup directory: {backup_dir}")

        os.makedirs(backup_dir, exist_ok=True)

    # ---------------- BATCH PROCESS MODE ----------------
    if process_type == "1":
        print("\nPlease select the root directory to scan in the window that opens...")
        selected_dir = filedialog.askdirectory(title="Select Directory for Batch Processing")
        if not selected_dir:
            print("No directory selected. Operation cancelled.")
            return

        print(f"\nScanning '{selected_dir}' for valid triples (.tsv, .srt, media)...")
        triples, orphans = scan_batch_triples(selected_dir)

        if orphans:
            print("\n" + "="*60)
            print(" WARNING: Incomplete Triples Found (Skipped)")
            print("="*60)
            for orphan in orphans:
                print(orphan)
            print("="*60 + "\n")

        if not triples:
            print("No valid complete triples (.tsv, .srt, media) found.")
            return

        triples.sort(key=lambda x: x['base'])

        print("\nFound Valid Triples:")
        print("="*60)
        for idx, item in enumerate(triples):
            print(f" [{idx}] {item['base']}")
            print(f"     └─ Folder: {item['folder']}")
        print("="*60)

        try:
            start_idx = int(input(f"Enter start index (0 to {len(triples)-1}): "))
            end_idx = int(input(f"Enter end index ({start_idx} to {len(triples)-1}): "))
        except ValueError:
            print("Invalid input. Exiting.")
            return

        if start_idx < 0 or end_idx >= len(triples) or start_idx > end_idx:
            print("Index out of bounds. Exiting.")
            return

        print(f"\nStarting Batch Processing for items {start_idx} through {end_idx}...\n")
        for i in range(start_idx, end_idx + 1):
            item = triples[i]
            print(f"\n---> Processing Batch Item [{i}]: {item['base']}")
            process_single_triple(
                table_path=item['tsv_path'],
                sub_path=item['srt_path'],
                media_path=item['media_path'],
                mode=mode,
                quality=quality,
                want_screenshots=want_screenshots,
                output_dir=output_dir,
                backup_dir=backup_dir
            )

    # ---------------- SINGLE FILE MODE ----------------
    else:
        print("\nPlease select the table file (TSV/CSV)...")
        table_path = filedialog.askopenfilename(
            title="Select Table File",
            filetypes=[("Table Files", "*.tsv *.csv"), ("All Files", "*.*")]
        )
        if not table_path:
            print("Operation cancelled.")
            return

        print("Please select the SRT subtitle file...")
        sub_path = filedialog.askopenfilename(
            title="Select SRT Subtitles",
            filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
        )
        if not sub_path:
            print("Operation cancelled.")
            return

        media_path = None
        if run_media:
            print("Please select the video/audio file...")
            media_path = filedialog.askopenfilename(
                title="Select Media File",
                filetypes=[("Media Files", "*.m4a *.mp4 *.mkv *.mp3 *.wav"), ("All Files", "*.*")]
            )
            if not media_path:
                print("Operation cancelled.")
                return

        process_single_triple(
            table_path=table_path,
            sub_path=sub_path,
            media_path=media_path,
            mode=mode,
            quality=quality,
            want_screenshots=want_screenshots,
            output_dir=output_dir,
            backup_dir=backup_dir
        )

    print("\n=== ALL PROCESSES COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()