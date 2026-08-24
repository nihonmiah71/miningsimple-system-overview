#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py - Standalone Configuration and Codebase Refactoring Tool
Propagates deck, model, card template, and field renaming substitutions
across all Anki Add-ons and External Mining/JS Scripts.
Supports custom renaming as well as 1-click restoration to default names.
"""

import os
import sys
import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

CONFIG_FILE_NAME = "config.txt"

# Canonical system default names
DEFAULT_CONFIG = {
    "decks": {
        "mining": "Mining",
        "grammar": "Grammar"
    },
    "models": {
        "miningsimple": "miningsimple",
        "Grammar": "Grammar"
    },
    "templates": {
        "pronounciation": "Pronounciation"
    },
    "mining_fields": {
        "Word": "Word",
        "SentencePlain": "SentencePlain",
        "SentenceFurigana": "SentenceFurigana",
        "Correct English Definition": "Correct English Definition",
        "Correct Japanese Definition": "Correct Japanese Definition",
        "English Definition Overview": "English Definition Overview",
        "Frequency": "Frequency",
        "SoundFront": "SoundFront",
        "SoundBack": "SoundBack",
        "Picture": "Picture",
        "Note ID": "Note ID",
        "Link to Related Cards": "Link to Related Cards",
        "TranslationExampleSentence": "TranslationExampleSentence",
        "SiblingSyncInfo": "SiblingSyncInfo"
    },
    "grammar_fields": {
        "Level And Grammar Point": "Level And Grammar Point",
        "Link": "Link",
        "Connected Grammar Points from jlptsensei (optional)": "Connected Grammar Points from jlptsensei (optional)",
        "Notes": "Notes",
        "construction": "construction",
        "examplesentences": "examplesentences",
        "regexpattern": "regexpattern",
        "mined sentences": "mined sentences",
        "title audio": "title audio",
        "construction audio": "construction audio",
        "examplesentences audio": "examplesentences audio"
    }
}


# ==============================================================================
# CONFIG LOADER
# ==============================================================================

def load_config_data(base_dir):
    """Loads configuration data from config.txt."""
    cfg_path = os.path.join(base_dir, CONFIG_FILE_NAME)
    if not os.path.exists(cfg_path):
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
    def __init__(self, config_data, anki_addons_dir, repo_dir, is_restore=False, logger=print):
        self.cfg = config_data
        self.addons_dir = anki_addons_dir
        self.repo_dir = repo_dir
        self.is_restore = is_restore
        self.log = logger
        
        self.decks = self.cfg.get("decks", {})
        self.models = self.cfg.get("models", {})
        self.templates = self.cfg.get("templates", {})
        self.m_fields = self.cfg.get("mining_fields", {})
        self.g_fields = self.cfg.get("grammar_fields", {})

    def get_val(self, group, key, default=None):
        if default is None:
            default = DEFAULT_CONFIG.get(group, {}).get(key, key)
        return self.cfg.get(group, {}).get(key, default)

    def replace_in_file(self, file_path, replacer_callback):
        """Safely updates a file in place using a callback function."""
        if not file_path or not os.path.exists(file_path):
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
        
        direct_path = os.path.join(self.addons_dir, str(addon_id), filename)
        if os.path.exists(direct_path):
            return direct_path

        for root, dirs, files in os.walk(self.addons_dir):
            if os.path.basename(root) == str(addon_id) or str(addon_id) in os.path.basename(root):
                if filename in files:
                    return os.path.join(root, filename)
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
        """field_extract_inject_config.json (Extraction / Injection Addon)"""
        fpath = self.find_addon_file("207985417", "field_extract_inject_config.json")
        if not os.path.exists(fpath):
            fpath = self.find_addon_file("207985417", "config.json")

        m_model = self.get_val("models", "miningsimple")
        g_model = self.get_val("models", "Grammar")

        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")
        ced_f = self.get_val("mining_fields", "Correct English Definition")
        cjd_f = self.get_val("mining_fields", "Correct Japanese Definition")
        sf_f = self.get_val("mining_fields", "SoundFront")
        sb_f = self.get_val("mining_fields", "SoundBack")
        pic_f = self.get_val("mining_fields", "Picture")
        freq_f = self.get_val("mining_fields", "Frequency")
        trans_f = self.get_val("mining_fields", "TranslationExampleSentence")

        lvl_pt = self.get_val("grammar_fields", "Level And Grammar Point")
        link_f = self.get_val("grammar_fields", "Link")
        conn_g = self.get_val("grammar_fields", "Connected Grammar Points from jlptsensei (optional)")
        notes_f = self.get_val("grammar_fields", "Notes")
        const_f = self.get_val("grammar_fields", "construction")
        ex_f = self.get_val("grammar_fields", "examplesentences")
        t_aud = self.get_val("grammar_fields", "title audio")
        c_aud = self.get_val("grammar_fields", "construction audio")
        e_aud = self.get_val("grammar_fields", "examplesentences audio")
        reg_f = self.get_val("grammar_fields", "regexpattern")

        grammar_data_path = ""
        add_voc_path = ""
        if self.repo_dir and not self.is_restore:
            grammar_data_path = os.path.normpath(
                os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "simplegrammarregex_fixed.tsv")
            ).replace("\\", "/")
            add_voc_path = os.path.normpath(
                os.path.join(self.repo_dir, "browseraddons", "markierer_extension", "extracted_fields1.tsv")
            ).replace("\\", "/")

        def transform(text):
            try:
                data = json.loads(text)
            except Exception:
                return text

            # 1. Extraction Profiles
            ext_profiles = data.get("profiles", {}).get("extraction", {})
            for prof_name, prof in ext_profiles.items():
                if prof_name == "AddNewVocToList":
                    prof["model_name"] = m_model
                    prof["selected_fields"] = [word_f]
                    prof["fixed_file_path"] = add_voc_path

                elif prof_name == "GrammarDataUpdate":
                    prof["model_name"] = g_model
                    prof["selected_fields"] = [
                        lvl_pt, link_f, conn_g, notes_f,
                        const_f, ex_f, t_aud, c_aud, e_aud, reg_f
                    ]
                    prof["fixed_file_path"] = grammar_data_path

                elif prof_name in ["AnimePictureAudioSubSync", "LNAudioSubSync", "LNAudioSubSyncManualSelect", "AnimePictureAudioSubSyncManualSelect"]:
                    prof["model_name"] = m_model
                    prof["selected_fields"] = [word_f, sp_f, ced_f]

            # 2. Injection Profiles
            inj_profiles = data.get("profiles", {}).get("injection", {})
            for prof_name, prof in inj_profiles.items():
                if prof_name in ["CorrectDefinitionImport", "CorrectDefinitionImportManualSelect"]:
                    prof["model_name"] = m_model
                    prof["target_fields"] = [ced_f, cjd_f]
                    prof["field_mapping"] = {ced_f: ced_f, cjd_f: cjd_f}

                elif prof_name == "TagUpdateImport":
                    prof["model_name"] = g_model
                    prof["target_fields"] = [notes_f]
                    prof["field_mapping"] = {notes_f: notes_f}

                elif prof_name == "LNAudioSubSync":
                    prof["model_name"] = m_model
                    prof["target_fields"] = [sf_f, sb_f]
                    prof["field_mapping"] = {sf_f: sf_f, sb_f: sb_f}

                elif prof_name == "AnimePictureAudioSubSync":
                    prof["model_name"] = m_model
                    prof["target_fields"] = [sf_f, sb_f, pic_f]
                    prof["field_mapping"] = {sf_f: sf_f, sb_f: sb_f, pic_f: pic_f}

                elif prof_name in ["BatchTranslate", "BatchTranslateManualSelect"]:
                    prof["model_name"] = m_model
                    prof["target_fields"] = [trans_f]
                    prof["field_mapping"] = {trans_f: trans_f}

                elif prof_name == "LNAudioSubSyncManualSelect":
                    prof["model_name"] = m_model
                    prof["target_fields"] = [freq_f]
                    prof["field_mapping"] = {freq_f: freq_f}

                elif prof_name == "AnimePictureAudioSubSyncManualSelect":
                    prof["model_name"] = m_model
                    prof["target_fields"] = [word_f]
                    prof["field_mapping"] = {word_f: word_f}

            return json.dumps(data, indent=4, ensure_ascii=False)

        self.replace_in_file(fpath, transform)

    def refactor_addon_1552719434(self):
        """NoteEnhancer - Sentence Hover Preview & Browser Search"""
        fpath = self.find_addon_file("1552719434", "__init__.py")
        if not os.path.exists(fpath):
            fpath = self.find_addon_file("1552719434", "init.py")

        model_m = self.get_val("models", "miningsimple")
        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")

        def transform(text):
            query_pattern = r"query\s*=\s*f['\"]note:[^\s]+\s+card:\{card_type_name\}\s+-is:suspended\s+[^\s:]+:\"\{word\}\"['\"]"
            query_replacement = f"query = f'note:{model_m} card:{{card_type_name}} -is:suspended {word_f}:\"{{word}}\"'"
            text = re.sub(query_pattern, query_replacement, text)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+note:', f'if "{sp_f}" in note:', text)
            text = re.sub(r'note\["[^"]+"\]\.strip\(\)', f'note["{sp_f}"].strip()', text)
            return text

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
            text = re.sub(r'row_data\["[^"]+"\]\s*==\s*"[^"]+"', f'row_data["{nid_f}"] == "{nid_f}"', text)
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

        prep_script_path = os.path.normpath(
            os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "prepare_data.py")
        ).replace("\\", "/") if (self.repo_dir and not self.is_restore) else ""

        def transform_cfg(text):
            try:
                data = json.loads(text)
                if "search_filter" in data:
                    data["search_filter"] = re.sub(r'deck:(?:"[^"]+"|\S+)', f'deck:{deck_g}', data["search_filter"])
                data["script_path"] = prep_script_path
                return json.dumps(data, indent=4, ensure_ascii=False)
            except Exception:
                text = re.sub(r'deck:\w+', f'deck:{deck_g}', text)
                return text

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
            text = re.sub(r'query\s*=\s*f\'deck:[^\s\']+\s+"\{SOURCE_LABEL_FIELD\}', f"query = f'deck:{deck_g} \"{{SOURCE_LABEL_FIELD}}", text)
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
                          f'query = f\'note:{model_m} card:{{card_type_name}} -is:suspended {word_f}:\"{{word}}\"\'', text)
            text = re.sub(r'if\s+"[^"]+"\s+in\s+note:\s*\n\s*sentence_text\s*=\s*note\["[^"]+"\]\.strip\(\)',
                          f'if "{sp_f}" in note:\n                sentence_text = note["{sp_f}"].strip()', text)
            return text

        self.replace_in_file(fpath, transform_init)

        voc_script_path = os.path.normpath(
            os.path.join(self.repo_dir, "browseraddons", "markierer_extension", "vocappend.py")
        ).replace("\\", "/") if (self.repo_dir and not self.is_restore) else ""

        def transform_cfg(text):
            try:
                data = json.loads(text)
                if "search_filter" in data:
                    sf = data["search_filter"]
                    sf = re.sub(r'deck:(?:"[^"]+"|\S+)', f'deck:{deck_m}', sf)
                    sf = re.sub(r'card:(?:"[^"]+"|\S+)', f'card:{tmpl_p}', sf)
                    data["search_filter"] = sf
                data["script_path"] = voc_script_path
                return json.dumps(data, indent=4, ensure_ascii=False)
            except Exception:
                text = re.sub(r'deck:\w+', f'deck:{deck_m}', text)
                text = re.sub(r'card:\w+', f'card:{tmpl_p}', text)
                return text

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
            text = re.sub(r"AUDIO_FRONT_COLUMN\s*=\s*'[^']+'", f"AUDIO_FRONT_COLUMN = '{sf_f}'", text)
            text = re.sub(r"AUDIO_BACK_COLUMN\s*=\s*'[^']+'", f"AUDIO_BACK_COLUMN = '{sb_f}'", text)
            return text

        self.replace_in_file(ln_script, transform_ln)

    def refactor_browser_extensions(self):
        """
        Refactors browseraddons safely.
        Updates TSV ingestion in prepare_data.py and TSV export headers in content.js.
        Internal JS rendering properties (options.js / content.js) remain completely untouched.
        """
        # 1. prepare_data.py - Dynamic TSV column mapping
        prep_py = os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "prepare_data.py")
        lvl_pt = self.get_val("grammar_fields", "Level And Grammar Point")
        link_f = self.get_val("grammar_fields", "Link")
        const_f = self.get_val("grammar_fields", "construction")
        ex_f = self.get_val("grammar_fields", "examplesentences")
        reg_f = self.get_val("grammar_fields", "regexpattern")
        notes_f = self.get_val("grammar_fields", "Notes")

        def transform_prep(text):
            text = re.sub(r'"level_and_point":\s*row\.get\([^)]+\)', f'"level_and_point": row.get(\'{lvl_pt}\', \'\')', text)
            text = re.sub(r'"link":\s*row\.get\([^)]+\)', f'"link": row.get(\'{link_f}\', \'\')', text)
            text = re.sub(r'"construction":\s*row\.get\([^)]+\)', f'"construction": row.get(\'{const_f}\', \'\')', text)
            text = re.sub(r'"examplesentences":\s*row\.get\([^)]+\)', f'"examplesentences": row.get(\'{ex_f}\', \'\')', text)
            text = re.sub(r'"regexpattern":\s*row\.get\([^)]+\)', f'"regexpattern": row.get(\'{reg_f}\', \'\')', text)
            text = re.sub(r'"notes":\s*row\.get\([^)]+\)', f'"notes": row.get(\'{notes_f}\', \'\')', text)
            return text

        self.replace_in_file(prep_py, transform_prep)

        # 2. content.js - Mining Table UI and TSV Export Headers
        content_js = os.path.join(self.repo_dir, "browseraddons", "grammaraddonregex", "content.js")
        nid_f = self.get_val("mining_fields", "Note ID")
        word_f = self.get_val("mining_fields", "Word")
        sp_f = self.get_val("mining_fields", "SentencePlain")
        edo_f = self.get_val("mining_fields", "English Definition Overview")
        freq_f = self.get_val("mining_fields", "Frequency")
        cjd_f = self.get_val("mining_fields", "Correct Japanese Definition")

        def transform_content_js(text):
            # Mining Table Header HTML
            th_pattern = r'<th>[^<]+</th>\s*<th>[^<]+</th>\s*<th>[^<]+</th>\s*<th>[^<]+</th>\s*<th>[^<]+</th>\s*<th>[^<]+</th>'
            th_replace = f'<th>{nid_f}</th>\n        <th>{word_f}</th>\n        <th>{sp_f}</th>\n        <th>{edo_f}</th>\n        <th>{freq_f}</th>\n        <th>{cjd_f}</th>'
            text = re.sub(th_pattern, th_replace, text, count=1)

            # TSV Export Output Header Array
            tsv_header_pattern = r'outputText\s*=\s*\["[^"]+",\s*"[^"]+",\s*"[^"]+",\s*"[^"]+",\s*"[^"]+",\s*"[^"]+"\]'
            tsv_header_replace = f'outputText = ["{nid_f}", "{word_f}", "{sp_f}", "{edo_f}", "{freq_f}", "{cjd_f}"]'
            text = re.sub(tsv_header_pattern, tsv_header_replace, text, count=1)
            return text

        self.replace_in_file(content_js, transform_content_js)

    def run_all(self):
        """Executes all refactoring stages."""
        self.log("\n========================================================")
        self.log(" STARTING CODEBASE AND ADD-ONS REFACTORING")
        self.log("========================================================")

        self.log("\n--- Phase 1: Anki Add-ons ---")
        self.refactor_addon_1552719434()
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

        self.log("\n--- Phase 3: Browser Extensions (Grammar Regex & Ingestion) ---")
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
        self.root.geometry(f"{width}x640")
        self.root.minsize(650, 540)

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

        self.btn_run = ttk.Button(frame_act, text="Apply Substitutions (From config.txt)", command=self.execute_substitutions)
        self.btn_run.pack(side="left", padx=5)

        self.btn_restore = ttk.Button(frame_act, text="Restore Default Names Across Codebase", command=self.restore_defaults)
        self.btn_restore.pack(side="left", padx=5)

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
        self.btn_restore.config(state="disabled")
        self.status_var.set("Running refactoring operations...")

        try:
            engine = RefactorEngine(self.config_data, addons_dir, repo_dir, is_restore=False, logger=self.log_message)
            engine.run_all()
            self.status_var.set("All files successfully updated.")
            messagebox.showinfo("Completed", "All substitutions have been successfully applied!")
        except Exception as e:
            self.log_message(f"[FATAL ERROR] {str(e)}")
            self.status_var.set("Execution stopped due to an error.")
            messagebox.showerror("Execution Error", f"An error occurred during execution:\n{str(e)}")
        finally:
            self.btn_run.config(state="normal")
            self.btn_restore.config(state="normal")

    def restore_defaults(self):
        """Restores the codebase back to standard default names and resets dynamic paths to empty."""
        addons_dir = self.addons_dir_var.get().strip()
        repo_dir = self.repo_dir_var.get().strip()

        if not addons_dir or not os.path.exists(addons_dir):
            messagebox.showerror("Error", f"Anki add-ons directory does not exist:\n{addons_dir}")
            return

        if not repo_dir or not os.path.exists(repo_dir):
            messagebox.showerror("Error", f"Project repository directory does not exist:\n{repo_dir}")
            return

        confirm = messagebox.askyesno(
            "Confirm Reset to Defaults",
            "Are you sure you want to reset all add-ons, mining scripts, and browser extensions "
            "back to their original default names?\n\n"
            "This will reset all custom substitutions and clear dynamic file paths to empty."
        )
        if not confirm:
            return

        self.btn_run.config(state="disabled")
        self.btn_restore.config(state="disabled")
        self.status_var.set("Restoring factory default names...")

        try:
            self.log_message("\n--- RESTORING CANONICAL DEFAULT NAMES ACROSS CODEBASE ---")
            engine = RefactorEngine(DEFAULT_CONFIG, addons_dir, repo_dir, is_restore=True, logger=self.log_message)
            engine.run_all()
            self.status_var.set("Codebase successfully restored to default names.")
            messagebox.showinfo("Defaults Restored", "All files have been restored to their standard default names!")
        except Exception as e:
            self.log_message(f"[FATAL ERROR] {str(e)}")
            self.status_var.set("Restoration failed.")
            messagebox.showerror("Error", f"An error occurred during restoration:\n{str(e)}")
        finally:
            self.btn_run.config(state="normal")
            self.btn_restore.config(state="normal")


def main():
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
