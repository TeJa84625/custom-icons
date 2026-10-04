import os
import json
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox

SAVE_DIR = "save"
SVGS_JSON_PATH = os.path.join(SAVE_DIR, "svgs.json")

def generate_3char_key(filename, author, license_text, category):
    """Generates a guaranteed unique 3-character alphanumeric key incorporating filename, author, license, and category."""
    raw_str = f"{filename}_{author}_{license_text}_{category}"
    hasher = hashlib.md5(raw_str.encode('utf-8')).hexdigest()
    return hasher[:3].upper()

class SVGManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG Library Manager - Pro Sidebar Edition")
        self.root.geometry("1300x800")
        
        self.data = self.load_svgs_json()
        self.file_widgets = []
        self._resize_timer = None
        self.bulk_panel_visible = False

        self.create_widgets()
        self.populate_grid()

    def load_svgs_json(self):
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        if not os.path.exists(SVGS_JSON_PATH):
            default_data = {"totalFiles": 0, "totalSvgs": 0, "indices": []}
            with open(SVGS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)
            return default_data
        
        with open(SVGS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_widgets(self):
        # Top Control & Filter Frame
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        title_label = ttk.Label(top_frame, text="SVG Library Manager", font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)

        # Action Buttons on Right
        save_btn = ttk.Button(top_frame, text="Save All Changes (Disk)", command=self.save_all_data)
        save_btn.pack(side=tk.RIGHT, padx=5)

        refresh_btn = ttk.Button(top_frame, text="Reload", command=self.reload_data)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Filter/Search Bar Frame
        filter_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        filter_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(filter_frame, text="Filter/Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_grid())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        select_all_btn = ttk.Button(filter_frame, text="Select All Visible", command=lambda: self.toggle_all_selection(True))
        select_all_btn.pack(side=tk.LEFT, padx=10)

        deselect_all_btn = ttk.Button(filter_frame, text="Deselect All", command=lambda: self.toggle_all_selection(False))
        deselect_all_btn.pack(side=tk.LEFT, padx=2)

        # Main Workspace Container (Grid Left, Bulk Sidebar Right)
        workspace = ttk.Frame(self.root)
        workspace.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Container for Grid
        left_container = ttk.Frame(workspace)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left_container, borderwidth=0, background="#f4f4f4")
        self.scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding=5)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Right-Hand Side Bulk Edit Panel (Hidden initially)
        self.right_panel = ttk.LabelFrame(workspace, text=" Bulk Edit Panel ", padding=10)

        # Responsive window resizing listener
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    def setup_bulk_panel(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        selected_items = [item for item in self.file_widgets if item["var_selected"].get()]
        
        if not selected_items:
            self.right_panel.pack_forget()
            self.bulk_panel_visible = False
            return

        if not self.bulk_panel_visible:
            self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=5)
            self.bulk_panel_visible = True

        ttk.Label(self.right_panel, text=f"Selected Files: {len(selected_items)}", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))

        file_list_frame = ttk.LabelFrame(self.right_panel, text=" Files Target ", padding=5)
        file_list_frame.pack(fill=tk.X, pady=5)
        
        file_names_str = ", ".join([item["filename"] for item in selected_items])
        lbl_files = ttk.Label(file_list_frame, text=file_names_str, wraplength=260, font=("Arial", 9))
        lbl_files.pack(fill=tk.X)

        options_frame = ttk.LabelFrame(self.right_panel, text=" Fields to Patch (Check to Modify) ", padding=8)
        options_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        row = 0
        self.bulk_vars = {}

        def add_toggle_field(label, key):
            nonlocal row
            apply_var = tk.BooleanVar(value=False)
            val_var = tk.BooleanVar(value=False)
            
            cb_apply = ttk.Checkbutton(options_frame, text=f"Update {label}", variable=apply_var)
            cb_apply.grid(row=row, column=0, sticky="w", pady=3)
            
            cb_val = ttk.Checkbutton(options_frame, text="True", variable=val_var)
            cb_val.grid(row=row, column=1, sticky="w", padx=5, pady=3)
            
            self.bulk_vars[key] = (apply_var, val_var)
            row += 1

        add_toggle_field("Animated", "animated")
        add_toggle_field("New", "new")
        add_toggle_field("Colored", "colored")
        add_toggle_field("Outline", "outline")  # Outline boolean toggle in bulk panel

        def add_text_field(label, key):
            nonlocal row
            apply_var = tk.BooleanVar(value=False)
            val_var = tk.StringVar(value="")
            
            cb_apply = ttk.Checkbutton(options_frame, text=f"Update {label}", variable=apply_var)
            cb_apply.grid(row=row, column=0, sticky="w", pady=3)
            
            ent = ttk.Entry(options_frame, textvariable=val_var, width=18)
            ent.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
            
            self.bulk_vars[key] = (apply_var, val_var)
            row += 1

        add_text_field("Category", "category")
        add_text_field("License", "license")

        btn_action_frame = ttk.Frame(self.right_panel)
        btn_action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_action_frame, text="Apply", command=self.apply_bulk_changes).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_action_frame, text="Cancel", command=lambda: self.toggle_all_selection(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        if self._resize_timer:
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(150, self.reflow_grid)

    def reflow_grid(self):
        canvas_width = self.canvas.winfo_width()
        cols = max(1, canvas_width // 450)
        
        visible_items = [item for item in self.file_widgets if item["visible"]]
        for index, item in enumerate(visible_items):
            item["card"].grid(row=index // cols, column=index % cols, sticky="nsew", padx=6, pady=6)

    def populate_grid(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.file_widgets.clear()

        indices = self.data.get("indices", [])
        
        for entry in indices:
            filename = entry.get("file", "")
            file_path = os.path.join(SAVE_DIR, filename)

            file_info = {}
            icon_count = entry.get("count", 0)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        ind_data = json.load(f)
                        file_info = ind_data.get("info", {})
                        icon_count = len(ind_data.get("icons", {}))
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

            card = ttk.LabelFrame(self.scrollable_frame, text=f" File: {filename} ", padding=8)

            var_selected = tk.BooleanVar(value=False)
            var_selected.trace("w", lambda *args: self.setup_bulk_panel())
            sel_cb = ttk.Checkbutton(card, text="Select for Bulk Edit", variable=var_selected)
            sel_cb.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

            var_animated = tk.BooleanVar(value=entry.get("animated", False))
            var_new = tk.BooleanVar(value=entry.get("new", False))
            var_colored = tk.BooleanVar(value=entry.get("colored", False))
            
            # Handle outline: check current 'outline' or legacy 'width edit'
            raw_outline = entry.get("outline", entry.get("width edit", False))
            default_outline = True if (raw_outline is True or raw_outline == "outline") else False
            var_outline = tk.BooleanVar(value=default_outline)

            var_count = tk.StringVar(value=str(icon_count))
            var_author = tk.StringVar(value=file_info.get("author", {}).get("name", ""))
            var_author_url = tk.StringVar(value=file_info.get("author", {}).get("url", ""))
            var_license = tk.StringVar(value=file_info.get("license", {}).get("title", ""))
            var_license_url = tk.StringVar(value=file_info.get("license", {}).get("url", ""))
            
            file_category = file_info.get("category", entry.get("category", ""))
            var_category = tk.StringVar(value=file_category)

            row_idx = 1
            # Checkbox frame containing all booleans including outline
            cb_frame = ttk.Frame(card)
            cb_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=2)
            ttk.Checkbutton(cb_frame, text="Animated", variable=var_animated).pack(side=tk.LEFT, padx=2)
            ttk.Checkbutton(cb_frame, text="New", variable=var_new).pack(side=tk.LEFT, padx=2)
            ttk.Checkbutton(cb_frame, text="Colored", variable=var_colored).pack(side=tk.LEFT, padx=2)
            ttk.Checkbutton(cb_frame, text="Outline", variable=var_outline).pack(side=tk.LEFT, padx=2)
            row_idx += 1

            def add_field(label_text, var_ref):
                nonlocal row_idx
                lbl = ttk.Label(card, text=label_text, width=13)
                lbl.grid(row=row_idx, column=0, sticky="w", pady=2)
                ent = ttk.Entry(card, textvariable=var_ref, width=30)
                ent.grid(row=row_idx, column=1, sticky="ew", pady=2)
                row_idx += 1

            add_field("Total Icons:", var_count)
            add_field("Author Name:", var_author)
            add_field("Author URL:", var_author_url)
            add_field("License:", var_license)
            add_field("License URL:", var_license_url)
            add_field("Category:", var_category)

            self.file_widgets.append({
                "filename": filename,
                "file_path": file_path,
                "card": card,
                "visible": True,
                "var_selected": var_selected,
                "var_animated": var_animated,
                "var_new": var_new,
                "var_colored": var_colored,
                "var_outline": var_outline,
                "var_count": var_count,
                "var_author": var_author,
                "var_author_url": var_author_url,
                "var_license": var_license,
                "var_license_url": var_license_url,
                "var_category": var_category
            })

        self.reflow_grid()

    def filter_grid(self):
        query = self.search_var.get().lower().strip()
        for item in self.file_widgets:
            match = (
                query in item["filename"].lower() or
                query in item["var_author"].get().lower() or
                query in item["var_category"].get().lower() or
                query in item["var_license"].get().lower()
            )
            item["visible"] = match
            if match:
                item["card"].grid()
            else:
                item["card"].grid_remove()
        self.reflow_grid()

    def toggle_all_selection(self, state):
        for item in self.file_widgets:
            if item["visible"]:
                item["var_selected"].set(state)
        self.setup_bulk_panel()

    def apply_bulk_changes(self):
        selected_items = [item for item in self.file_widgets if item["var_selected"].get()]
        if not selected_items:
            return

        changes_desc = []
        patches = {}
        for key, (apply_var, val_var) in self.bulk_vars.items():
            if apply_var.get():
                val = val_var.get()
                patches[key] = val
                changes_desc.append(f"• {key.capitalize()} -> {val}")

        if not patches:
            messagebox.showwarning("No Fields Selected", "Please check at least one field to update in the side panel.")
            return

        msg = f"You are about to update {len(selected_items)} file(s) with these selective changes:\n\n" + \
              "\n".join(changes_desc) + \
              "\n\nDo you want to apply these changes? (Remember to click 'Save All Changes (Disk)' afterwards)."
              
        confirm = messagebox.askyesno("Confirm Selective Bulk Update", msg)
        if not confirm:
            return

        for item in selected_items:
            if "animated" in patches:
                item["var_animated"].set(patches["animated"])
            if "new" in patches:
                item["var_new"].set(patches["new"])
            if "colored" in patches:
                item["var_colored"].set(patches["colored"])
            if "outline" in patches:
                item["var_outline"].set(patches["outline"])
            if "category" in patches and str(patches["category"]).strip() != "":
                item["var_category"].set(patches["category"])
            if "license" in patches and str(patches["license"]).strip() != "":
                item["var_license"].set(patches["license"])

        messagebox.showinfo("Applied", "Changes staged successfully! Click 'Save All Changes (Disk)' to finalize.")
        self.toggle_all_selection(False)

    def save_all_data(self):
        confirm = messagebox.askyesno("Confirm Disk Write", "Are you sure you want to write all updates and regenerate unique keys to disk?")
        if not confirm:
            return

        total_svgs = 0
        updated_indices = []

        for item in self.file_widgets:
            filename = item["filename"]
            file_path = item["file_path"]

            try:
                count = int(item["var_count"].get())
            except ValueError:
                count = 0

            total_svgs += count

            author_name = item["var_author"].get()
            license_title = item["var_license"].get()
            category_val = item["var_category"].get()
            
            # Generate unique 3-char key incorporating filename
            short_key = generate_3char_key(filename, author_name, license_title, category_val)

            updated_indices.append({
                "file": filename,
                "count": count,
                "animated": item["var_animated"].get(),
                "colored": item["var_colored"].get(),
                "outline": item["var_outline"].get(),  # Stored as boolean true/false
                "new": item["var_new"].get(),
                "category": category_val,
                "key": short_key
            })

            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        ind_data = json.load(f)
                    
                    if "info" not in ind_data:
                        ind_data["info"] = {}
                    
                    ind_data["info"]["category"] = category_val
                    ind_data["info"]["total"] = count
                    
                    if "author" not in ind_data["info"]:
                        ind_data["info"]["author"] = {}
                    ind_data["info"]["author"]["name"] = author_name
                    ind_data["info"]["author"]["url"] = item["var_author_url"].get()

                    if "license" not in ind_data["info"]:
                        ind_data["info"]["license"] = {}
                    ind_data["info"]["license"]["title"] = license_title
                    ind_data["info"]["license"]["url"] = item["var_license_url"].get()

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(ind_data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"Failed to update individual file {filename}: {e}")

        self.data["totalFiles"] = len(updated_indices)
        self.data["totalSvgs"] = total_svgs
        self.data["indices"] = updated_indices

        with open(SVGS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Success", "All files and svgs.json saved successfully to disk with unique keys and outline booleans!")

    def reload_data(self):
        self.data = self.load_svgs_json()
        self.populate_grid()
        messagebox.showinfo("Reloaded", "Data reloaded from disk.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SVGManagerApp(root)
    root.mainloop()