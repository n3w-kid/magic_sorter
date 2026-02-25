import json
import os
import sys
import re
from xml.dom import minidom
from datetime import datetime

# --- 🎨 Color & Emoji Configuration ---
class Style:
    # ANSI Colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    
    # Foreground Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    ORANGE = "\033[38;5;208m"
    
    # Background
    BG_BLUE = "\033[44m"
    BG_WHITE = "\033[47m"

    # Emojis
    E_ROCKET = "🚀"
    E_FILE = "📄"
    E_SAVE = "💾"
    E_CHECK = "✅"
    E_CROSS = "❌"
    E_WARNING = "⚠️"
    E_MAGIC = "✨"
    E_PASTE = "📋"
    E_FOLDER = "📂"
    E_STOP = "🛑"
    E_HEART = "❤️"

    # Separators
    SEP = "-" * 80

# --- 🧠 Logic Functions ---

def print_banner():
    """Prints a colorful welcome banner."""
    print(f"\n{Style.CYAN}{Style.BOLD}{Style.SEP}{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}   {Style.E_ROCKET}  MAGIC ORGANIZER  {Style.E_ROCKET}   {Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}{Style.SEP}{Style.RESET}\n")
    print(f"{Style.GREEN}Welcome! I can beautify JSON, XML, or Text.{Style.RESET}")
    print(f"{Style.DIM}I will show you the result here first, then save it if you like.{Style.RESET}\n")

def get_input_mode():
    """Asks user how they want to provide data."""
    while True:
        print(f"{Style.YELLOW}[1]{Style.RESET} Provide File Path {Style.E_FILE}")
        print(f"{Style.YELLOW}[2]{Style.RESET} Copy-Paste Content {Style.E_PASTE}")
        choice = input(f"\n{Style.BOLD}✨ Choose option (1 or 2): {Style.RESET}").strip()
        if choice == '1':
            return 'file'
        elif choice == '2':
            return 'paste'
        else:
            print(f"{Style.RED}{Style.E_WARNING} Please choose 1 or 2.{Style.RESET}\n")

def get_file_path():
    """Gets and validates file path."""
    while True:
        path = input(f"\n{Style.BLUE}📂 Enter file path: {Style.RESET}").strip().strip('"').strip("'")
        if os.path.exists(path):
            return path
        print(f"{Style.RED}{Style.E_CROSS} File not found! Try again.{Style.RESET}")

def get_pasted_content():
    """Gets multi-line content from user."""
    print(f"\n{Style.CYAN}📋 Paste your content below.{Style.RESET}")
    print(f"{Style.DIM}Type 'DONE' on a new line when finished.{Style.RESET}")
    print(f"{Style.SEP}\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'DONE':
                break
            lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines)

def detect_and_process(content):
    """Detects format and processes content."""
    content = content.strip()
    if not content:
        return None, "Empty Content"
    
    # Try JSON
    try:
        data = json.loads(content)
        formatted = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)
        return colorize_json(formatted), "JSON"
    except:
        pass
    
    # Try XML
    try:
        dom = minidom.parseString(content)
        formatted = dom.toprettyxml(indent="  ")
        # Remove extra blank lines from minidom
        formatted = '\n'.join([line for line in formatted.split('\n') if line.strip()])
        return colorize_xml(formatted), "XML"
    except:
        pass
    
    # Fallback Text
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    lines.sort()
    return colorize_txt(lines), "Text (Sorted)"

def colorize_json(text):
    """Adds colors to JSON."""
    text = re.sub(r'(".*?")(\s*:)', f'{Style.BLUE}\\1{Style.RESET}\\2', text)
    text = re.sub(r'(:\s*)(".*?")', f'\\1{Style.GREEN}\\2{Style.RESET}', text)
    text = re.sub(r'(:\s*)(\d+)', f'\\1{Style.ORANGE}\\2{Style.RESET}', text)
    text = re.sub(r'(\s*)(true|false|null)', f'\\1{Style.MAGENTA}\\2{Style.RESET}', text)
    return text

def colorize_xml(text):
    """Adds colors to XML."""
    text = re.sub(r'(<[^>]+>)', f'{Style.MAGENTA}\\1{Style.RESET}', text)
    return text

def colorize_txt(lines):
    """Adds colors and line numbers to Text."""
    colored = []
    for i, line in enumerate(lines, 1):
        colored.append(f"{Style.CYAN}{i:04d}{Style.RESET} | {Style.WHITE}{line}{Style.RESET}")
    return "\n".join(colored)

def add_separators(content):
    """Adds the requested separator lines between every line of output."""
    lines = content.split('\n')
    # Join lines with the separator
    separated_content = f"\n{Style.SEP}\n".join(lines)
    return separated_content

def display_output(content, file_type):
    """Prints the result to terminal."""
    print(f"\n{Style.SEP}")
    print(f"{Style.BOLD}{Style.GREEN} {Style.E_MAGIC} PREVIEW: {file_type} Detected {Style.E_MAGIC} {Style.RESET}")
    print(f"{Style.SEP}\n")
    print(content)
    print(f"\n{Style.SEP}\n")

def save_to_pwd(content, file_type):
    """Saves file to Current Working Directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"organized_{file_type.lower()}_{timestamp}.txt"
    path = os.path.join(os.getcwd(), filename)
    
    try:
        # We save raw text without ANSI codes for compatibility, 
        # OR we can save with codes if they use a compatible editor.
        # Let's save WITH codes so they see colors in supported editors, 
        # but strip them for standard notepad compatibility if preferred.
        # Decision: Save WITH colors as requested ("colored txt file").
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, path
    except Exception as e:
        return False, str(e)

def ask_to_save(content, file_type):
    """Asks user if they want to save the file."""
    while True:
        choice = input(f"{Style.BOLD}{Style.E_SAVE} Do you want to save this to the current folder? (y/n): {Style.RESET}").strip().lower()
        if choice in ['y', 'yes']:
            success, result = save_to_pwd(content, file_type)
            if success:
                print(f"\n{Style.GREEN}{Style.BOLD}{Style.E_CHECK} Saved successfully!{Style.RESET}")
                print(f"{Style.DIM}Location: {result}{Style.RESET}\n")
            else:
                print(f"\n{Style.RED}{Style.E_CROSS} Save failed: {result}{Style.RESET}\n")
            break
        elif choice in ['n', 'no']:
            print(f"\n{Style.YELLOW}{Style.E_STOP} No problem! File not saved.{Style.RESET}\n")
            break
        else:
            print(f"{Style.RED}Please type 'y' or 'n'.{Style.RESET}")

# --- 🏁 Main Program ---

def main():
    # Enable ANSI colors on Windows if needed
    if os.name == 'nt':
        os.system('') 

    print_banner()
    
    try:
        # 1. Choose Input Mode
        mode = get_input_mode()
        content = ""
        
        if mode == 'file':
            path = get_file_path()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"{Style.RED}{Style.E_CROSS} Error reading file: {e}{Style.RESET}")
                return
        else:
            content = get_pasted_content()
            
        if not content.strip():
            print(f"{Style.RED}{Style.E_WARNING} No content provided. Exiting.{Style.RESET}")
            return

        # 2. Process Content
        print(f"\n{Style.CYAN}⚙️  Processing...{Style.RESET}")
        processed_content, file_type = detect_and_process(content)
        
        if not processed_content:
            print(f"{Style.RED}{Style.E_CROSS} Could not parse content.{Style.RESET}")
            return

        # 3. Add Separators (The requested '----' lines)
        final_output = add_separators(processed_content)
        
        # Add a header to the output content itself
        header = f"{Style.DIM}# Organized by Magic Organizer | Type: {file_type} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}{Style.RESET}"
        final_output = header + "\n" + final_output

        # 4. Display Immediately
        display_output(final_output, file_type)
        
        # 5. Ask to Save
        ask_to_save(final_output, file_type)
        
        print(f"{Style.HEART} Thank you for using Magic Organizer! {Style.HEART}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Style.RED}{Style.E_STOP} Program interrupted by user.{Style.RESET}\n")
    except Exception as e:
        print(f"\n{Style.RED}{Style.E_CROSS} Unexpected Error: {e}{Style.RESET}\n")

if __name__ == "__main__":
    main()
