import os
import json
import re
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class IconifyBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Iconify HTML Batch & Queue Processor")
        self.root.geometry("850x700")
        self.root.minsize(750, 580)
        
        self.queue_items = [] # Stores collection metadata and status
        
        self.setup_ui()

    def setup_ui(self):
        pad_opts = {'padx': 10, 'pady': 5}
        
        # --- Top Section: HTML Input ---
        html_frame = tk.LabelFrame(self.root, text=" 1. Paste HTML Snippet ", font=("Arial", 10, "bold"))
        html_frame.pack(fill="x", **pad_opts)
        
        top_bar = tk.Frame(html_frame)
        top_bar.pack(fill="x", padx=5, pady=2)
        
        paste_btn = tk.Button(top_bar, text="Paste HTML", command=self.paste_html, bg="#e0e0e0", cursor="hand2")
        paste_btn.pack(side="left", padx=2)
        
        parse_btn = tk.Button(top_bar, text="Extract Collections & Save data.json", command=self.extract_collections, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), cursor="hand2")
        parse_btn.pack(side="right", padx=2)
        
        self.html_text = scrolledtext.ScrolledText(html_frame, height=5, font=("Courier", 9), wrap=tk.WORD)
        self.html_text.pack(fill="x", padx=5, pady=5)
        
        # --- Middle Section: Live Data Table ---
        table_frame = tk.LabelFrame(self.root, text=" 2. Collection Processing Queue & Live Status Table ", font=("Arial", 10, "bold"))
        table_frame.pack(fill="both", expand=True, **pad_opts)
        
        columns = ("file", "name", "author", "status", "svgs")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("file", text="Filename")
        self.tree.heading("name", text="Collection Name")
        self.tree.heading("author", text="Author")
        self.tree.heading("status", text="Status")
        self.tree.heading("svgs", text="No. of SVGs")
        
        self.tree.column("file", width=160, anchor="w")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("author", width=120, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("svgs", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # --- Bottom Section: Action Control ---
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill="x", **pad_opts)
        
        self.process_btn = tk.Button(
            action_frame, 
            text="▶ Start Processing Queue (One-by-One with Confirmation)", 
            font=("Arial", 11, "bold"), 
            bg="#4CAF50", 
            fg="white", 
            cursor="hand2",
            command=self.start_queue_processing
        )
        self.process_btn.pack(fill="x", padx=5, pady=5)

    def paste_html(self):
        try:
            content = self.root.clipboard_get()
            self.html_text.delete("1.0", tk.END)
            self.html_text.insert("1.0", content)
        except tk.TclError:
            messagebox.showwarning("Warning", "Clipboard is empty.")

    def extract_collections(self):
        html_content = self.html_text.get("1.0", tk.END).strip()
        if not html_content:
            messagebox.showerror("Error", "Please paste an HTML snippet first.")
            return

        # Find all <a> blocks containing collection links
        pattern = r'<a[^>]*href=["\']?/collection/([a-zA-Z0-9\-_]+)["\'][^>]*>(.*?)</a>'
        matches = re.findall(pattern, html_content, re.DOTALL)

        if not matches:
            messagebox.showwarning("Warning", "No collection links found matching pattern '/collection/...'.")
            return

        # Clear existing table and queue
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.queue_items = []
        extracted_data_for_json = []

        for slug, inner_html in matches:
            filename = f"{slug}.json"
            url = f"https://icones.js.org/collections/{slug}.json"
            
            # 1. Extract Collection Name
            name_match = re.search(r'class="[^"]*text-lg[^"]*"[^>]*>(.*?)<span', inner_html, re.DOTALL)
            if not name_match:
                name_match = re.search(r'<div[^>]*text-lg[^>]*>(.*?)</div>', inner_html, re.DOTALL)
            name = " ".join(re.sub(r'<[^>]+>', '', name_match.group(1)).split()) if name_match else slug.replace("-", " ").title()

            # 2. Extract Author & Total Icons
            author_name = "Unknown"
            total = 0
            
            text_xs_match = re.search(r'text-xs["\'][^>]*>(.*?)</div>', inner_html, re.DOTALL)
            if text_xs_match:
                xs_content = text_xs_match.group(1)
                spans = re.findall(r'<span[^>]*>(.*?)</span>', xs_content, re.DOTALL)
                clean_spans = [s.strip() for s in spans if s.strip()]
                
                if len(clean_spans) > 0:
                    author_name = re.sub(r'<[^>]+>', '', clean_spans[0])
                
                for span in clean_spans:
                    if "icon" in span.lower():
                        num_match = re.search(r'([\d,]+)', span)
                        if num_match:
                            total = int(num_match.group(1).replace(",", ""))

            item_data = {
                "slug": slug,
                "filename": filename,
                "url": url,
                "name": name,
                "total": total,
                "author": author_name,
                "status": "Pending",
                "count": 0
            }
            self.queue_items.append(item_data)
            
            # Prepare format for data.json
            extracted_data_for_json.append({
                "url": url,
                "filename": filename,
                "author": author_name,
                "name": name,
                "no_of_icons": total
            })
            
            # Insert into live table
            self.tree.insert("", "end", values=(filename, name, author_name, "Pending", "0"))

        # Save extracted metadata to data.json
        os.makedirs("save", exist_ok=True)
        data_json_path = os.path.join("save", "data.json")
        with open(data_json_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data_for_json, f, indent=2, ensure_ascii=False)

        # Stop and wait for user response as requested
        user_choice = messagebox.askyesno(
            "Extraction Complete", 
            f"All collections are extracted and ready to process ({len(self.queue_items)} found).\nMetadata saved to 'save/data.json'.\n\nWould you like to begin processing collections now?"
        )
        
        if user_choice:
            self.start_queue_processing()

    def start_queue_processing(self):
        if not self.queue_items:
            messagebox.showwarning("Warning", "Queue is empty. Please extract collections first.")
            return

        os.makedirs("save", exist_ok=True)

        for index, item in enumerate(self.queue_items):
            if item["status"] != "Pending":
                continue  

            filename = item["filename"]
            slug = item["slug"]

            # Prompt user per file with Continue / Skip / Cancel buttons
            choice = messagebox.askyesnocancel(
                "Confirm Collection Processing", 
                f"Continue with file: {filename}?\n(Collection: {item['name']})\n\n[Yes] = Continue & Process\n[No] = Skip\n[Cancel] = Stop Batch Entirely"
            )

            if choice is None:  # Cancel clicked
                break
            elif choice is False:  # Skip clicked
                item["status"] = "Skipped"
                self.update_table_row(index, "Skipped", item["count"])
                continue

            # Fetch and process collection JSON
            target_url = item["url"]
            try:
                response = requests.get(target_url)
                response.raise_for_status()
                data = response.json()

                count = self.process_and_save_collection(data, item)
                
                item["status"] = "Processed"
                item["count"] = count
                self.update_table_row(index, "Processed", count)

            except Exception as e:
                item["status"] = "Error"
                self.update_table_row(index, "Error", 0)
                messagebox.showerror("Error", f"Failed to process {filename}:\n{str(e)}")

        # Update global svgs.json summary after queue finishes or halts
        self.update_svgs_summary()
        messagebox.showinfo("Queue Complete", "Queue processing sequence finished!")

    def process_and_save_collection(self, data, item):
        filename = os.path.join("save", item["filename"])
        category = data.get("prefix", item["slug"])

        info_data = data.get("info", {})
        if not info_data:
            info_data = {
                "name": item["name"],
                "total": item["total"] if item["total"] > 0 else len(data.get("icons", {})),
                "author": {
                    "name": item["author"],
                    "url": f"https://github.com/{item['author'].lower().replace(' ', '')}"
                }
            }

        default_width = data.get("width", 24)
        default_height = data.get("height", 24)
        icons = data.get("icons", {})
        processed_icons = {}

        for icon_name, icon_info in icons.items():
            body = icon_info.get("body", "")
            w = icon_info.get("width", default_width)
            h = icon_info.get("height", default_height)

            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'

            processed_icons[icon_name] = {
                "version": "0.0.1",
                "category": category,
                "svg": svg_str
            }

        final_output = {
            "info": info_data,
            "icons": processed_icons
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        return len(processed_icons)

    def update_table_row(self, index, status, count):
        tree_items = self.tree.get_children()
        if index < len(tree_items):
            item_id = tree_items[index]
            item = self.queue_items[index]
            self.tree.item(item_id, values=(item["filename"], item["name"], item["author"], status, count))
            self.root.update_idletasks()

    def update_svgs_summary(self):
        save_dir = "save"
        if not os.path.exists(save_dir):
            return

        json_files = [f for f in os.listdir(save_dir) if f.endswith('.json') and f not in ('svgs.json', 'data.json')]
        total_files = len(json_files)
        total_svgs = 0
        indices = []

        for jf in json_files:
            file_path = os.path.join(save_dir, jf)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    icons_dict = content.get("icons", content)
                    count = len(icons_dict) if isinstance(icons_dict, dict) else 0
                    total_svgs += count
                    indices.append({"file": jf, "count": count})
            except Exception:
                pass

        summary_data = {
            "totalFiles": total_files,
            "totalSvgs": total_svgs,
            "indices": indices
        }

        summary_path = os.path.join(save_dir, "svgs.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = IconifyBatchApp(root)
    root.mainloop()