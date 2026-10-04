import json
import os
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext


def extract_and_update_svg_loaders(html_content):
  # 1. Ensure the 'save' directory exists
  save_dir = "save"
  os.makedirs(save_dir, exist_ok=True)
  json_filename = os.path.join(save_dir, "svg-loaders.json")

  # 2. Find all loader anchor tags using regular expressions (no BeautifulSoup required)
  # Matches <a href="/tools/svg-loaders/NAME" ...> ... </a>
  pattern = (
      r'<a\s+[^>]*href=["\']?/tools/svg-loaders/([^"\']+)["\']?[^>]*>(.*?)</a>'
  )
  loader_matches = list(re.finditer(pattern, html_content, re.DOTALL))

  if not loader_matches:
    return (
        0,
        "No loader elements matching '/tools/svg-loaders/' found in the HTML.",
    )

  # 3. Load existing JSON data if the file already exists, else create default structure
  if os.path.exists(json_filename):
    with open(json_filename, "r", encoding="utf-8") as f:
      data = json.load(f)
  else:
    data = {
        "info": {
            "name": "SVG Loaders",
            "total": 0,
            "version": "1.0.0",
            "author": {"name": "Loaders Author", "url": ""},
            "license": {"title": "MIT", "spdx": "MIT", "url": ""},
            "samples": [],
            "height": 24,
            "category": "Loaders",
            "tags": ["Animation", "Spinners"],
            "palette": False,
        },
        "icons": {},
    }

  # 4. Extract names and SVGs
  extracted_count = 0
  for match in loader_matches:
    name = match.group(1)
    inner_html = match.group(2)

    # Find the <svg ...>...</svg> block inside the anchor tag content
    svg_match = re.search(r"(<svg\b.*?</svg>)", inner_html, re.DOTALL)
    if svg_match and name:
      svg_str = svg_match.group(1)
      data["icons"][name] = {
          "version": "1.0.0",
          "category": "Loaders",
          "svg": svg_str,
      }
      extracted_count += 1

  # 5. Update metadata fields
  data["info"]["total"] = len(data["icons"])
  data["info"]["samples"] = list(data["icons"].keys())[:6]

  # 6. Save back to the JSON file inside the save directory
  with open(json_filename, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

  return extracted_count, json_filename


# GUI Application Class
class SVGExtractorApp:

  def __init__(self, root):
    self.root = root
    self.root.title("SVG Loader Extractor (Built-in)")
    self.root.geometry("650x520")

    # Instruction Label
    self.label = tk.Label(
        root,
        text="Paste your HTML code containing the SVG loaders below:",
        font=("Arial", 11, "bold"),
    )
    self.label.pack(pady=10)

    # Scrolled Text Box for HTML input
    self.text_area = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, width=75, height=16, font=("Consolas", 10)
    )
    self.text_area.pack(padx=10, pady=5)

    # Process & Save Button
    self.process_btn = tk.Button(
        root,
        text="Extract & Save to /save",
        command=self.on_process,
        bg="#2E7D32",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=12,
        pady=6,
    )
    self.process_btn.pack(pady=15)

  def on_process(self):
    html_content = self.text_area.get("1.0", tk.END).strip()
    if not html_content:
      messagebox.showwarning("Warning", "Please paste some HTML code first!")
      return

    try:
      count, result = extract_and_update_svg_loaders(html_content)
      if count > 0:
        messagebox.showinfo(
            "Success!",
            f"Successfully extracted {count} loader(s)!\nSaved inside:"
            f" {result}",
        )
      else:
        messagebox.showwarning("No Match Found", result)
    except Exception as e:
      messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")


if __name__ == "__main__":
  root = tk.Tk()
  app = SVGExtractorApp(root)
  root.mainloop()