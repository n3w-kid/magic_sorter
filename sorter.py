import json
import os
import sys
import re
from xml.dom import minidom
from datetime import datetime

sys.setrecursionlimit(5000)

class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    ORANGE = "\033[38;5;208m"
    BG_BLUE = "\033[44m"
    BG_WHITE = "\033[47m"
    E_ROCKET = "🚀"
    E_FILE = "📄"
    E_SAVE = "💾"
    E_CHECK = "✅"
    E_CROSS = "❌"
    E_WARNING = "⚠"
    E_MAGIC = "✨"
    E_PASTE = "📋"
    E_FOLDER = "📂"
    E_STOP = "🛑"
    E_HEART = "❤"
    SEP = "-" * 80

def print_banner():
    print(f"\n{Style.CYAN}{Style.BOLD}{Style.SEP}{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}   {Style.E_ROCKET}  MAGIC ORGANIZER  {Style.E_ROCKET}   {Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}{Style.SEP}{Style.RESET}\n")
    print(f"{Style.GREEN}Welcome! I can beautify JSON, XML, or Text.{Style.RESET}")
    print(f"{Style.DIM}I will show you the result here first, then save it if you like.{Style.RESET}\n")

def get_input_mode():
    while True:
        print(f"{Style.YELLOW}[1]{Style.RESET} Provide File Path {Style.E_FILE}")
        print(f"{Style.YELLOW}[2]{Style.RESET} Copy-Paste Content {Style.E_PASTE}")
        print(f"{Style.YELLOW}[3]{Style.RESET} Localization Mode {Style.E_MAGIC}")
        choice = input(f"\n{Style.BOLD}✨ Choose option (1-3): {Style.RESET}").strip()
        if choice == '1': return 'file'
        elif choice == '2': return 'paste'
        elif choice == '3': return 'localize'
        else: print(f"{Style.RED}{Style.E_WARNING} Please choose 1, 2, or 3.{Style.RESET}\n")

def get_file_path():
    while True:
        path = input(f"\n{Style.BLUE}📂 Enter file path: {Style.RESET}").strip().strip('"').strip("'")
        if os.path.exists(path): return path
        print(f"{Style.RED}{Style.E_CROSS} File not found! Try again.{Style.RESET}")

def get_pasted_content():
    print(f"\n{Style.CYAN}📋 Paste your content below.{Style.RESET}")
    print(f"{Style.DIM}Type 'DONE' on a new line when finished.{Style.RESET}")
    print(f"{Style.SEP}\n")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'DONE': break
            lines.append(line)
        except EOFError: break
    return "\n".join(lines)

def detect_and_process(content):
    content = content.strip()
    if not content: return None, "Empty Content"
    
    file_size = len(content.encode('utf-8'))
    sort_keys = file_size < 500000 
    
    try:
        data = json.loads(content)
        formatted = json.dumps(data, indent=4, sort_keys=sort_keys, ensure_ascii=False)
        return colorize_json(formatted), "JSON"
    except: pass
    
    try:
        dom = minidom.parseString(content)
        formatted = dom.toprettyxml(indent="  ")
        formatted = '\n'.join([line for line in formatted.split('\n') if line.strip()])
        return colorize_xml(formatted), "XML"
    except: pass
    
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    lines.sort()
    return colorize_txt(lines), "Text (Sorted)"

def colorize_json(text):
    text = re.sub(r'(".*?")(\s*:)', f'{Style.BLUE}\\1{Style.RESET}\\2', text)
    text = re.sub(r'(:\s*)(".*?")', f'\\1{Style.GREEN}\\2{Style.RESET}', text)
    text = re.sub(r'(:\s*)(\d+)', f'\\1{Style.ORANGE}\\2{Style.RESET}', text)
    text = re.sub(r'(\s*)(true|false|null)', f'\\1{Style.MAGENTA}\\2{Style.RESET}', text)
    return text

def colorize_xml(text):
    text = re.sub(r'(<[^>]+>)', f'{Style.MAGENTA}\\1{Style.RESET}', text)
    return text

def colorize_txt(lines):
    colored = []
    for i, line in enumerate(lines, 1):
        colored.append(f"{Style.CYAN}{i:04d}{Style.RESET} | {Style.WHITE}{line}{Style.RESET}")
    return "\n".join(colored)

def add_separators(content):
    lines = content.split('\n')
    separated_content = f"\n{Style.SEP}\n".join(lines)
    return separated_content

def display_output(content, file_type):
    print(f"\n{Style.SEP}")
    print(f"{Style.BOLD}{Style.GREEN} {Style.E_MAGIC} PREVIEW: {file_type} Detected {Style.E_MAGIC} {Style.RESET}")
    print(f"{Style.SEP}\n")
    print(content)
    print(f"\n{Style.SEP}\n")

def save_to_pwd(content, file_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"organized_{file_type.lower()}_{timestamp}.txt"
    path = os.path.join(os.getcwd(), filename)
    try:
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        return True, path
    except Exception as e: return False, str(e)

def ask_to_save(content, file_type):
    while True:
        choice = input(f"{Style.BOLD}{Style.E_SAVE} Do you want to save this to the current folder? (y/n): {Style.RESET}").strip().lower()
        if choice in ['y', 'yes']:
            success, result = save_to_pwd(content, file_type)
            if success:
                print(f"\n{Style.GREEN}{Style.BOLD}{Style.E_CHECK} Saved successfully!{Style.RESET}")
                print(f"{Style.DIM}Location: {result}{Style.RESET}\n")
            else: print(f"\n{Style.RED}{Style.E_CROSS} Save failed: {result}{Style.RESET}\n")
            break
        elif choice in ['n', 'no']:
            print(f"\n{Style.YELLOW}{Style.E_STOP} No problem! File not saved.{Style.RESET}\n")
            break
        else: print(f"{Style.RED}Please type 'y' or 'n'.{Style.RESET}")

# --- 🌍 Localization Logic ---

def run_localization():
    print(f"\n{Style.YELLOW}{Style.BOLD}--- Localization Mode ---{Style.RESET}")
    path = get_file_path()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            outer_json = json.load(f)
    except Exception as e:
        print(f"{Style.RED}{Style.E_CROSS} Error loading JSON: {e}{Style.RESET}")
        return

    if "m_Script" not in outer_json:
        print(f"{Style.RED}{Style.E_CROSS} Not a valid Unity Ink JSON file.{Style.RESET}")
        return

    try:
        inner_json = json.loads(outer_json["m_Script"])
    except Exception as e:
        print(f"{Style.RED}{Style.E_CROSS} Error parsing inner script: {e}{Style.RESET}")
        return

    extracted = []
    def extract_text(obj):
        if isinstance(obj, list):
            for item in obj: extract_text(item)
        elif isinstance(obj, dict):
            for val in obj.values(): extract_text(val)
        elif isinstance(obj, str) and obj.startswith("^"):
            extracted.append(obj[1:].strip())
    
    extract_text(inner_json)
    
    if not extracted:
        print(f"{Style.YELLOW}No translatable strings found.{Style.RESET}")
        return

    out_file = "extracted_strings.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)
    print(f"\n{Style.GREEN}{Style.E_CHECK} Extracted {len(extracted)} strings to: {out_file}{Style.RESET}")
    print(f"{Style.DIM}Translate this file, save as 'translated_strings.json' in same folder.{Style.RESET}")

    trans_file = "translated_strings.json"
    if not os.path.exists(trans_file):
        print(f"{Style.YELLOW}Waiting for translated file... Press Enter when ready.{Style.RESET}")
        input()
        
    try:
        with open(trans_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
    except Exception as e:
        print(f"{Style.RED}{Style.E_CROSS} Error loading translations: {e}{Style.RESET}")
        return

    if len(translations) != len(extracted):
        print(f"{Style.RED}{Style.E_WARNING} Translation count mismatch!{Style.RESET}")
        return

    idx = 0
    def insert_text(obj):
        nonlocal idx
        if isinstance(obj, list):
            for i in range(len(obj)):
                if isinstance(obj[i], str) and obj[i].startswith("^"):
                    if idx < len(translations):
                        obj[i] = "^" + translations[idx].strip()
                    idx += 1
                elif isinstance(obj[i], (dict, list)):
                    insert_text(obj[i])
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("^"):
                    if idx < len(translations):
                        obj[k] = "^" + translations[idx].strip()
                    idx += 1
                elif isinstance(v, (dict, list)):
                    insert_text(v)

    insert_text(inner_json)
    outer_json["m_Script"] = json.dumps(inner_json, ensure_ascii=False, indent=2)
    
    final_path = path.replace(".json", "_localized.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(outer_json, f, indent=2, ensure_ascii=False)
        
    print(f"\n{Style.GREEN}{Style.BOLD}{Style.E_CHECK} Localization complete!{Style.RESET}")
    print(f"{Style.DIM}Saved to: {final_path}{Style.RESET}\n")

# --- 🏁 Main Program ---

def main():
    if os.name == 'nt': os.system('') 
    print_banner()
    
    try:
        mode = get_input_mode()
        
        if mode == 'localize':
            run_localization()
            print(f"{Style.E_HEART} Thank you for using Magic Organizer! {Style.E_HEART}\n")
            return

        content = ""
        if mode == 'file':
            path = get_file_path()
            try:
                with open(path, "r", encoding="utf-8") as f: content = f.read()
            except Exception as e:
                print(f"{Style.RED}{Style.E_CROSS} Error reading file: {e}{Style.RESET}")
                return
        else: content = get_pasted_content()
            
        if not content.strip():
            print(f"{Style.RED}{Style.E_WARNING} No content provided. Exiting.{Style.RESET}")
            return

        print(f"\n{Style.CYAN}⚙  Processing...{Style.RESET}")
        processed_content, file_type = detect_and_process(content)
        
        if not processed_content:
            print(f"{Style.RED}{Style.E_CROSS} Could not parse content.{Style.RESET}")
            return

        final_output = add_separators(processed_content)
        header = f"{Style.DIM}# Organized by Magic Organizer | Type: {file_type} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}{Style.RESET}"
        final_output = header + "\n" + final_output

        display_output(final_output, file_type)
        ask_to_save(final_output, file_type)
        
        print(f"{Style.E_HEART} Thank you for using Magic Organizer! {Style.E_HEART}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Style.RED}{Style.E_STOP} Program interrupted by user.{Style.RESET}\n")
    except Exception as e:
        print(f"\n{Style.RED}{Style.E_CROSS} Unexpected Error: {e}{Style.RESET}\n")

if __name__ == "__main__":
    main()
