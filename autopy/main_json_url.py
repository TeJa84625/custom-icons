import os
import json
import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext

def paste_to_widget(widget):
    """Pastes text from clipboard into an Entry or Text widget."""
    try:
        content = widget.clipboard_get()
        if isinstance(widget, tk.Entry):
            widget.delete(0, tk.END)
            widget.insert(0, content)
        elif isinstance(widget, scrolledtext.ScrolledText):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", content)
    except tk.TclError:
        messagebox.showwarning("Warning", "Clipboard is empty or contains unsupported data.")

def process_and_save_data(data, status_box):
    """Core logic to process icons dictionary, save/update JSON, and return file stats."""
    try:
        os.makedirs("save", exist_ok=True)
        
        # Extract prefix to use as both filename and category name
        prefix = data.get("prefix", "icons")
        filename = os.path.join("save", f"{prefix}.json")
        category = prefix
        
        # Load existing JSON data if the file already exists (for updates/merging)
        existing_data = {}
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
                
        default_width = data.get("width", 24)
        default_height = data.get("height", 24)
        icons = data.get("icons", {})
        processed_count = len(icons)
        
        # Process each icon and convert to the requested format
        for icon_name, icon_info in icons.items():
            body = icon_info.get("body", "")
            w = icon_info.get("width", default_width)
            h = icon_info.get("height", default_height)
            
            # Construct the SVG string
            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
            
            existing_data[icon_name] = {
                "version": "0.0.1",
                "category": category,
                "svg": svg_str
            }
            
        # Save/Update the JSON file in the save/ directory
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
        total_file_icons = len(existing_data)
        
        # Log detailed stats to status box
        success_msg = (
            f"✔ Successfully saved/updated!\n"
            f"   📂 File: {filename}\n"
            f"   🏷️ Category: {category}\n"
            f"   ➕ Added/Updated: {processed_count} icons\n"
            f"   📊 Total Icons in File: {total_file_icons}\n"
            f"{'-'*55}\n"
        )
        status_box.insert(tk.END, success_msg)
        status_box.see(tk.END)
        
        return filename, processed_count
    except Exception as e:
        raise e

def process_from_url(url_entry, status_box):
    """Fetches data from the URL input."""
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter or paste an Iconify JSON URL.")
        return

    try:
        status_box.insert(tk.END, f"Fetching data from URL...\n")
        status_box.see(tk.END)
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        filename, count = process_and_save_data(data, status_box)
        
        # Clear the input box on success
        url_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"Successfully updated '{filename}' with {count} icons!")
        
    except Exception as e:
        err_msg = f"❌ URL Error: {str(e)}\n{'-'*55}\n"
        status_box.insert(tk.END, err_msg)
        status_box.see(tk.END)
        messagebox.showerror("Error", f"Failed to fetch URL:\n{str(e)}")

def process_from_raw_json(json_text_box, status_box):
    """Processes data from the raw JSON text area."""
    raw_text = json_text_box.get("1.0", tk.END).strip()
    if not raw_text:
        messagebox.showerror("Error", "Please paste the raw JSON content into the text area.")
        return

    try:
        status_box.insert(tk.END, f"Parsing raw JSON data...\n")
        status_box.see(tk.END)
        
        data = json.loads(raw_text)
        filename, count = process_and_save_data(data, status_box)
        
        # Clear the text box on success
        json_text_box.delete("1.0", tk.END)
        messagebox.showinfo("Success", f"Successfully updated '{filename}' with {count} icons from raw JSON!")
        
    except json.JSONDecodeError as je:
        err_msg = f"❌ JSON Parse Error: {str(je)}\n{'-'*55}\n"
        status_box.insert(tk.END, err_msg)
        status_box.see(tk.END)
        messagebox.showerror("Error", f"Invalid JSON format:\n{str(je)}")
    except Exception as e:
        err_msg = f"❌ Error: {str(e)}\n{'-'*55}\n"
        status_box.insert(tk.END, err_msg)
        status_box.see(tk.END)
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

def run_app():
    root = tk.Tk()
    root.title("Iconify JSON Processor")
    root.geometry("680x680")
    root.minsize(580, 600)
    
    pad_opts = {'padx': 10, 'pady': 5}
    
    # --- Option 1: URL Section ---
    url_frame = tk.LabelFrame(root, text=" Option 1: Iconify API URL ", font=("Arial", 10, "bold"))
    url_frame.pack(fill="x", **pad_opts)
    
    url_entry = tk.Entry(url_frame, font=("Arial", 10))
    url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
    
    paste_url_btn = tk.Button(url_frame, text="Paste", command=lambda: paste_to_widget(url_entry), width=8, bg="#e0e0e0", cursor="hand2")
    paste_url_btn.pack(side="right", padx=5, pady=5)
    
    process_url_btn = tk.Button(
        root, 
        text="Process & Update from URL", 
        font=("Arial", 10, "bold"), 
        bg="#4CAF50", 
        fg="white", 
        cursor="hand2",
        command=lambda: process_from_url(url_entry, status_box)
    )
    process_url_btn.pack(fill="x", padx=10, pady=2)
    
    # --- Option 2: Raw JSON Text Area Section ---
    json_frame = tk.LabelFrame(root, text=" Option 2: Paste Raw JSON Content (Fallback if URL unreachable) ", font=("Arial", 10, "bold"))
    json_frame.pack(fill="both", expand=True, **pad_opts)
    
    # Top bar inside raw json frame for paste button
    json_top_bar = tk.Frame(json_frame)
    json_top_bar.pack(fill="x", padx=5, pady=2)
    
    paste_json_btn = tk.Button(json_top_bar, text="Paste JSON Here", command=lambda: paste_to_widget(json_text_box), bg="#e0e0e0", cursor="hand2")
    paste_json_btn.pack(side="left", padx=2)
    
    json_text_box = scrolledtext.ScrolledText(json_frame, font=("Courier", 9), wrap=tk.WORD, height=6)
    json_text_box.pack(fill="both", expand=True, padx=5, pady=5)
    
    process_json_btn = tk.Button(
        root, 
        text="Process & Update from Raw JSON", 
        font=("Arial", 10, "bold"), 
        bg="#2196F3", 
        fg="white", 
        cursor="hand2",
        command=lambda: process_from_raw_json(json_text_box, status_box)
    )
    process_json_btn.pack(fill="x", padx=10, pady=2)
    
    # --- Status/Log Section ---
    log_frame = tk.LabelFrame(root, text=" Status & Logs ", font=("Arial", 10, "bold"))
    log_frame.pack(fill="both", expand=True, **pad_opts)
    
    status_box = scrolledtext.ScrolledText(log_frame, font=("Courier", 9), wrap=tk.WORD, bg="#f9f9f9", height=8)
    status_box.pack(fill="both", expand=True, padx=5, pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    run_app()