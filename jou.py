import customtkinter as ctk
import sqlite3
from datetime import datetime
import json
from tkinter import filedialog, messagebox

# Set global appearance and default theme
ctk.set_appearance_mode("Dark")  # Options: "Dark", "Light", "System"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class ModernJournalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Journal App")
        self.geometry("950x650")
        self.minsize(800, 500)

        # Database Setup
        self.conn = sqlite3.connect("journal_modern.db")
        self.cursor = self.conn.cursor()
        self.create_table()

        self.selected_entry_id = None

        # Build Layout
        self.setup_ui()
        self.load_entries()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                date_time TEXT,
                content TEXT,
                last_modified TEXT
            )
        """)
        self.conn.commit()

    def setup_ui(self):
        # Configure Grid Layout (2 Columns: Sidebar & Main Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------- LEFT SIDEBAR ------------------- #
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # Search Box
        self.search_entry = ctk.CTkEntry(
            self.sidebar, placeholder_text="Search entries..."
        )
        self.search_entry.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_entries())

        # New Entry Button
        self.btn_new = ctk.CTkButton(
            self.sidebar,
            text="+ New Entry",
            fg_color="#0d6efd",
            hover_color="#0b5ed7",
            command=self.clear_fields,
        )
        self.btn_new.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # Section Header
        self.lbl_entries = ctk.CTkLabel(
            self.sidebar,
            text="All Entries",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.lbl_entries.grid(row=2, column=0, padx=15, pady=(10, 5), sticky="w")

        # Entries Scrollable List
        self.scrollable_entries = ctk.CTkScrollableFrame(self.sidebar)
        self.scrollable_entries.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        # Theme Selector Toggle
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar, text="Dark Mode", command=self.toggle_theme
        )
        self.theme_switch.grid(row=4, column=0, padx=15, pady=15, sticky="w")
        self.theme_switch.select()

        # ------------------- RIGHT MAIN AREA ------------------- #
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=15)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Title Section
        ctk.CTkLabel(
            self.main_frame, text="Title", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.title_entry = ctk.CTkEntry(
            self.main_frame, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Date & Time Section
        ctk.CTkLabel(
            self.main_frame,
            text="Date & Time",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.date_entry = ctk.CTkEntry(self.main_frame)
        self.date_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Content Text Box
        self.content_text = ctk.CTkTextbox(
            self.main_frame, font=ctk.CTkFont(size=13), wrap="word"
        )
        self.content_text.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.content_text.bind("<KeyRelease>", self.update_stats)

        # Action Buttons Bar
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        self.btn_save = ctk.CTkButton(
            self.btn_frame,
            text="Save Entry",
            fg_color="#0d6efd",
            hover_color="#0b5ed7",
            width=100,
            command=self.save_entry,
        )
        self.btn_save.pack(side="left", padx=(0, 5))

        self.btn_update = ctk.CTkButton(
            self.btn_frame,
            text="Update Entry",
            fg_color="#198754",
            hover_color="#157347",
            width=100,
            command=self.update_entry,
        )
        self.btn_update.pack(side="left", padx=5)

        self.btn_delete = ctk.CTkButton(
            self.btn_frame,
            text="Delete Entry",
            fg_color="#dc3545",
            hover_color="#bb2d3b",
            width=100,
            command=self.delete_entry,
        )
        self.btn_delete.pack(side="left", padx=5)

        self.btn_restore = ctk.CTkButton(
            self.btn_frame,
            text="Restore",
            fg_color="#6c757d",
            hover_color="#5c636a",
            width=80,
            command=self.restore_backup,
        )
        self.btn_restore.pack(side="right", padx=(5, 0))

        self.btn_backup = ctk.CTkButton(
            self.btn_frame,
            text="Backup",
            fg_color="#6c757d",
            hover_color="#5c636a",
            width=80,
            command=self.backup_data,
        )
        self.btn_backup.pack(side="right", padx=5)

        # Statistics Box
        self.stats_frame = ctk.CTkFrame(self.main_frame, corner_radius=6)
        self.stats_frame.grid(row=6, column=0, sticky="ew")

        self.lbl_stats = ctk.CTkLabel(
            self.stats_frame,
            text="0 words | 0 characters",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self.lbl_stats.pack(anchor="w", padx=10, pady=(4, 0))

        self.lbl_last_mod = ctk.CTkLabel(
            self.stats_frame,
            text="Last Modified: N/A",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
        )
        self.lbl_last_mod.pack(anchor="w", padx=10, pady=(0, 4))

        self.clear_fields()

    # ------------------- LOGIC & FUNCTIONS ------------------- #
    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def clear_fields(self):
        self.selected_entry_id = None
        self.title_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%d %b %Y %I:%M %p"))
        self.content_text.delete("1.0", "end")
        self.update_stats()

    def load_entries(self):
        for widget in self.scrollable_entries.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip()
        if query:
            self.cursor.execute(
                "SELECT id, title FROM entries WHERE title LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
            )
        else:
            self.cursor.execute("SELECT id, title FROM entries ORDER BY id DESC")

        entries = self.cursor.fetchall()
        for entry_id, title in entries:
            btn_title = title if title else "Untitled Entry"
            btn = ctk.CTkButton(
                self.scrollable_entries,
                text=btn_title,
                anchor="w",
                fg_color="transparent",
                text_color=("black", "white"),
                hover_color=("gray85", "gray25"),
                command=lambda eid=entry_id: self.select_entry(eid),
            )
            btn.pack(fill="x", pady=2)

    def select_entry(self, entry_id):
        self.selected_entry_id = entry_id
        self.cursor.execute(
            "SELECT title, date_time, content, last_modified FROM entries WHERE id = ?",
            (entry_id,),
        )
        row = self.cursor.fetchone()
        if row:
            title, date_time, content, last_modified = row
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, title)
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date_time)
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", content)
            self.lbl_last_mod.configure(text=f"Last Modified: {last_modified}")
            self.update_stats()

    def save_entry(self):
        title = self.title_entry.get().strip() or "Untitled Entry"
        date_time = self.date_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c")
        last_mod = datetime.now().strftime("%d %b %Y %I:%M %p")

        self.cursor.execute(
            "INSERT INTO entries (title, date_time, content, last_modified) VALUES (?, ?, ?, ?)",
            (title, date_time, content, last_mod),
        )
        self.conn.commit()
        messagebox.showinfo("Saved", "Entry saved successfully!")
        self.load_entries()
        self.clear_fields()

    def update_entry(self):
        if not self.selected_entry_id:
            messagebox.showwarning("Warning", "Select an entry to update.")
            return

        title = self.title_entry.get().strip() or "Untitled Entry"
        date_time = self.date_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c")
        last_mod = datetime.now().strftime("%d %b %Y %I:%M %p")

        self.cursor.execute(
            "UPDATE entries SET title = ?, date_time = ?, content = ?, last_modified = ? WHERE id = ?",
            (title, date_time, content, last_mod, self.selected_entry_id),
        )
        self.conn.commit()
        messagebox.showinfo("Updated", "Entry updated successfully!")
        self.load_entries()

    def delete_entry(self):
        if not self.selected_entry_id:
            messagebox.showwarning("Warning", "Select an entry to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
            self.cursor.execute(
                "DELETE FROM entries WHERE id = ?", (self.selected_entry_id,)
            )
            self.conn.commit()
            self.load_entries()
            self.clear_fields()

    def backup_data(self):
        self.cursor.execute(
            "SELECT title, date_time, content, last_modified FROM entries"
        )
        data = self.cursor.fetchall()
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON Files", "*.json")]
        )
        if path:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Backup", "Data backed up successfully!")

    def restore_backup(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                for item in data:
                    self.cursor.execute(
                        "INSERT INTO entries (title, date_time, content, last_modified) VALUES (?, ?, ?, ?)",
                        item,
                    )
                self.conn.commit()
                self.load_entries()
                messagebox.showinfo("Restore", "Data restored successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore data: {e}")

    def update_stats(self, event=None):
        text = self.content_text.get("1.0", "end-1c")
        words = len(text.split())
        chars = len(text)
        self.lbl_stats.configure(text=f"{words} words | {chars} characters")


if __name__ == "__main__":
    app = ModernJournalApp()
    app.mainloop()
