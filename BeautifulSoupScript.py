from bs4 import BeautifulSoup
import os

# Updated to your new filename
input_file = 'MyActivity-edited.html'
output_file = 'Clean_Agent_Context.txt'

def extract_clean_chat(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Make sure the script is in the same folder.")
        return

    print("Scrubbing the bloat... this may take a moment.")
    with open(input_path, 'r', encoding='utf-8') as f:
        # We use lxml if available, otherwise html.parser
        soup = BeautifulSoup(f, 'html.parser')

    # Google Activity stores chat content in divs with specific classes
    # 'content-column' usually holds the text, 'outer-cell' holds the entry
    entries = soup.find_all('div', class_='outer-cell')
    
    clean_history = []

    for entry in entries:
        # Get the timestamp and product name (Gemini)
        # Usually inside a <div> within the entry
        text_content = entry.get_text(separator="\n", strip=True)
        
        # We only want Gemini chats, not searches or other activity
        if "Gemini" in text_content:
            clean_history.append(text_content)
            clean_history.append("-" * 50)

    if clean_history:
        # Reverse because Google lists newest at the top
        clean_history.reverse()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(clean_history))
        print(f"Done! Created {output_path}")
        print("You can now upload this .txt file or paste its contents.")
    else:
        print("Couldn't find any Gemini entries. If the file is very trimmed, check the class names.")

if __name__ == "__main__":
    extract_clean_chat(input_file, output_file)