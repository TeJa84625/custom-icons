import os
import json
import csv
import io
import re
import html
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Pre-compile regex patterns at module level for maximum parsing speed
RE_SVG_TAG = re.compile(r'<svg\b([^>]*)>(.*?)</svg>', re.DOTALL | re.IGNORECASE)
RE_ATTR = re.compile(r'([a-zA-Z0-9\-_:]+)=(["\'])(.*?)\2')
RE_H2_TAG = re.compile(r'<h2[^>]*>(.*?)<\/h2>', re.DOTALL | re.IGNORECASE)
RE_HTML_TAG = re.compile(r'<[^>]+>')
RE_WHITESPACE_CHARS = re.compile(r'[\u200b\u00a0]+')
RE_DATA_V = re.compile(r'^data-v-', re.IGNORECASE)

class SVGManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG Data Processor (Optimized)")
        self.root.geometry("740x700")
        self.root.minsize(620, 560)
        
        # Format selection variable
        self.format_var = tk.StringVar(value="HTML")
        
        self.create_widgets()
        
    def create_widgets(self):
        # 1. Format Selection Frame
        format_frame = ttk.LabelFrame(self.root, text=" 1. Select Input Data Format ", padding=12)
        format_frame.pack(fill="x", padx=15, pady=10)
        
        for fmt in ["HTML", "CSV", "Single SVG"]:
            ttk.Radiobutton(
                format_frame, text=fmt, value=fmt, 
                variable=self.format_var, command=self.on_format_change
            ).pack(side="left", padx=25)
            
        # 2. Dynamic Input Container Frame
        self.content_frame = ttk.LabelFrame(self.root, text=" 2. Input Data ", padding=12)
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.setup_bulk_inputs()
        
        # 3. Action Buttons & Progress Frame
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x", padx=15, pady=10)
        
        self.progress_bar = ttk.Progressbar(action_frame, orient="horizontal", mode="indeterminate", length=180)
        
        self.process_btn = ttk.Button(action_frame, text="Process & Update JSON", command=self.start_processing_thread, state="disabled")
        self.process_btn.pack(side="right", padx=5)
        
        ttk.Button(action_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)
        
    def on_format_change(self):
        # Cleanly destroy existing children without lagging
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        fmt = self.format_var.get()
        if fmt in ["HTML", "CSV"]:
            self.setup_bulk_inputs()
        else:
            self.setup_single_svg_inputs()
            
        self.process_btn.config(state="disabled")
        
    def setup_bulk_inputs(self):
        fmt = self.format_var.get()
        lbl_text = "Paste your HTML section containing <h2> categories and icon blocks below:" if fmt == "HTML" else "Paste your CSV data below (columns: name, svg, version, category):"
        
        ttk.Label(self.content_frame, text=lbl_text, font=("Arial", 9, "bold")).pack(anchor="w", pady=5)
        ttk.Button(self.content_frame, text="📋 Paste from Clipboard", command=self.paste_clipboard).pack(anchor="w", pady=5)
        
        text_container = ttk.Frame(self.content_frame)
        text_container.pack(fill="both", expand=True, pady=5)
        
        self.text_input = tk.Text(text_container, wrap="word", height=14)
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text_input.yview)
        self.text_input.configure(yscrollcommand=scrollbar.set)
        
        self.text_input.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.text_input.bind("<KeyRelease>", self.check_text_input)
        
    def setup_single_svg_inputs(self):
        ttk.Label(self.content_frame, text="Enter Single SVG Details", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(self.content_frame, text="Name (Mandatory):").grid(row=1, column=0, sticky="w", pady=8)
        self.name_entry = ttk.Entry(self.content_frame, width=45)
        self.name_entry.grid(row=1, column=1, sticky="w", pady=8)
        self.name_entry.bind("<KeyRelease>", self.check_single_inputs)
        
        ttk.Label(self.content_frame, text="SVG Code (Mandatory):").grid(row=2, column=0, sticky="nw", pady=8)
        
        svg_container = ttk.Frame(self.content_frame)
        svg_container.grid(row=2, column=1, sticky="w", pady=8)
        
        self.svg_text = tk.Text(svg_container, width=45, height=6)
        svg_scroll = ttk.Scrollbar(svg_container, orient="vertical", command=self.svg_text.yview)
        self.svg_text.configure(yscrollcommand=svg_scroll.set)
        self.svg_text.pack(side="left", fill="both", expand=True)
        svg_scroll.pack(side="right", fill="y")
        self.svg_text.bind("<KeyRelease>", self.check_single_inputs)
        
        ttk.Label(self.content_frame, text="Version (Optional):").grid(row=3, column=0, sticky="w", pady=8)
        self.version_entry = ttk.Entry(self.content_frame, width=45)
        self.version_entry.insert(0, "0.0.1")
        self.version_entry.grid(row=3, column=1, sticky="w", pady=8)
        
        ttk.Label(self.content_frame, text="Category (Optional):").grid(row=4, column=0, sticky="w", pady=8)
        self.category_entry = ttk.Entry(self.content_frame, width=45)
        self.category_entry.grid(row=4, column=1, sticky="w", pady=8)
        
        ttk.Button(self.content_frame, text="📋 Paste to SVG Box", command=self.paste_clipboard).grid(row=5, column=1, sticky="w", pady=5)
        
    def paste_clipboard(self):
        try:
            clipboard_data = self.root.clipboard_get()
            fmt = self.format_var.get()
            if fmt in ["HTML", "CSV"]:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", clipboard_data)
                self.check_text_input()
            elif fmt == "Single SVG":
                self.svg_text.delete("1.0", tk.END)
                self.svg_text.insert("1.0", clipboard_data)
                self.check_single_inputs()
            
            self.process_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Clipboard Error", f"Could not read clipboard: {e}")
            
    def check_text_input(self, event=None):
        content = self.text_input.get("1.0", tk.END).strip()
        self.process_btn.config(state="normal" if content else "disabled")
            
    def check_single_inputs(self, event=None):
        name = self.name_entry.get().strip()
        svg = self.svg_text.get("1.0", tk.END).strip()
        self.process_btn.config(state="normal" if (name and svg) else "disabled")

    def clean_and_format_svg(self, svg_str):
        match = RE_SVG_TAG.search(svg_str)
        if not match:
            return svg_str
            
        attr_str, inner_content = match.groups()
        attrs = {}
        
        for attr_match in RE_ATTR.finditer(attr_str):
            key, quote, val = attr_match.groups()
            key_lower = key.lower()
            
            if RE_DATA_V.match(key_lower) or key_lower in ['class', 'aria-hidden']:
                continue
                
            if key_lower == 'stroke' and val.lower() == 'currentcolor':
                val = '#ffffff'
                
            attrs[key] = val
            
        preferred_order = ['xmlns', 'width', 'height', 'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin']
        ordered_attrs = []
        
        for pref_key in preferred_order:
            found_key = None
            for k in attrs.keys():
                if k.lower() == pref_key.lower():
                    found_key = k
                    break
            
            if found_key:
                output_key = 'viewBox' if pref_key.lower() == 'viewbox' else found_key
                ordered_attrs.append(f'{output_key}="{attrs[found_key]}"')
                del attrs[found_key]
                
        for key, val in attrs.items():
            ordered_attrs.append(f'{key}="{val}"')
            
        return f"<svg {' '.join(ordered_attrs)}>{inner_content}</svg>"

    def start_processing_thread(self):
        """Dispatches data processing to a background thread to prevent UI freezing / lag."""
        self.process_btn.config(state="disabled")
        self.progress_bar.pack(side="left", padx=10)
        self.progress_bar.start(10)
        
        # Run worker in background
        threading.Thread(target=self.process_data, daemon=True).start()

    def process_data(self):
        fmt = self.format_var.get()
        new_data = {}
        
        try:
            if fmt == "HTML":
                html_content = self.text_input.get("1.0", tk.END)
                
                categories = []
                for m in RE_H2_TAG.finditer(html_content):
                    raw_title = m.group(1)
                    clean_title = RE_HTML_TAG.sub('', raw_title)
                    clean_title = html.unescape(clean_title)
                    clean_title = RE_WHITESPACE_CHARS.sub('', clean_title).strip()
                    categories.append((m.start(), clean_title))
                    
                def get_category_at_pos(pos):
                    active_cat = ""
                    for cat_pos, cat_name in categories:
                        if pos >= cat_pos:
                            active_cat = cat_name
                        else:
                            break
                    return active_cat

                for svg_m in RE_SVG_TAG.finditer(html_content):
                    svg_start = svg_m.start()
                    raw_svg = svg_m.group(0)
                    
                    window_start = max(0, svg_start - 300)
                    window_end = min(len(html_content), svg_start + 300)
                    context_snippet = html_content[window_start:window_end]
                    
                    label_match = re.search(r'aria-label=["\']([^"\']+)["\']', context_snippet)
                    if not label_match:
                        continue
                        
                    icon_name = label_match.group(1).strip()
                    current_category = get_category_at_pos(svg_start)
                    cleaned_svg = self.clean_and_format_svg(raw_svg)
                    
                    new_data[icon_name] = {
                        "version": "0.0.1",
                        "category": current_category,
                        "svg": cleaned_svg
                    }
                                
            elif fmt == "CSV":
                csv_content = self.text_input.get("1.0", tk.END)
                f = io.StringIO(csv_content.strip())
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name") or row.get("id")
                    if name:
                        raw_svg = row.get("svg", "")
                        category = row.get("category", "")
                        category = html.unescape(category)
                        category = RE_WHITESPACE_CHARS.sub('', category).strip()
                        
                        new_data[name] = {
                            "version": row.get("version", "0.0.1"),
                            "category": category,
                            "svg": self.clean_and_format_svg(raw_svg)
                        }
                        
            elif fmt == "Single SVG":
                # Safely pull text widgets on main thread before async callback
                name = self.name_entry.get().strip()
                svg = self.svg_text.get("1.0", tk.END).strip()
                version = self.version_entry.get().strip() or "0.0.1"
                category = self.category_entry.get().strip()
                category = html.unescape(category)
                category = RE_WHITESPACE_CHARS.sub('', category).strip()
                
                if not name or not svg:
                    self.root.after(0, lambda: messagebox.showwarning("Validation Error", "Name and SVG code are mandatory fields."))
                    self.root.after(0, self.reset_ui_state)
                    return
                    
                new_data[name] = {
                    "version": version,
                    "category": category,
                    "svg": self.clean_and_format_svg(svg)
                }
                
            if not new_data:
                self.root.after(0, lambda: messagebox.showwarning("No Data", "No valid records or icons could be parsed from your input."))
                self.root.after(0, self.reset_ui_state)
                return
                
            self.save_to_json(new_data)
            
        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Processing Error", f"An error occurred while parsing data: {err}"))
            self.root.after(0, self.reset_ui_state)
            
    def save_to_json(self, new_data):
        save_dir = "save"
        file_path = os.path.join(save_dir, "svgs.json")
        
        if not os.path.exists(file_path) and not messagebox.askyesno("File Not Found", f"The file '{file_path}' was not found.\nDo you want to create it?"):
            self.root.after(0, self.reset_ui_state)
            return
            
        existing_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = {}
                
        existing_data.update(new_data)
        
        os.makedirs(save_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)
            
        # Safely notify success on the main Tkinter thread
        self.root.after(0, lambda: messagebox.showinfo("Success", f"Successfully updated `{file_path}` with {len(new_data)} item(s)!"))
        self.root.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.process_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SVGManagerApp(root)
    root.mainloop()