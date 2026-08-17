#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py - Standalone Configuration and Codebase Refactoring Tool
Propagates deck, model, card template, and field renaming substitutions
across all Anki Add-ons and External Mining/JS Scripts.
"""

import os
import sys
import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

CONFIG_FILE_NAME = "config.txt"


# ==============================================================================
# CONFIG LOADER
# ==============================================================================

def load_config_data(base_dir):
    """Loads configuration data from config.txt."""
    cfg_path = os.path.join(base_dir, CONFIG_FILE_NAME)
    if not os.path.exists(cfg_path):
        # Check current working directory as fallback
        cfg_path = os.path.join(os.getcwd(), CONFIG_FILE_NAME)

    if not os.path.exists(cfg_path):
        return None, cfg_path

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f), cfg_path
    except Exception as e:
        print(f"Error loading {cfg_path}: {e}")
        return None, cfg_path


# ==============================================================================
# SUBSTITUTION ENGINE
# ==============================================================================

class RefactorEngine:
    def __init__(self, config_data, anki_addons_dir, repo_dir, logger=print):
        self.cfg = config_data
        self.addons_dir = anki_addons_dir
        self.repo_dir = repo_dir
        self.log = logger
        
        self.decks = self.cfg.get("decks", {})
        self.models = self.cfg.get("models", {})
        self.templates = self.cfg.get("templates", {})
        self.m_fields = self.cfg.get("mining_fields", {})
        self.g_fields = self.cfg.get("grammar_fields", {})

    def get_val(self, group, key, default=None):
        if default is None:
            default = key
        return self.cfg.get(group, {}).get(key, default)

    def replace_in_file(self, file_path, replacer_callback):
        """Safely updates a file in place using a callback function."""
        if not os.path.exists(file_path):
            self.log(f"[SKIPPED - Not Found] {file_path}")
            return False

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            new_content = replacer_callback(content)

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.log(f"[UPDATED] {file_path}")
                return True
            else:
                self.log(f"[UNCHANGED] {file_path}")
                return False
        except Exception as e:
            self.log(f"[ERROR] Failed modifying {file_path}: {e}")
            return False

    def find_addon_file(self, addon_id, filename):
        """Locates an add-on file either inside a folder named addon_id or subfolders."""
        if not self.addons_dir or not os.path.exists(self.addons_dir):
            return None
        
        # Check direct folder
        direct_path = os.path.join(self.addons_dir, str(addon_id), filename)
        if os.path.exists(direct_path):
            return direct_path

        # Scan folder names containing the ID
        for root, dirs, files in os.walk(self.addons_dir):
            if os.path.basename(root) == str(addon_id) or str(addon_id) in os.path.basename(root):
                if filename in files:
                    return os.path.join(root, filename)
                # Check init alternative
                if filename == "__init__.py" and "init.py" in files:
                    return os.path.join(root, "init.py")

        return direct_path

    # ==========================================================================
    # FILE SPECIFIC REFACTORING RULES
    # ==========================================================================

    def refactor_addon_943429275(self):
        """Export to AI Bot (TSV) - Definitions"""
        fpath = self.find_addon_file("943429275", "__init__.py")
        sp = self.get_val("mining_fields", "SentencePlain")
        ced = self.get_val("mining_fields", "Correct English Definition")

        def transform(text):
            text = re.sub(r'headers\s*=\s*\["nid",\s*"[^"]+"\]', f'headers = ["nid", "{sp}"]', text)
            text = re.sub(r'if\s+"[^"]+"\s+not\s+in\s+note:', f'if "{sp}" not in note:', text)
            text = re.sub(r'sentence\s*=\s*note\["[^"]+"\]\.replace', f'sentence = note["{sp}"].replace', text)
            text = re.sub(r'contain the \'[^\']+\' field\.', f"contain the '{sp}' field.", text)
            text = re.sub(r'within the "[^"]+" column\.', f'within the "{sp}" column.', text)
            text = re.sub(r'nid\\t[^\n\r]+', f'nid\\t{ced}', text)
            text = re.sub(r'Example for "[^"]+":', f'Example for "{ced}":', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_1444428697(self):
        """Batch Link & Highlight"""
        fpath = self.find_addon_file("1444428697", "__init__.py")
        link_field = self.get_val("mining_fields", "Link to Related Cards")
        word_field = self.get_val("mining_fields", "Word")
        sp = self.get_val("mining_fields", "SentencePlain")
        sf = self.get_val("mining_fields", "SentenceFurigana")

        def transform(text):
            text = re.sub(r'TARGET_FIELD_LINK\s*=\s*"[^"]+"', f'TARGET_FIELD_LINK = "{link_field}"', text)
            text = re.sub(r'SOURCE_FIELD_LINK\s*=\s*"[^"]+"', f'SOURCE_FIELD_LINK = "{word_field}"', text)
            text = re.sub(r'FIELDS_TO_PROCESS\s*=\s*\["[^"]+",\s*"[^"]+"\]', f'FIELDS_TO_PROCESS = ["{sp}", "{sf}"]', text)
            text = re.sub(r'GROUP_CRITERION_FIELD\s*=\s*"[^"]+"', f'GROUP_CRITERION_FIELD = "{sp}"', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_207985417(self):
        """field_extract_inject_config.json"""
        fpath = self.find_addon_file("207985417", "field_extract_inject_config.json")
        if not os.path.exists(fpath):
            fpath = self.find_addon_file("207985417", "config.json")

        def transform(text):
            try:
                data = json.loads(text)
            except Exception:
                return text

            m_model = self.get_val("models", "miningsimple")
            g_model = self.get_val("models", "Grammar")

            # Update extraction profiles
            for prof_name, prof in data.get("profiles", {}).get("extraction", {}).items():
                if prof.get("model_name") in ["miningsimple", m_model]:
                    prof["model_name"] = m_model
                    if "selected_fields" in prof:
                        prof["selected_fields"] = [self.get_val("mining_fields", f, f) for f in prof["selected_fields"]]
                elif prof.get("model_name") in ["Grammar", g_model]:
                    prof["model_name"] = g_model
                    if "selected_fields" in prof:
                        prof["selected_fields"] = [self.get_val("grammar_fields", f, f) for f in prof["selected_fields"]]

            # Update injection profiles
            for prof_name, prof in data.get("profiles", {}).get("injection", {}).items():
                if prof.get("model_name") in ["miningsimple", m_model]:
                    prof["model_name"] = m_model
                    if "target_fields" in prof:
                        prof["target_fields"] = [self.get_val("mining_fields", f, f) for f in prof["target_fields"]]
                    if "field_mapping" in prof:
                        new_mapping = {}
                        for k, v in prof["field_mapping"].items():
                            nk = self.get_val("mining_fields", k, k)
                            nv = self.get_val("mining_fields", v, v)
                            new_mapping[nk] = nv
                        prof["field_mapping"] = new_mapping
                elif prof.get("model_name") in ["Grammar", g_model]:
                    prof["model_name"] = g_model
                    if "target_fields" in prof:
                        prof["target_fields"] = [self.get_val("grammar_fields", f, f) for f in prof["target_fields"]]
                    if "field_mapping" in prof:
                        new_mapping = {}
                        for k, v in prof["field_mapping"].items():
                            nk = self.get_val("grammar_fields", k, k)
                            nv = self.get_val("grammar_fields", v, v)
                            new_mapping[nk] = nv
                        prof["field_mapping"] = new_mapping

            return json.dumps(data, indent=4, ensure_ascii=False)

        self.replace_in_file(fpath, transform)

    def refactor_addon_984445827(self):
        """Grammar Mining and Linking & GrammarDataUpdate"""
        fpath = self.find_addon_file("984445827", "__init__.py")
        cfg_path = self.find_addon_file("984445827", "grammar_data_update_config.json")

        deck_m = self.get_val("decks", "mining")
        deck_g = self.get_val("decks", "grammar")
        model_m = self.get_val("models", "miningsimple")
        tmpl_pron = self.get_val("templates", "pronounciation").lower()
        
        nid_f = self.get_val("mining_fields", "Note ID")
        word_f = self.get_val("mining_fields", "Word")
        freq_f = self.get_val("mining_fields", "Frequency")
        
        mined_s = self.get_val("grammar_fields", "mined sentences")
        lvl_pt = self.get_val("grammar_fields", "Level And Grammar Point")

        def transform_init(text):
            text = re.sub(r'deck_name\s*=\s*"[^"]+"', f'deck_name = "{deck_m}"', text)
            text = re.sub(r'model_name\s*=\s*"[^"]+"', f'model_name = "{model_m}"', text)
            text = re.sub(r'if\s+"[^"]+"\s+not\s+in\s+headers:', f'if "{nid_f}" not in headers:', text)
            text = re.sub(r'row_data\["[^"]+"\]\s*==\s*"Note ID"', f'row_data["{nid_f}"] == "{nid_f}"', text)
            text = re.sub(r'row_data\["[^"]+"\]\s*==\s*"nidindiv"', f'row_data["{nid_f}"] == "nidindiv"', text)
            text = re.sub(r'nidindiv\s*=\s*row_data\["[^"]+"\]', f'nidindiv = row_data["{nid_f}"]', text)
            text = re.sub(r'"term_content":\s*row_data\.get\("[^"]+",\s*""\)', f'"term_content": row_data.get("{word_f}", "")', text)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+card\.template\(\)\[\'name\'\]\.lower\(\):', f'if "{tmpl_pron}" in card.template()[\'name\'].lower():', text)
            
            text = re.sub(r'if\s+"[^"]+"\s+not\s+in\s+g_fields\s+or\s+"[^"]+"\s+not\s+in\s+g_fields:', 
                          f'if "{mined_s}" not in g_fields or "{lvl_pt}" not in g_fields:', text)
            text = re.sub(r'g_fields\["[^"]+"\]', f'g_fields["{lvl_pt}"]', text, count=1)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+anki_fields:', f'if "{freq_f}" in anki_fields:', text)
            text = re.sub(r'anki_fields\["[^"]+"\]', f'anki_fields["{freq_f}"]', text)
            text = re.sub(r'current_mined_sentences\s*=\s*grammar_note\.fields\[g_fields\["[^"]+"\]\]', 
                          f'current_mined_sentences = grammar_note.fields[g_fields["{mined_s}"]]', text)
            text = re.sub(r'grammar_note\.fields\[g_fields\["[^"]+"\]\]\s*=\s*new_sentences_block', 
                          f'grammar_note.fields[g_fields["{mined_s}"]] = new_sentences_block', text)
            text = re.sub(r'grammar_note\.fields\[g_fields\["[^"]+"\]\]\s*=\s*f"\{new_sentences_block\}', 
                          f'grammar_note.fields[g_fields["{mined_s}"]] = f"{{new_sentences_block}}', text)
            return text

        self.replace_in_file(fpath, transform_init)

        def transform_cfg(text):
            return re.sub(r'deck:\w+', f'deck:{deck_g}', text)

        self.replace_in_file(cfg_path, transform_cfg)

    def refactor_addon_1383490780(self):
        """Sibling Sync Info"""
        fpath = self.find_addon_file("1383490780", "__init__.py")
        if not os.path.exists(fpath):
            fpath = self.find_addon_file("1383490780", "init.py")

        s_field = self.get_val("mining_fields", "SiblingSyncInfo")
        m_model = self.get_val("models", "miningsimple")

        def transform(text):
            text = re.sub(r'if\s+"[^"]+"\s+in\s+note:', f'if "{s_field}" in note:', text)
            text = re.sub(r'note\["[^"]+"\]\s*=\s*new_value', f'note["{s_field}"] = new_value', text)
            text = re.sub(r'note\["[^"]+"\]\s*!=\s*new_value', f'note["{s_field}"] != new_value', text)
            text = re.sub(r'find_notes\("note:[^"]+"\)', f'find_notes("note:{m_model}")', text)
            text = re.sub(r"No notes of type '[^']+' found\.", f"No notes of type '{m_model}' found.", text)
            text = re.sub(r"'[^']+' notes updated\.", f"'{m_model}' notes updated.", text)
            text = re.sub(r'QAction\("Sync all [^"]+ notes",\s*mw\)', f'QAction("Sync all {m_model} notes", mw)', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_630719015(self):
        """Relation Crawler"""
        fpath = self.find_addon_file("630719015", "__init__.py")
        if not os.path.exists(fpath):
            fpath = self.find_addon_file("630719015", "init.py")

        target_f = self.get_val("grammar_fields", "Connected Grammar Points from jlptsensei (optional)")
        source_l = self.get_val("grammar_fields", "Level And Grammar Point")
        deck_g = self.get_val("decks", "grammar")

        def transform(text):
            text = re.sub(r'TARGET_FIELD\s*=\s*"[^"]+"', f'TARGET_FIELD = "{target_f}"', text)
            text = re.sub(r'SOURCE_LABEL_FIELD\s*=\s*"[^"]+"', f'SOURCE_LABEL_FIELD = "{source_l}"', text)
            text = re.sub(r'query\s*=\s*f\'deck:\w+\s+"\{SOURCE_LABEL_FIELD\}', f"query = f'deck:{deck_g} \"{{SOURCE_LABEL_FIELD}}", text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_1389423810(self):
        """nplus1Scan"""
        fpath = self.find_addon_file("1389423810", "__init__.py")
        sf = self.get_val("mining_fields", "SoundFront")

        def transform(text):
            text = re.sub(r'note\["[^"]+"\]\.strip\(\)\s+if\s+"[^"]+"\s+in\s+note', f'note["{sf}"].strip() if "{sf}" in note', text)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+note\s+and\s+sound_counts\[note\["[^"]+"\]\.strip\(\)\]', 
                          f'if "{sf}" in note and sound_counts[note["{sf}"].strip()]', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_2051968993(self):
        """JPVocMarkExtension & Sentence Hover Preview"""
        fpath = self.find_addon_file("2051968993", "__init__.py")
        cfg_path = self.find_addon_file("2051968993", "jp_voc_mark_ext_config.json")

        deck_m = self.get_val("decks", "mining")
        tmpl_p = self.get_val("templates", "pronounciation").lower()
        model_m = self.get_val("models", "miningsimple")
        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")

        def transform_init(text):
            text = re.sub(r'query\s*=\s*f\'note:\w+\s+card:\{card_type_name\}\s+-is:suspended\s+\w+:"\{word\}"\'',
                          f'query = f\'note:{model_m} card:{{card_type_name}} -is:suspended {word_f}:"{{word}}"\'', text)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+note:\s*\n\s*sentence_text\s*=\s*note\["[^"]+"\]\.strip\(\)',
                          f'if "{sp_f}" in note:\n                sentence_text = note["{sp_f}"].strip()', text)
            return text

        self.replace_in_file(fpath, transform_init)

        def transform_cfg(text):
            return re.sub(r'"search_filter":\s*"deck:\w+\s+card:\w+"', f'"search_filter": "deck:{deck_m} card:{tmpl_p}"', text)

        self.replace_in_file(cfg_path, transform_cfg)

    def refactor_addon_880754415(self):
        """Export To AI BOT (TSV) (Translate)"""
        fpath = self.find_addon_file("880754415", "__init__.py")
        sp = self.get_val("mining_fields", "SentencePlain")
        t_field = self.get_val("mining_fields", "TranslationExampleSentence")

        def transform(text):
            text = re.sub(r'headers\s*=\s*\["nid",\s*"[^"]+"\]', f'headers = ["nid", "{sp}"]', text)
            text = re.sub(r'if\s+"[^"]+"\s+not\s+in\s+note:', f'if "{sp}" not in note:', text)
            text = re.sub(r'sentence\s*=\s*note\["[^"]+"\]\.replace', f'sentence = note["{sp}"].replace', text)
            text = re.sub(r'contain the \'[^\']+\' field\.', f"contain the '{sp}' field.", text)
            text = re.sub(r'column\s+[A-Za-z0-9_]+,', f'column {t_field},', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_addon_787429252(self):
        """Cross-Linker"""
        fpath = self.find_addon_file("787429252", "__init__.py")
        target_f = self.get_val("grammar_fields", "Connected Grammar Points from jlptsensei (optional)")
        source_l = self.get_val("grammar_fields", "Level And Grammar Point")

        def transform(text):
            text = re.sub(r'TARGET_FIELD\s*=\s*"[^"]+"', f'TARGET_FIELD = "{target_f}"', text)
            text = re.sub(r'SOURCE_LABEL_FIELD\s*=\s*"[^"]+"', f'SOURCE_LABEL_FIELD = "{source_l}"', text)
            return text

        self.replace_in_file(fpath, transform)

    def refactor_repo_python_scripts(self):
        """Refactors scripts in pythonscriptsNotInBrowseraddons and root scripts."""
        anime_script = os.path.join(self.repo_dir, "pythonscriptsNotInBrowseraddons", "Mining", "AnimeMining", 
                                    "AnimePictureAudioSubSync", "AudioScreenshotSubtitleAnkiAnime.py")
        ln_script = os.path.join(self.repo_dir, "pythonscriptsNotInBrowseraddons", "Mining", "LNAudiobookMining", 
                                 "LNAudioSubtitleSyncAnki", "AudioSubtitleSyncAnkiLightnovel.py")

        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")
        ced_f = self.get_val("mining_fields", "Correct English Definition")
        sf_f = self.get_val("mining_fields", "SoundFront")
        sb_f = self.get_val("mining_fields", "SoundBack")
        pic_f = self.get_val("mining_fields", "Picture")

        def transform_anime(text):
            text = re.sub(r'WORD_COLUMN_NAME\s*=\s*"[^"]+"', f'WORD_COLUMN_NAME = "{word_f}"', text)
            text = re.sub(r'SENTENCE_COLUMN_NAME\s*=\s*"[^"]+"', f'SENTENCE_COLUMN_NAME = "{sp_f}"', text)
            text = re.sub(r'DEFINITION_COLUMN_NAME\s*=\s*"[^"]+"', f'DEFINITION_COLUMN_NAME = "{ced_f}"', text)
            text = re.sub(r'AUDIO_FRONT_COLUMN\s*=\s*"[^"]+"', f'AUDIO_FRONT_COLUMN = "{sf_f}"', text)
            text = re.sub(r'AUDIO_BACK_COLUMN\s*=\s*"[^"]+"', f'AUDIO_BACK_COLUMN = "{sb_f}"', text)
            text = re.sub(r'IMAGE_COLUMN_NAME\s*=\s*"[^"]+"', f'IMAGE_COLUMN_NAME = "{pic_f}"', text)
            return text

        self.replace_in_file(anime_script, transform_anime)

        def transform_ln(text):
            text = re.sub(r'WORD_COLUMN_NAME\s*=\s*"[^"]+"', f'WORD_COLUMN_NAME = "{word_f}"', text)
            text = re.sub(r'SENTENCE_COLUMN_NAME\s*=\s*"[^"]+"', f'SENTENCE_COLUMN_NAME = "{sp_f}"', text)
            text = re.sub(r'DEFINITION_COLUMN_NAME\s*=\s*"[^"]+"', f'DEFINITION_COLUMN_NAME = "{ced_f}"', text)
            text = re.sub(r"'SoundFront'", f"'{sf_f}'", text)
            text = re.sub(r"'SoundBack'", f"'{sb_f}'", text)
            return text

        self.replace_in_file(ln_script, transform_ln)

    def refactor_browser_extensions(self):
        """Refactors browseraddons (grammaraddonregex, markierer_extension, etc.)."""
        # 1. prepare_data.py
        prep_py = os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "prepare_data.py")
        lvl_pt = self.get_val("grammar_fields", "Level And Grammar Point")
        link_f = self.get_val("grammar_fields", "Link")
        const_f = self.get_val("grammar_fields", "construction")
        ex_f = self.get_val("grammar_fields", "examplesentences")
        reg_f = self.get_val("grammar_fields", "regexpattern")

        def transform_prep(text):
            text = re.sub(r"row\.get\('Level And Grammar Point',\s*''\)", f"row.get('{lvl_pt}', '')", text)
            text = re.sub(r"row\.get\('Link',\s*''\)", f"row.get('{link_f}', '')", text)
            text = re.sub(r"row\.get\('construction',\s*''\)", f"row.get('{const_f}', '')", text)
            text = re.sub(r"row\.get\('examplesentences',\s*''\)", f"row.get('{ex_f}', '')", text)
            text = re.sub(r"row\.get\('regexpattern',\s*''\)", f"row.get('{reg_f}', '')", text)
            return text

        self.replace_in_file(prep_py, transform_prep)

        # 2. content.js
        content_js = os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "content.js")
        nid_f = self.get_val("mining_fields", "Note ID")
        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")
        edo_f = self.get_val("mining_fields", "English Definition Overview")
        freq_f = self.get_val("mining_fields", "Frequency")
        cjd_f = self.get_val("mining_fields", "Correct Japanese Definition")

        def transform_content_js(text):
            # Table headers
            th_pattern = r'<th>Note ID</th>\s*<th>Word</th>\s*<th>SentencePlain</th>\s*<th>English Definition Overview</th>\s*<th>Frequency</th>\s*<th>Correct Japanese Definition</th>'
            th_replace = f'<th>{nid_f}</th>\n        <th>{word_f}</th>\n        <th>{sp_f}</th>\n        <th>{edo_f}</th>\n        <th>{freq_f}</th>\n        <th>{cjd_f}</th>'
            text = re.sub(th_pattern, th_replace, text)

            # TSV Export Header Array
            tsv_header_pattern = r'\["Note ID",\s*"Word",\s*"SentencePlain",\s*"English Definition Overview",\s*"Frequency",\s*"Correct Japanese Definition"\]'
            tsv_header_replace = f'["{nid_f}", "{word_f}", "{sp_f}", "{edo_f}", "{freq_f}", "{cjd_f}"]'
            text = re.sub(tsv_header_pattern, tsv_header_replace, text)

            # Stats Table Header
            text = re.sub(r'<th>Grammar \("Level And Grammar Point"\)</th>', f'<th>Grammar ("{lvl_pt}")</th>', text)
            return text

        self.replace_in_file(content_js, transform_content_js)

        # 3. options.js
        options_js = os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "options.js")
        notes_f = self.get_val("grammar_fields", "Notes")

        def transform_options_js(text):
            text = re.sub(r"item\['Level And Grammar Point'\]", f"item['{lvl_pt}']", text)
            text = re.sub(r"g\['Notes'\]", f"g['{notes_f}']", text)
            text = re.sub(r"g\['Link'\]", f"g['{link_f}']", text)
            return text

        self.replace_in_file(options_js, transform_options_js)

    def run_all(self):
        """Executes all refactoring stages."""
        self.log("\n========================================================")
        self.log(" STARTING CODEBASE AND ADD-ONS REFACTORING")
        self.log("========================================================")

        self.log("\n--- Phase 1: Anki Add-ons ---")
        self.refactor_addon_943429275()
        self.refactor_addon_1444428697()
        self.refactor_addon_207985417()
        self.refactor_addon_984445827()
        self.refactor_addon_1383490780()
        self.refactor_addon_630719015()
        self.refactor_addon_1389423810()
        self.refactor_addon_2051968993()
        self.refactor_addon_880754415()
        self.refactor_addon_787429252()

        self.log("\n--- Phase 2: Python Scripts (Mining Pipelines) ---")
        self.refactor_repo_python_scripts()

        self.log("\n--- Phase 3: Browser Extensions (Grammar Regex & Highlighter) ---")
        self.refactor_browser_extensions()

        self.log("\n========================================================")
        self.log(" REFACTORING COMPLETED SUCCESSFULLY")
        self.log("========================================================\n")


# ==============================================================================
# TKINTER GUI LAUNCHER
# ==============================================================================

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Configuration Applier (config.py)")
        width = "750" if sys.platform == "win32" else "700"
        self.root.geometry(f"{width}x600")
        self.root.minsize(650, 520)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_data, self.cfg_path = load_config_data(self.base_dir)

        self.addons_dir_var = tk.StringVar()
        self.repo_dir_var = tk.StringVar()

        if self.config_data:
            paths = self.config_data.get("paths", {})
            self.addons_dir_var.set(paths.get("anki_addons_folder", ""))
            self.repo_dir_var.set(paths.get("repo_folder", self.base_dir))
        else:
            self.repo_dir_var.set(self.base_dir)

        self.build_ui()

    def build_ui(self):
        pad_opts = {'padx': 10, 'pady': 5}

        # Directory Pickers Frame
        frame_dirs = ttk.LabelFrame(self.root, text=" Target Directory Locations ")
        frame_dirs.pack(fill="x", **pad_opts)

        # Anki Addons Folder
        ttk.Label(frame_dirs, text="Anki Add-ons Folder (e.g. addons21):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        entry_addons = ttk.Entry(frame_dirs, textvariable=self.addons_dir_var, width=55)
        entry_addons.grid(row=0, column=1, padx=5, pady=4, sticky="we")
        btn_browse_addons = ttk.Button(frame_dirs, text="Browse...", command=self.browse_addons)
        btn_browse_addons.grid(row=0, column=2, padx=5, pady=4)

        # Repository Folder
        ttk.Label(frame_dirs, text="GitHub / Project Root Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        entry_repo = ttk.Entry(frame_dirs, textvariable=self.repo_dir_var, width=55)
        entry_repo.grid(row=1, column=1, padx=5, pady=4, sticky="we")
        btn_browse_repo = ttk.Button(frame_dirs, text="Browse...", command=self.browse_repo)
        btn_browse_repo.grid(row=1, column=2, padx=5, pady=4)

        frame_dirs.columnconfigure(1, weight=1)

        # Action Buttons Frame
        frame_act = ttk.Frame(self.root)
        frame_act.pack(fill="x", padx=10, pady=6)

        self.btn_run = ttk.Button(frame_act, text="Apply Substitutions & Update Codebase", command=self.execute_substitutions)
        self.btn_run.pack(side="left", padx=5)

        btn_reload = ttk.Button(frame_act, text="Reload config.txt", command=self.reload_config)
        btn_reload.pack(side="left", padx=5)

        # Log Output Box
        frame_log = ttk.LabelFrame(self.root, text=" Execution Output Log ")
        frame_log.pack(fill="both", expand=True, **pad_opts)

        self.log_box = tk.Text(frame_log, wrap="word", bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log_box.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_log, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        # Status Line
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        self.log_message(f"[LOADED] Active config file: {self.cfg_path}")
        if not self.config_data:
            self.log_message("[WARNING] config.txt was not found. Please create it or configure it via the Anki add-on.")

    def log_message(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def browse_addons(self):
        d = filedialog.askdirectory(title="Select Anki Addons Directory", initialdir=self.addons_dir_var.get() or os.path.expanduser("~"))
        if d:
            self.addons_dir_var.set(d)

    def browse_repo(self):
        d = filedialog.askdirectory(title="Select Project / GitHub Root Directory", initialdir=self.repo_dir_var.get() or self.base_dir)
        if d:
            self.repo_dir_var.set(d)

    def reload_config(self):
        self.config_data, self.cfg_path = load_config_data(self.base_dir)
        if self.config_data:
            self.log_message(f"[RELOADED] Configuration reloaded from {self.cfg_path}")
            messagebox.showinfo("Success", "Configuration successfully reloaded.")
        else:
            self.log_message(f"[ERROR] Could not load {self.cfg_path}")
            messagebox.showwarning("Warning", "Failed to reload config.txt.")

    def execute_substitutions(self):
        addons_dir = self.addons_dir_var.get().strip()
        repo_dir = self.repo_dir_var.get().strip()

        if not addons_dir or not os.path.exists(addons_dir):
            messagebox.showerror("Error", f"Anki add-ons directory does not exist:\n{addons_dir}")
            return

        if not repo_dir or not os.path.exists(repo_dir):
            messagebox.showerror("Error", f"Project repository directory does not exist:\n{repo_dir}")
            return

        if not self.config_data:
            self.reload_config()
            if not self.config_data:
                messagebox.showerror("Error", "No valid configuration found in config.txt.")
                return

        self.btn_run.config(state="disabled")
        self.status_var.set("Running refactoring operations...")

        try:
            engine = RefactorEngine(self.config_data, addons_dir, repo_dir, logger=self.log_message)
            engine.run_all()
            self.status_var.set("All files successfully updated.")
            messagebox.showinfo("Completed", "All substitutions have been successfully applied!")
        except Exception as e:
            self.log_message(f"[FATAL ERROR] {str(e)}")
            self.status_var.set("Execution stopped due to an error.")
            messagebox.showerror("Execution Error", f"An error occurred during execution:\n{str(e)}")
        finally:
            self.btn_run.config(state="normal")


def main():
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()