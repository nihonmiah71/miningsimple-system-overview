import os
import re
import json
import pandas as pd

# Define subfolder
DATA_DIR = "data"
TSV_FILE = "simplegrammarregex_fixed.tsv"

# Update paths to the subfolder
OUT_GRAMMAR = os.path.join(DATA_DIR, "grammar_data.json")
OUT_PATTERNS = os.path.join(DATA_DIR, "patterns_data.json")

def expand_regex_options(pattern_str):
    """
    Resolves complex, deeply nested regex options like (?:A|B) or (A|B)
    step-by-step from inside to outside into individual plain-text combinations.
    """
    if not pattern_str or pd.isna(pattern_str):
        return []
        
    pattern_str = str(pattern_str).strip()
    
    def replace_char_class(match):
        chars = match.group(1)
        # Prevents splitting predefined regex classes like \s
        if chars.startswith('\\'):
            return match.group(0)
        return '(?:' + '|'.join(list(chars)) + ')'
    
    if '[' in pattern_str and '^' not in pattern_str:
        pattern_str = re.sub(r'\[([^\]]+)\]', replace_char_class, pattern_str)

    def expand_step(text):
        match = re.search(r'\(\?(?::)?([^()]*)\)(\?)?|\(([^()]*)\)(\?)?', text)
        if not match:
            if '|' in text:
                return [opt.strip() for opt in text.split('|') if opt.strip()]
            return [text]
        
        start, end = match.span()
        if match.group(1) is not None:
            inner_content = match.group(1)
            is_optional = match.group(2) == '?'
        else:
            inner_content = match.group(3)
            is_optional = match.group(4) == '?'
            
        alternatives = [opt.strip() for opt in inner_content.split('|') if opt.strip()]
        if is_optional:
            alternatives.append("")
            
        results = []
        prefix = text[:start]
        suffix = text[end:]
        
        for alt in alternatives:
            combined = prefix + alt + suffix
            results.extend(expand_step(combined))
            
        return results

    expanded_patterns = expand_step(pattern_str)
    
    unique_patterns = []
    for p in expanded_patterns:
        p_cleaned = p.strip()
        if p_cleaned and p_cleaned not in unique_patterns:
            unique_patterns.append(p_cleaned)
            
    return unique_patterns

def calculate_max_length_score(pattern_str):
    """
    Calculates the maximum potential match length of a flat pattern.
    """
    score = 0
    temp_str = pattern_str
    quantifiers = re.findall(r'\{\d+,(\d+)\}', temp_str)
    for q in quantifiers:
        score += int(q)
    temp_str = re.sub(r'\{\d+,\d+\}', '', temp_str)
    temp_str = re.sub(r'\[[^\]]+\]', '', temp_str)
    temp_str = re.sub(r'[\(\)\?\+\*^$]', '', temp_str)
    score += len(temp_str)
    return score

def main():
    # Ensure the data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(TSV_FILE):
        print(f"Error: {TSV_FILE} was not found in the current directory!")
        return

    print("Reading original TSV file...")
    df = pd.read_csv(TSV_FILE, sep='\t', encoding='utf-8-sig').fillna('')
    
    grammar_dict = {}
    pattern_to_nids = {}
    
    for _, row in df.iterrows():
        nid = str(row['nid']).strip()
        if not nid or nid == 'nan':
            continue
            
        # Keep original entry in grammar_dict under its original NID
        grammar_dict[nid] = {
            "nid": nid,
            "tags": row.get('tags', ''),
            "level_and_point": row.get('Level And Grammar Point', ''),
            "link": row.get('Link', ''),
            "construction": row.get('construction', ''),
            "examplesentences": row.get('examplesentences', ''),
            "regexpattern": row.get('regexpattern', '')
        }
        
        raw_regex = row.get('regexpattern', '')
        flat_patterns = expand_regex_options(raw_regex)
        tags_str = str(row.get('tags', ''))
        
        for pat in flat_patterns:
            if pat not in pattern_to_nids:
                pattern_to_nids[pat] = set()
            
            # Always add the original NID
            pattern_to_nids[pat].add(nid)
            
            # If the row matches specific expression tags, also add the corresponding master NID
            if "ことexpressions" in tags_str:
                pattern_to_nids[pat].add("1782137079844")
            elif "ところexpressions" in tags_str:
                pattern_to_nids[pat].add("1782103290741")
            elif "ものexpressions" in tags_str:
                pattern_to_nids[pat].add("1782136857308")
            elif "上expressions" in tags_str:
                pattern_to_nids[pat].add("1775895481191")
            elif "そうexpressions" in tags_str:
                pattern_to_nids[pat].add("1775895481586")
            elif "限り" in tags_str:
                pattern_to_nids[pat].update([
                    "1775895481203",
                    "1775895481204",
                    "1785181057952"
                ])
            
    processed_patterns = []
    for pat, nids in pattern_to_nids.items():
        score = calculate_max_length_score(pat)
        processed_patterns.append({
            "pattern": pat,
            "length_score": score,
            "nids": list(nids)
        })
        
    processed_patterns.sort(key=lambda x: x['length_score'], reverse=True)
    
    # Export to the data folder
    with open(OUT_GRAMMAR, 'w', encoding='utf-8') as f:
        json.dump(grammar_dict, f, ensure_ascii=False, indent=2)
        
    with open(OUT_PATTERNS, 'w', encoding='utf-8') as f:
        json.dump(processed_patterns, f, ensure_ascii=False, indent=2)
        
    print("\n--- Preparation completed successfully! ---")
    print(f"-> {OUT_GRAMMAR} created")
    print(f"-> {OUT_PATTERNS} created")

if __name__ == "__main__":
    main()