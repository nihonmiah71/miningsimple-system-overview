import os
import re
import csv
import hashlib
import sys
import random
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
from pydub import AudioSegment
from difflib import SequenceMatcher
from datetime import datetime

# ---- CONFIGURATION ----
WORD_COLUMN_NAME = "Word"
SENTENCE_COLUMN_NAME = "SentencePlain"
DEFINITION_COLUMN_NAME = "Correct English Definition"

MATCH_THRESHOLD = 0.45  # Baseline for Audio-Matching
LOG_FILE_NAME = "debug_missing_matches.log"
CONFIG_FILE_NAME = "paths.txt"
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

        audio_dir = paths.get("AUDIO_OUTPUT_DIR", "")
        backup_dir = paths.get("BACKUP_DIR", "")

        if not audio_dir and not backup_dir:
            return None

        return {
            "AUDIO_OUTPUT_DIR": audio_dir if audio_dir else None,
            "BACKUP_DIR": backup_dir if backup_dir else None
        }
    except Exception as e:
        print(f"Warning: Failed to read {CONFIG_FILE_NAME}: {e}")
        return None

def save_paths_config(audio_dir, backup_dir):
    """Saves configured paths to paths.txt"""
    config_path = get_config_file_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"AUDIO_OUTPUT_DIR={audio_dir or ''}\n")
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
    
    print("Please select the Audio Output Directory...")
    audio_dir = filedialog.askdirectory(title="Select Default Audio Output Directory")
    if audio_dir:
        print(f"Audio Output Directory set to: {audio_dir}")
    else:
        print("Audio Output Directory skipped.")

    print("\nPlease select the Subtitle Backup Directory...")
    backup_dir = filedialog.askdirectory(title="Select Default Subtitle Backup Directory")
    if backup_dir:
        print(f"Subtitle Backup Directory set to: {backup_dir}")
    else:
        print("Subtitle Backup Directory skipped.")

    if audio_dir or backup_dir:
        save_paths_config(audio_dir, backup_dir)
        return {
            "AUDIO_OUTPUT_DIR": audio_dir if audio_dir else None,
            "BACKUP_DIR": backup_dir if backup_dir else None
        }
    else:
        print("\nNo paths were configured.")
        return None

def get_process_type():
    print("=" * 60)
    print(" CHOOSE PROCESSING TYPE")
    print("=" * 60)
    print(" [1] Batch Process (Scan directory for matching triples)")
    print(" [2] Single File Process (Manual file selection)")
    print(" [3] Configure Default Paths (Audio & Backup directories)")
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
    print(" [1] Full Process (Audio Extraction & Subtitle Marking)")
    print(" [2] Audio Extraction Only (Cut from M4A & generate new TSV)")
    print(" [3] Subtitle Marking Only (Add colors and definitions to ASS)")
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
    print(" [1] Best Quality (Lossless / Highest Bitrate - Stereo, 44.1kHz, 320k)")
    print(" [2] High Quality (Stereo, 44.1kHz, 192k)")
    print(" [3] Good Quality (Standard - Stereo, 44.1kHz, 128k)")
    print(" [4] Low Quality (Mono, 22.05kHz, 64k)")
    print(" [5] Lowest Quality (Very compact - Mono, 22.05kHz, 24k)")
    print("=" * 60)
    
    while True:
        choice = input("Please select a quality level (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            break
        print("Invalid input. Please enter a number from 1 to 5.")

    if choice == "1":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "320k", "format": "mp3"}
    elif choice == "2":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "192k", "format": "mp3"}
    elif choice == "3":
        return {"channels": 2, "frame_rate": 44100, "bitrate": "128k", "format": "mp3"}
    elif choice == "4":
        return {"channels": 1, "frame_rate": 22050, "bitrate": "64k", "format": "mp3"}
    elif choice == "5":
        return {"channels": 1, "frame_rate": 22050, "bitrate": "24k", "format": "mp3"}

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '░' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} [{bar}] {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()

def normalize_text_audio(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{[^}]+\}', '', text)
    text = re.sub(r'\\N', '', text)
    text = re.sub(r'\\n', '', text)
    text = text.replace('●', '')
    text = re.sub(r'[\s+、。！？「」『』()（）.,!?\-=_+*⑨<>█░…·•\"\'’]', '', text)
    
    katakana = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモヤャユュヨョラリルレロワヮヰヱヲンヴヵヶ"
    hiragana = "ぁあぃいううぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゃゆゅよょらりるれろわゎゐゑをんゔゕゖ"
    trans = str.maketrans(katakana, hiragana)
    text = text.translate(trans)
    return text.strip()

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

def log_failed_match(row_idx, raw_sentence, normalized_sentence, ass_blocks):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scored_blocks = []
    for block in ass_blocks:
        matcher = SequenceMatcher(None, normalized_sentence, block['text'])
        scored_blocks.append({'block': block, 'ratio': matcher.ratio()})
    
    scored_blocks.sort(key=lambda x: x['ratio'], reverse=True)
    top_matches = scored_blocks[:3]
    
    with open(LOG_FILE_NAME, "a", encoding="utf-8") as log_file:
        log_file.write("="*80 + "\n")
        log_file.write(f"[{timestamp}] NO AUDIO MATCH FOUND FOR ROW {row_idx}\n")
        log_file.write("="*80 + "\n")
        log_file.write(f"Original TSV Text: {raw_sentence}\n")
        log_file.write(f"Normalized TSV Text: {normalized_sentence}\n\n")
        log_file.write("Top 3 most similar ASS blocks:\n")
        log_file.write(f"{'Start Time':<12} | {'Ratio':<6} | {'Normalized ASS Text'}\n")
        log_file.write("-" * 80 + "\n")
        for item in top_matches:
            block = item['block']
            ratio = item['ratio']
            total_secs = block['start'] / 1000
            h = int(total_secs // 3600)
            m = int((total_secs % 3600) // 60)
            s = int(total_secs % 60)
            ms = int(block['start'] % 1000)
            time_str = f"{h:01d}:{m:02d}:{s:02d}.{ms//10:02d}"
            log_file.write(f"{time_str:<12} | {ratio:.4f} | {block['text']}\n")
        log_file.write("\n\n")

def ass_time_to_ms(time_str):
    try:
        parts = time_str.strip().split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        frac_str = seconds_parts[1]
        if len(frac_str) == 2:
            ms = int(frac_str) * 10
        elif len(frac_str) == 3:
            ms = int(frac_str)
        else:
            ms = int(frac_str[:3].ljust(3, '0'))
        return (hours * 3600 + minutes * 60 + seconds) * 1000 + ms
    except Exception:
        return None

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

def is_single_block_match(tsv_sentence, block):
    if SequenceMatcher(None, tsv_sentence, block['text']).ratio() >= MATCH_THRESHOLD:
        return True
    if tsv_sentence in block['text'] or block['text'] in tsv_sentence:
        return True
    if window_search_match(tsv_sentence, block['text'], min_ratio=0.50):
        return True
    return False

def parse_ass_file_for_audio(ass_path):
    temp_blocks = {}
    if not os.path.exists(ass_path):
        return []

    with open(ass_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    start_str = parts[1]
                    end_str = parts[2]
                    style = parts[3].strip()
                    text_content = parts[9]
                    
                    if style.lower() == 'text' and '●' in text_content:
                        start_ms = ass_time_to_ms(start_str)
                        end_ms = ass_time_to_ms(end_str)
                        
                        if start_ms is not None and end_ms is not None:
                            time_key = (start_ms, end_ms)
                            if time_key in temp_blocks:
                                temp_blocks[time_key] += " " + text_content
                            else:
                                temp_blocks[time_key] = text_content
    
    blocks = []
    for (start_ms, end_ms), raw_text in temp_blocks.items():
        blocks.append({
            'start': start_ms,
            'end': end_ms,
            'text': normalize_text_audio(raw_text)
        })
    blocks.sort(key=lambda x: x['start'])
    return blocks

def generate_bright_ass_color():
    b = random.randint(120, 255)
    g = random.randint(120, 255)
    r = random.randint(120, 255)
    return f"{b:02X}{g:02X}{r:02X}"

def process_single_triple(table_path, ass_path, media_path, mode, quality, output_dir, backup_dir):
    """Core logic to process a single file set"""
    run_audio = (mode in ["1", "2"])
    run_subs = (mode in ["1", "3"])

    base_name = os.path.splitext(os.path.basename(table_path))[0]
    orig_dir = os.path.dirname(table_path)

    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        delimiter = "\t"
        if ";" in sample and sample.count(";") > sample.count("\t"):
            delimiter = ";"
        elif "," in sample and sample.count(",") > sample.count("\t"):
            delimiter = ","

    table_rows = []
    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items() if k}
            table_rows.append(cleaned_row)

    if not table_rows:
        print(f"Error: The selected table '{os.path.basename(table_path)}' is empty.")
        return

    required_cols = [WORD_COLUMN_NAME, SENTENCE_COLUMN_NAME, DEFINITION_COLUMN_NAME]
    missing_cols = [col for col in required_cols if col not in table_rows[0]]
    if missing_cols:
        print(f"Error: Required columns are missing from the table: {missing_cols}")
        return

    # --- AUDIO PROCESSING ---
    if run_audio and media_path:
        if 'SoundFront' not in fieldnames:
            fieldnames.append('SoundFront')
        if 'SoundBack' not in fieldnames:
            fieldnames.append('SoundBack')

        print(f"\n[PART 1] Starting audio extraction for {base_name}...")
        ass_blocks_for_audio = parse_ass_file_for_audio(ass_path)
        
        full_audio = None
        repaired_path = None
        repaired_file_created = False

        print(f"Loading main audio file ({os.path.basename(media_path)})...")
        try:
            full_audio = AudioSegment.from_file(media_path)
        except Exception as e:
            print(f"Error loading audio file: {e}")
            print("Attempting to run auto-repair using FFmpeg...")
            
            dir_name = os.path.dirname(media_path)
            base_media_name = os.path.basename(media_path)
            name, ext = os.path.splitext(base_media_name)
            repaired_path = os.path.join(dir_name, f"{name}_repariert{ext}")
            
            cmd = [
                "ffmpeg",
                "-y",
                "-err_detect", "ignore_err",
                "-i", media_path,
                "-c:a", "aac",
                repaired_path
            ]
            
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if os.path.exists(repaired_path) and os.path.getsize(repaired_path) > 0:
                    print(f"Successfully created repaired audio file: {repaired_path}")
                    print("Loading repaired audio file...")
                    full_audio = AudioSegment.from_file(repaired_path)
                    repaired_file_created = True
                else:
                    print("FFmpeg repair failed. Repaired file could not be created.")
                    if result.stderr:
                        print(f"FFmpeg output:\n{result.stderr}")
                    return
            except Exception as repair_err:
                print(f"Failed to execute FFmpeg repair: {repair_err}")
                return

        generated_audios_cache = {}
        failed_matches_count = 0
        total_rows = len(table_rows)
        last_match_index = 0
        num_ass_blocks = len(ass_blocks_for_audio)

        print_progress_bar(0, total_rows, prefix='Audio Progress:', suffix=f'(0/{total_rows} rows)', length=40)

        for i, row in enumerate(table_rows):
            current_row_num = i + 2
            raw_sentence = row[SENTENCE_COLUMN_NAME]
            normalized_tsv_sentence = normalize_text_audio(raw_sentence)

            if not normalized_tsv_sentence:
                print_progress_bar(i + 1, total_rows, prefix='Audio Progress:', suffix=f'({i + 1}/{total_rows} rows)', length=40)
                continue

            if normalized_tsv_sentence in generated_audios_cache:
                sound_tag = f"[sound:{generated_audios_cache[normalized_tsv_sentence]}]"
                row['SoundFront'] = sound_tag
                row['SoundBack'] = sound_tag
                print_progress_bar(i + 1, total_rows, prefix='Audio Progress:', suffix=f'({i + 1}/{total_rows} rows)', length=40)
                continue

            found_block = None
            found_at_idx = -1

            for idx in range(last_match_index, num_ass_blocks):
                if is_single_block_match(normalized_tsv_sentence, ass_blocks_for_audio[idx]):
                    found_block = ass_blocks_for_audio[idx]
                    found_at_idx = idx
                    break

            if found_block is None and last_match_index > 0:
                for idx in range(0, last_match_index):
                    if is_single_block_match(normalized_tsv_sentence, ass_blocks_for_audio[idx]):
                        found_block = ass_blocks_for_audio[idx]
                        found_at_idx = idx
                        break

            if found_block is None:
                sys.stdout.write("\n")
                print(f"Row {current_row_num}: No audio match found for '{raw_sentence[:20]}...'.")
                log_failed_match(current_row_num, raw_sentence, normalized_tsv_sentence, ass_blocks_for_audio)
                failed_matches_count += 1
                print_progress_bar(i + 1, total_rows, prefix='Audio Progress:', suffix=f'({i + 1}/{total_rows} rows)', length=40)
                continue

            last_match_index = found_at_idx
            start_time = found_block['start']
            end_time = found_block['end']
            
            text_hash = hashlib.md5(normalized_tsv_sentence.encode('utf-8')).hexdigest()[:10]
            audio_filename = f"audio_{text_hash}.mp3"
            output_path = os.path.join(output_dir, audio_filename)

            if not os.path.exists(output_path):
                audio_segment = full_audio[start_time:end_time]
                audio_segment = audio_segment.set_channels(quality["channels"])
                audio_segment = audio_segment.set_frame_rate(quality["frame_rate"])
                audio_segment.export(output_path, format=quality["format"], bitrate=quality["bitrate"])

            generated_audios_cache[normalized_tsv_sentence] = audio_filename
            sound_tag = f"[sound:{audio_filename}]"
            row['SoundFront'] = sound_tag
            row['SoundBack'] = sound_tag
            
            print_progress_bar(i + 1, total_rows, prefix='Audio Progress:', suffix=f'({i + 1}/{total_rows} rows)', length=40)

        if repaired_file_created and repaired_path and os.path.exists(repaired_path):
            try:
                del full_audio
                os.remove(repaired_path)
                print(f"\n[CLEANUP] Temporary repaired file removed: {repaired_path}")
            except Exception as cleanup_error:
                print(f"\n[CLEANUP WARNING] Could not remove {repaired_path}: {cleanup_error}")

        output_tsv_path = os.path.join(orig_dir, f"{base_name}_output.tsv")

        with open(output_tsv_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(table_rows)

        print(f"\n[TSV EXPORT] New file created: {output_tsv_path}")
        print(f"Audio extraction complete. Unmatched rows: {failed_matches_count}")

    # --- SUBTITLE PROCESSING ---
    if run_subs and ass_path:
        print(f"\n[PART 2] Starting ASS subtitle processing for {base_name}...")
        row_colors = {}
        for row in table_rows:
            word = row[WORD_COLUMN_NAME]
            sentence = row[SENTENCE_COLUMN_NAME]
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

            cleaned_ass_text = clean_text_subs(text_part)
            clean_text_for_locating, mapping = get_clean_map(text_part)

            matched_items = []
            for t_idx, row in enumerate(table_rows):
                word = row[WORD_COLUMN_NAME]
                sentence_plain = row[SENTENCE_COLUMN_NAME]

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
            n_orig = len(text_part)

            while k < n_orig:
                if k in orig_style:
                    target_style = orig_style[k]
                    if target_style != current_style:
                        if target_style is None:
                            reconstructed.append(r"{\b0\c&HFFFFFF&}")
                        else:
                            reconstructed.append(f"{{\\b1\\c&H{target_style['color']}&}}")
                        current_style = target_style

                if text_part[k] == '{':
                    end = text_part.find('}', k)
                    if end != -1:
                        reconstructed.append(text_part[k:end+1])
                        k = end + 1
                        continue

                if k + 1 < n_orig and text_part[k] == '\\' and text_part[k+1].lower() == 'n':
                    reconstructed.append(text_part[k:k+2])
                    k += 2
                    continue

                reconstructed.append(text_part[k])
                k += 1

            if current_style is not None:
                reconstructed.append(r"{\b0\c&HFFFFFF&}")

            updated_text_part = "".join(reconstructed)

            matched_items_sorted_by_appearance = sorted(
                matched_items, 
                key=lambda r: clean_text_for_locating.find(r[WORD_COLUMN_NAME])
            )

            defs_to_render = []
            for item in matched_items_sorted_by_appearance:
                word = item[WORD_COLUMN_NAME]
                definition = item[DEFINITION_COLUMN_NAME]
                sentence_plain = item[SENTENCE_COLUMN_NAME]
                color = row_colors[(word, sentence_plain)]
                defs_to_render.append(f"{{\\c&H{color}&}}{definition}")

            pos_match = re.search(r"\{\\pos\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\}", text_part)

            if pos_match and defs_to_render:
                x_coord = int(pos_match.group(1))
                y_coord = int(pos_match.group(2))
                y_new = y_coord - 100

                def_combined_text = "    ".join(defs_to_render)
                def_text_part = f"{{\\pos({x_coord},{y_new})}}{def_combined_text}"

                def_line = ",".join(prefix) + "," + def_text_part + "\n"
                new_ass_lines.append(def_line)

            modified_main_line = ",".join(prefix) + "," + updated_text_part + "\n"
            new_ass_lines.append(modified_main_line)
            
            print_progress_bar(line_idx + 1, total_lines, prefix='Subtitle Progress:', suffix=f'({line_idx + 1}/{total_lines} lines)', length=40)

        print("\nChecking for unmatched subtitle entries...")
        for t_idx, row in enumerate(table_rows):
            if t_idx not in matched_table_indices:
                unmatched_subs_count += 1
                print(f" -> Table row {t_idx + 2}: No ASS match for word '{row[WORD_COLUMN_NAME]}' in '{row[SENTENCE_COLUMN_NAME][:20]}...'")

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

    # Rename prep input TSV to _processed.tsv
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
    """Scans the directory tree for matching TSV, ASS, and Media triples"""
    valid_triples = []
    orphans = []
    
    media_extensions = ('.m4a', '.mp3', '.wav', '.aac', '.mp4', '.mkv', '.avi', '.webm')

    for root, dirs, files in os.walk(selected_dir):
        tsv_map = {}
        ass_map = {}
        media_map = {}

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            base = os.path.splitext(f)[0]

            if ext in ['.tsv', '.csv']:
                if base.endswith('_processed') or base.endswith('_output') or base.startswith('output_'):
                    continue
                tsv_map[base] = os.path.join(root, f)
            elif ext == '.ass':
                ass_map[base] = os.path.join(root, f)
            elif ext in media_extensions:
                media_map[base] = os.path.join(root, f)

        tsv_set = set(tsv_map.keys())
        ass_set = set(ass_map.keys())
        media_set = set(media_map.keys())

        matched_bases = tsv_set.intersection(ass_set).intersection(media_set)

        for base in matched_bases:
            valid_triples.append({
                'base': base,
                'tsv_path': tsv_map[base],
                'ass_path': ass_map[base],
                'media_path': media_map[base],
                'folder': root
            })

        all_found = tsv_set.union(ass_set).union(media_set)
        for base in all_found - matched_bases:
            missing = []
            if base not in tsv_set: missing.append("TSV")
            if base not in ass_set: missing.append("ASS")
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
        print(f" Audio Output Dir: {paths_config.get('AUDIO_OUTPUT_DIR') or 'Not configured'}")
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
    
    run_audio = (mode in ["1", "2"])
    run_subs = (mode in ["1", "3"])

    # Step 3: Handle Audio Output Directory
    output_dir = None
    if paths_config and paths_config.get("AUDIO_OUTPUT_DIR"):
        output_dir = paths_config["AUDIO_OUTPUT_DIR"]

    quality = None
    if run_audio:
        if not output_dir:
            print("\nPlease select the output directory for audio export...")
            output_dir = filedialog.askdirectory(title="Audio Export Directory")
            if not output_dir:
                print("Operation cancelled. Audio output directory is required.")
                return
        else:
            print(f"\nUsing configured audio output directory: {output_dir}")

        quality = get_audio_quality_settings()
        os.makedirs(output_dir, exist_ok=True)

    # Step 4: Handle Subtitle Backup Directory
    backup_dir = None
    if paths_config and paths_config.get("BACKUP_DIR"):
        backup_dir = paths_config["BACKUP_DIR"]

    if run_subs:
        if not backup_dir:
            print("\nPlease select the backup directory for ASS subtitles...")
            backup_dir = filedialog.askdirectory(title="Subtitle Backup Directory")
            if not backup_dir:
                print("Operation cancelled. Subtitle backup directory is required.")
                return
        else:
            print(f"Using configured subtitle backup directory: {backup_dir}")

        os.makedirs(backup_dir, exist_ok=True)

    # ---------------- BATCH PROCESS MODE ----------------
    if process_type == "1":
        print("\nPlease select the root directory to scan in the window that opens...")
        selected_dir = filedialog.askdirectory(title="Select Directory for Batch Processing")
        if not selected_dir:
            print("Operation cancelled.")
            return

        print(f"\nScanning '{selected_dir}' for valid triples (.tsv, .ass, media)...")
        triples, orphans = scan_batch_triples(selected_dir)

        if orphans:
            print("\n" + "="*60)
            print(" WARNING: Incomplete Triples Found (Skipped)")
            print("="*60)
            for orphan in orphans:
                print(orphan)
            print("="*60 + "\n")

        if not triples:
            print("No valid complete triples (.tsv, .ass, media) found.")
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
                ass_path=item['ass_path'],
                media_path=item['media_path'],
                mode=mode,
                quality=quality,
                output_dir=output_dir,
                backup_dir=backup_dir
            )

    # ---------------- SINGLE FILE MODE ----------------
    else:
        print("\nPlease select the table file (TSV/CSV)...")
        table_path = filedialog.askopenfilename(
            title="Select the table file (TSV/CSV)",
            filetypes=[("Table Files", "*.tsv *.csv"), ("All Files", "*.*")]
        )
        if not table_path:
            print("Operation cancelled.")
            return

        print("Please select the ASS subtitle file...")
        ass_path = filedialog.askopenfilename(
            title="Select the ASS subtitle file",
            filetypes=[("ASS Subtitles", "*.ass"), ("All Files", "*.*")]
        )
        if not ass_path:
            print("Operation cancelled.")
            return

        media_path = None
        if run_audio:
            print("Please select the M4A audio file...")
            media_path = filedialog.askopenfilename(
                title="Select the M4A audio file",
                filetypes=[("Audio Files", "*.m4a *.mp3 *.wav *.aac"), ("All Files", "*.*")]
            )
            if not media_path:
                print("Operation cancelled.")
                return

        process_single_triple(
            table_path=table_path,
            ass_path=ass_path,
            media_path=media_path,
            mode=mode,
            quality=quality,
            output_dir=output_dir,
            backup_dir=backup_dir
        )

    print("\n=== ALL PROCESSES COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()