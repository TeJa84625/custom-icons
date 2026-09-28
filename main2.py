import json
import os
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext


def paste_from_clipboard():
  """Grabs text from clipboard and inserts it into the text box."""
  try:
    clipboard_content = root.clipboard_get()
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, clipboard_content)
  except Exception as e:
    messagebox.showerror("Error", f"Could not read from clipboard:\n{str(e)}")


def process_and_save():
  """Processes the JSON, structures data, and keeps the 'search' list on a single line."""
  raw_text = text_area.get("1.0", tk.END).strip()
  if not raw_text:
    messagebox.showerror("Error", "The text area is empty. Please paste your JSON data!")
    return

  try:
    input_data = json.loads(raw_text)
  except json.JSONDecodeError as e:
    messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
    return

  svgs_file = "svgs.json"
  existing_data = {}

  # Load existing svgs.json if it already exists to append/update safely
  if os.path.exists(svgs_file):
    try:
      with open(svgs_file, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    except Exception:
      existing_data = {}

  added_count = 0
  for key, value in input_data.items():
    styles = value.get("styles", ["brands"])
    style_key = styles[0] if styles else "brands"
    
    # Extract the raw SVG string
    svg_raw = value.get("svg", {}).get(style_key, {}).get("raw", "")
    
    # Format category name
    category = style_key.capitalize() if style_key else "General"

    # Extract search terms list (defaults to empty list if not found)
    search_terms = value.get("search", {}).get("terms", [])

    # Map to your required structure including the 'search' key
    existing_data[key] = {
        "version": "0.0.1",
        "category": category,
        "search": search_terms,
        "svg": svg_raw
    }
    added_count += 1

  # Save updated data back to svgs.json with single-line search arrays
  try:
    # 1. Generate standard formatted JSON
    json_str = json.dumps(existing_data, indent=2)

    # 2. Regex to find the "search" array blocks and collapse them into a single line
    def collapse_search(match):
      inner = match.group(1)
      items = [item.strip() for item in inner.split(",") if item.strip()]
      return f'"search": [{", ".join(items)}]'

    pattern = re.compile(r'"search":\s*\[([\s\S]*?)\]')
    json_str = pattern.sub(collapse_search, json_str)

    # 3. Write to file
    with open(svgs_file, "w", encoding="utf-8") as f:
      f.write(json_str)

    messagebox.showinfo(
        "Success", 
        f"Successfully added/updated {added_count} icons in '{svgs_file}' with single-line search lists!"
    )
  except Exception as e:
    messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")


# --- GUI Setup ---
root = tk.Tk()
root.title("SVG JSON Processor")
root.geometry("650x550")
root.minsize(500, 400)

# Instruction Label
label = tk.Label(
    root, 
    text="Copy your icon data to clipboard, click 'Paste', then click 'Process'.",
    font=("Arial", 10)
)
label.pack(pady=10)

# Button Frame
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

# Paste Button
paste_btn = tk.Button(
    btn_frame, 
    text="📋 Paste from Clipboard", 
    command=paste_from_clipboard,
    bg="#4CAF50", 
    fg="white", 
    font=("Arial", 10, "bold"),
    padx=10, 
    pady=5
)
paste_btn.pack(side=tk.LEFT, padx=5)

# Text Area for JSON
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=75, height=22, font=("Consolas", 9))
text_area.pack(pady=10, padx=15, fill=tk.BOTH, expand=True)

# Process & Save Button
process_btn = tk.Button(
    root, 
    text="⚙️ Process & Save to svgs.json", 
    command=process_and_save,
    bg="#2196F3", 
    fg="white", 
    font=("Arial", 11, "bold"),
    padx=15, 
    pady=8
)
process_btn.pack(pady=15)

root.mainloop()