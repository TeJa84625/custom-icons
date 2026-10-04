import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class SVGIndexManagerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("SVG JSON Index & Property Manager")
    self.root.geometry("1200x750")

    self.workspace_dir = ""
    self.svgs_index_data = {}
    self.index_file_path = ""

    # Track selection state for each file name: {file_name: bool}
    self.selection_states = {}

    # Configure style
    style = ttk.Style()
    style.theme_use("clam")

    self.create_widgets()

  def create_widgets(self):
    # Top Control Bar (Workspace Selection & Stats)
    top_frame = ttk.LabelFrame(
        self.root, text=" Workspace & Summary ", padding=10
    )
    top_frame.pack(fill="x", padx=10, pady=10)

    ttk.Button(
        top_frame,
        text="Select Folder (e.g., 'save' or parent)",
        command=self.load_workspace,
    ).pack(side="left", padx=5)

    self.lbl_workspace = ttk.Label(
        top_frame, text="No workspace selected", font=("Arial", 10, "italic")
    )
    self.lbl_workspace.pack(side="left", padx=10)

    self.lbl_stats = ttk.Label(
        top_frame, text="Total Files: 0 | Total Svgs: 0", font=("Arial", 10, "bold")
    )
    self.lbl_stats.pack(side="right", padx=10)

    # Main Content Area (Split into Table and Batch Edit Panel)
    main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
    main_pane.pack(fill="both", expand=True, padx=10, pady=5)

    # Left Frame: Table of SVG JSON files
    left_frame = ttk.Frame(main_pane)
    main_pane.add(left_frame, weight=3)

    # Search / Filter Bar & Quick Selection Buttons
    filter_frame = ttk.Frame(left_frame)
    filter_frame.pack(fill="x", pady=5)

    ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=2)
    self.search_var = tk.StringVar()
    self.search_var.trace("w", self.filter_table)
    search_entry = ttk.Entry(
        filter_frame, textvariable=self.search_var, width=22
    )
    search_entry.pack(side="left", padx=2)

    ttk.Button(
        filter_frame,
        text="Select Filtered",
        command=self.select_all_filtered,
    ).pack(side="left", padx=5)
    ttk.Button(
        filter_frame, text="Clear Selection", command=self.clear_selection
    ).pack(side="left", padx=2)

    ttk.Label(
        filter_frame,
        text="(Double-click row to edit individual file)",
        font=("Arial", 8, "italic"),
        foreground="gray",
    ).pack(side="right", padx=5)

    # Treeview Table with Checkbox Column
    table_frame = ttk.Frame(left_frame)
    table_frame.pack(fill="both", expand=True, pady=5)

    self.columns = (
        "select",
        "file",
        "count",
        "animated",
        "colored",
        "width_edit",
        "new",
    )
    self.tree = ttk.Treeview(
        table_frame, columns=self.columns, show="headings", selectmode="browse"
    )

    self.tree.heading("select", text="[✓]")
    self.tree.heading("file", text="JSON File Name")
    self.tree.heading("count", text="SVG Count")
    self.tree.heading("animated", text="Animated")
    self.tree.heading("colored", text="Colored")
    self.tree.heading("width_edit", text="Width Edit")
    self.tree.heading("new", text="New")

    self.tree.column("select", width=45, anchor="center", stretch=False)
    self.tree.column("file", width=240, anchor="w")
    self.tree.column("count", width=80, anchor="center")
    self.tree.column("animated", width=75, anchor="center")
    self.tree.column("colored", width=75, anchor="center")
    self.tree.column("width_edit", width=80, anchor="center")
    self.tree.column("new", width=60, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=self.tree.yview
    )
    self.tree.configure(yscrollcommand=scrollbar.set)

    self.tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind click for checkbox toggling and double click for individual editor
    self.tree.bind("<Button-1>", self.on_table_click)
    self.tree.bind("<Double-1>", self.on_item_double_click)

    # Right Frame: Batch Update Panel
    right_frame = ttk.LabelFrame(
        main_pane, text=" Batch Update Properties ", padding=15
    )
    main_pane.add(right_frame, weight=1)

    ttk.Label(
        right_frame,
        text=(
            "1. Check boxes in the list\n   (or use 'Select Filtered').\n2."
            " Configure properties below.\n3. Click 'Apply & Update All'."
        ),
        font=("Arial", 9),
    ).pack(anchor="w", pady=5)

    self.var_animated = tk.BooleanVar()
    self.var_colored = tk.BooleanVar()
    self.var_width_edit = tk.BooleanVar()
    self.var_new = tk.BooleanVar()

    ttk.Checkbutton(
        right_frame, text="Animated", variable=self.var_animated
    ).pack(anchor="w", pady=8)
    ttk.Checkbutton(right_frame, text="Colored", variable=self.var_colored).pack(
        anchor="w", pady=8
    )
    ttk.Checkbutton(
        right_frame, text="Width Edit", variable=self.var_width_edit
    ).pack(anchor="w", pady=8)
    ttk.Checkbutton(
        right_frame, text="New (add field if checked)", variable=self.var_new
    ).pack(anchor="w", pady=8)

    ttk.Separator(right_frame, orient="horizontal").pack(fill="x", pady=15)

    ttk.Button(
        right_frame,
        text="Apply & Update Files",
        command=self.apply_batch_update,
    ).pack(fill="x", pady=5)
    ttk.Button(
        right_frame, text="Save svgs.json Index", command=self.save_index
    ).pack(fill="x", pady=15)

    # Status Bar
    self.status_var = tk.StringVar(
        value="Ready. Please select your 'save' folder containing svgs.json."
    )
    status_bar = ttk.Label(
        self.root,
        textvariable=self.status_var,
        relief="sunken",
        anchor="w",
        padding=5,
    )
    status_bar.pack(side="bottom", fill="x")

  def load_workspace(self):
    folder = filedialog.askdirectory(title="Select Folder containing svgs.json")
    if not folder:
      return

    # Smart detection: check if svgs.json is in selected folder or inside a 'save' subfolder
    if os.path.exists(os.path.join(folder, "svgs.json")):
      self.workspace_dir = folder
    elif os.path.exists(os.path.join(folder, "save", "svgs.json")):
      self.workspace_dir = os.path.join(folder, "save")
    else:
      messagebox.showerror(
          "Error",
          "Could not locate 'svgs.json' in the selected folder or a 'save'"
          " subfolder!",
      )
      return

    self.index_file_path = os.path.join(self.workspace_dir, "svgs.json")

    try:
      with open(self.index_file_path, "r", encoding="utf-8") as f:
        self.svgs_index_data = json.load(f)

      self.lbl_workspace.config(text=self.workspace_dir)
      total_files = self.svgs_index_data.get("totalFiles", 0)
      total_svgs = self.svgs_index_data.get("totalSvgs", 0)
      self.lbl_stats.config(
          text=f"Total Files: {total_files} | Total Svgs: {total_svgs}"
      )

      # Initialize selection states
      self.selection_states.clear()
      for idx in self.svgs_index_data.get("indices", []):
        self.selection_states[idx.get("file")] = False

      self.populate_table()
      self.status_var.set(f"Workspace loaded successfully: {self.workspace_dir}")
    except Exception as e:
      messagebox.showerror("Error", f"Failed to load svgs.json:\n{e}")

  def populate_table(self, filter_text=""):
    for item in self.tree.get_children():
      self.tree.delete(item)

    indices = self.svgs_index_data.get("indices", [])
    for idx in indices:
      file_name = idx.get("file", "")
      if filter_text and filter_text.lower() not in file_name.lower():
        continue

      is_selected = self.selection_states.get(file_name, False)
      check_symbol = "[✓]" if is_selected else "[ ]"

      count = idx.get("count", 0)
      animated = str(idx.get("animated", False))
      colored = str(idx.get("colored", False))
      width_edit = str(idx.get("width edit", False))
      new_val = str(idx.get("new", False)) if "new" in idx else "-"

      self.tree.insert(
          "",
          "end",
          values=(
              check_symbol,
              file_name,
              count,
              animated,
              colored,
              width_edit,
              new_val,
          ),
      )

  def filter_table(self, *args):
    query = self.search_var.get()
    self.populate_table(query)

  def on_table_click(self, event):
    region = self.tree.identify("region", event.x, event.y)
    if region == "cell":
      col = self.tree.identify_column(event.x)
      item = self.tree.identify_row(event.y)
      if col == "#1" and item:  # Clicked on the checkbox column
        values = self.tree.item(item, "values")
        file_name = values[1]
        current_state = self.selection_states.get(file_name, False)
        self.selection_states[file_name] = not current_state
        self.populate_table(self.search_var.get())

  def select_all_filtered(self):
    query = self.search_var.get().lower()
    for idx in self.svgs_index_data.get("indices", []):
      file_name = idx.get("file", "")
      if not query or query in file_name.lower():
        self.selection_states[file_name] = True
    self.populate_table(self.search_var.get())

  def clear_selection(self):
    for file_name in self.selection_states:
      self.selection_states[file_name] = False
    self.populate_table(self.search_var.get())

  def apply_batch_update(self):
    selected_files = [
        fname for fname, selected in self.selection_states.items() if selected
    ]
    if not selected_files:
      messagebox.showwarning(
          "Warning",
          "Please select at least one file using the checkboxes in the table.",
      )
      return

    anim_val = self.var_animated.get()
    color_val = self.var_colored.get()
    width_val = self.var_width_edit.get()
    new_val = self.var_new.get()

    updated_count = 0

    # 1. Update svgs.json index in memory
    for idx in self.svgs_index_data.get("indices", []):
      file_name = idx.get("file")
      if file_name in selected_files:
        idx["animated"] = anim_val
        idx["colored"] = color_val
        idx["width edit"] = width_val

        if new_val:
          idx["new"] = True
        else:
          if "new" in idx:
            del idx["new"]

        # 2. Also update the individual JSON file on disk (inside 'save/')
        file_path = os.path.join(self.workspace_dir, file_name)
        if os.path.exists(file_path):
          try:
            with open(file_path, "r", encoding="utf-8") as f:
              file_data = json.load(f)

            if "info" not in file_data:
              file_data["info"] = {}

            file_data["info"]["animated"] = anim_val
            file_data["info"]["colored"] = color_val
            file_data["info"]["width edit"] = width_val

            if new_val:
              file_data["info"]["new"] = True
            else:
              if "new" in file_data["info"]:
                del file_data["info"]["new"]

            with open(file_path, "w", encoding="utf-8") as f:
              json.dump(file_data, f, indent=2)
            updated_count += 1
          except Exception as ex:
            print(f"Could not update individual file {file_name}: {ex}")

    # Save index file automatically upon batch apply
    self.save_index(silent=True)

    # Clear selections and reset form options back to base selection
    self.clear_selection()
    self.var_animated.set(False)
    self.var_colored.set(False)
    self.var_width_edit.set(False)
    self.var_new.set(False)

    self.status_var.set(
        f"Successfully updated {updated_count} individual file(s) and"
        " svgs.json index."
    )
    messagebox.showinfo(
        "Success",
        f"Successfully updated {updated_count} files and svgs.json! Selections"
        " and form properties have been reset.",
    )

  def save_index(self, silent=False):
    if not self.index_file_path:
      if not silent:
        messagebox.showwarning("Warning", "No active workspace loaded.")
      return

    try:
      with open(self.index_file_path, "w", encoding="utf-8") as f:
        json.dump(self.svgs_index_data, f, indent=2)
      if not silent:
        self.status_var.set(
            f"Successfully saved index to {self.index_file_path}"
        )
        messagebox.showinfo("Saved", "svgs.json index saved successfully!")
    except Exception as e:
      if not silent:
        messagebox.showerror("Error", f"Failed to save svgs.json:\n{e}")

  def on_item_double_click(self, event):
    item = self.tree.identify_row(event.y)
    if not item:
      return
    values = self.tree.item(item, "values")
    file_name = values[1]
    self.open_file_editor(file_name)

  def open_file_editor(self, file_name):
    file_path = os.path.join(self.workspace_dir, file_name)
    if not os.path.exists(file_path):
      messagebox.showerror("Error", f"File not found on disk: {file_name}")
      return

    editor_win = tk.Toplevel(self.root)
    editor_win.title(f"Individual File Editor: save/{file_name}")
    editor_win.geometry("750x550")

    try:
      with open(file_path, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    except Exception as e:
      messagebox.showerror("Error", f"Could not parse JSON for {file_name}:\n{e}")
      editor_win.destroy()
      return

    info = file_data.get("info", {})
    icons = file_data.get("icons", {})

    notebook = ttk.Notebook(editor_win)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Tab 1: Info Metadata
    tab_info = ttk.Frame(notebook, padding=10)
    notebook.add(tab_info, text="Info Metadata")

    entries = {}
    row = 0
    for key, val in info.items():
      if isinstance(val, (str, int, float, bool)):
        ttk.Label(tab_info, text=f"{key}:").grid(
            row=row, column=0, sticky="w", pady=5, padx=5
        )
        ent = ttk.Entry(tab_info, width=50)
        ent.insert(0, str(val))
        ent.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        entries[key] = ent
        row += 1

    # Tab 2: Icons View
    tab_icons = ttk.Frame(notebook, padding=10)
    notebook.add(tab_icons, text=f"Icons List ({len(icons)})")

    icon_tree = ttk.Treeview(
        tab_icons, columns=("key", "category", "version"), show="headings"
    )
    icon_tree.heading("key", text="Icon Name / Key")
    icon_tree.heading("category", text="Category")
    icon_tree.heading("version", text="Version")
    icon_tree.column("key", width=250)
    icon_tree.column("category", width=150)
    icon_tree.column("version", width=100)

    icon_scroll = ttk.Scrollbar(
        tab_icons, orient="vertical", command=icon_tree.yview
    )
    icon_tree.configure(yscrollcommand=icon_scroll.set)

    icon_tree.pack(side="left", fill="both", expand=True, pady=5)
    icon_scroll.pack(side="right", fill="y", pady=5)

    for ic_key, ic_val in icons.items():
      icat = ic_val.get("category", "")
      iver = ic_val.get("version", "")
      icon_tree.insert("", "end", values=(ic_key, icat, iver))

    def save_individual_file():
      for k, ent in entries.items():
        val = ent.get()
        if isinstance(info[k], bool):
          info[k] = val.lower() == "true"
        elif isinstance(info[k], int):
          try:
            info[k] = int(val)
          except ValueError:
            pass
        else:
          info[k] = val

      file_data["info"] = info
      try:
        with open(file_path, "w", encoding="utf-8") as f:
          json.dump(file_data, f, indent=2)
        messagebox.showinfo("Success", f"Successfully saved {file_name}!")
        editor_win.destroy()
      except Exception as e:
        messagebox.showerror("Error", f"Failed to save file:\n{e}")

    btn_frame = ttk.Frame(editor_win)
    btn_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(
        btn_frame, text="Save File Changes", command=save_individual_file
    ).pack(side="right", padx=5)
    ttk.Button(
        btn_frame, text="Cancel", command=editor_win.destroy
    ).pack(side="right", padx=5)


if __name__ == "__main__":
  root = tk.Tk()
  app = SVGIndexManagerApp(root)
  root.mainloop()