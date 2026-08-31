import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import markdown
from tkhtmlview import HTMLLabel

# Set appearance mode and color theme for CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OpenCode - LLM Text Transformer")
        self.geometry("1100\\x700")

        # State variables
        self.current_work_dir = os.getcwd()
        self.current_file_path = None
        self.current_file_name = "Untitled"
        self.file_list_items = []
        self.is_rendered_markdown = False

        # Configure root grid weight
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create PanedWindow for resizable sections (Draggable Separators A & B)
        # Using horizontal PanedWindow
        self.paned_window = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            bd=0,
            bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#d1d1d1"
        )
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # 1. Left-side panel frame
        self.left_frame = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color="transparent")
        self.paned_window.add(self.left_frame, minsize=200)

        # 2. Raw-Text section frame
        self.raw_frame = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color="transparent")
        self.paned_window.add(self.raw_frame, minsize=250)

        # 3. Processed-Text section frame
        self.processed_frame = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color="transparent")
        self.paned_window.add(self.processed_frame, minsize=250)

        # Build individual sections
        self.build_left_panel()
        self.build_raw_panel()
        self.build_processed_panel()

        # Load initial file list from current directory
        self.refresh_file_list()

    def build_left_panel(self):
        self.left_frame.grid_rowconfigure(2, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # --- Action Panel (Upper Section) ---
        action_panel = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        action_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        action_panel.grid_columnconfigure(1, weight=1)

        # Gear Icon / Settings Button
        self.settings_btn = ctk.CTkButton(
            action_panel,
            text="⚙",
            width=36,
            height=36,
            font=("Arial", 16),
            command=self.open_settings
        )
        self.settings_btn.grid(row=0, column=0, padx=(0, 5), sticky="w")

        # Directory Selector Bar
        self.dir_btn = ctk.CTkButton(
            action_panel,
            text=self.current_work_dir,
            anchor="w",
            command=self.select_directory
        )
        self.dir_btn.grid(row=0, column=1, sticky="ew", padx=(0, 0))

        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_file_list())
        self.search_entry = ctk.CTkEntry(
            self.left_frame,
            placeholder_text="Search files...",
            textvariable=self.search_var
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # --- Files List Section ---
        self.files_scroll_frame = ctk.CTkScrollableFrame(self.left_frame, label_text="Files")
        self.files_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.files_scroll_frame.grid_columnconfigure(0, weight=1)

    def build_raw_panel(self):
        self.raw_frame.grid_rowconfigure(1, weight=1)
        self.raw_frame.grid_columnconfigure(0, weight=1)

        # --- Header ---
        raw_header = ctk.CTkFrame(self.raw_frame, height=45, fg_color="transparent")
        raw_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        raw_header.grid_columnconfigure(1, weight=1)

        # Save Button (Left of filename)
        raw_save_btn = ctk.CTkButton(raw_header, text="Save", width=60, command=self.save_raw_file)
        raw_save_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")

        # Current File Name Label
        self.raw_filename_lbl = ctk.CTkLabel(raw_header, text=self.current_file_name, font=("Arial", 14, "bold"))
        self.raw_filename_lbl.grid(row=0, column=1, sticky="w")

        # Process Button (Right of filename)
        raw_process_btn = ctk.CTkButton(raw_header, text="Process", width=70, fg_color="#28a745", hover_color="#218838", command=self.process_text)
        raw_process_btn.grid(row=0, column=2, padx=(10, 0), sticky="e")

        # --- Body ---
        self.raw_textbox = ctk.CTkTextbox(self.raw_frame, undo=True)
        self.raw_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def build_processed_panel(self):
        self.processed_frame.grid_rowconfigure(1, weight=1)
        self.processed_frame.grid_columnconfigure(0, weight=1)

        # --- Header ---
        proc_header = ctk.CTkFrame(self.processed_frame, height=45, fg_color="transparent")
        proc_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        proc_header.grid_columnconfigure(1, weight=1)

        # Save Button
        proc_save_btn = ctk.CTkButton(proc_header, text="Save", width=60, command=self.save_processed_file)
        proc_save_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")

        # Current File Name Label
        self.proc_filename_lbl = ctk.CTkLabel(proc_header, text=self.current_file_name, font=("Arial", 14, "bold"))
        self.proc_filename_lbl.grid(row=0, column=1, sticky="w")

        # Toggle Button (Right of filename)
        self.toggle_btn = ctk.CTkButton(proc_header, text="Toggle: Markdown", width=130, command=self.toggle_markdown_view)
        self.toggle_btn.grid(row=0, column=2, padx=(10, 0), sticky="e")

        # --- Body Container (supports switching between CTkTextbox and HTMLLabel) ---
        self.processed_body_container = ctk.CTkFrame(self.processed_frame, fg_color="transparent")
        self.processed_body_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.processed_body_container.grid_rowconfigure(0, weight=1)
        self.processed_body_container.grid_columnconfigure(0, weight=1)

        # Pure Text View (CTkTextbox)
        self.processed_textbox = ctk.CTkTextbox(self.processed_body_container, undo=True)
        self.processed_textbox.grid(row=0, column=0, sticky="nsew")

        # Rendered Markdown View (HTMLLabel inside a frame or directly)
        # We use a CTkFrame as wrapper for HTMLLabel to control styling/background cleanly in CustomTkinter
        self.html_wrapper = ctk.CTkFrame(self.processed_body_container, fg_color="white")
        self.html_label = HTMLLabel(self.html_wrapper, html="<h3>Processed Markdown Output will appear here...</h3>")
        self.html_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initially hide html wrapper, show textbox
        self.html_wrapper.grid_remove()

        # --- Prompt Section ---
        prompt_frame = ctk.CTkFrame(self.processed_frame, fg_color="transparent", height=50)
        prompt_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        prompt_frame.grid_columnconfigure(0, weight=1)

        self.prompt_entry = ctk.CTkEntry(prompt_frame, placeholder_text="Ask LLM additional instructions...")
        self.prompt_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.prompt_entry.bind("<Return>", lambda event: self.send_prompt())

        # Circular Send Button with right-pointing arrow
        self.send_btn = ctk.CTkButton(
            prompt_frame,
            text="➔",
            width=36,
            height=36,
            corner_radius=18,
            font=("Arial", 16, "bold"),
            command=self.send_prompt
        )
        self.send_btn.grid(row=0, column=1, sticky="e")

    def select_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.current_work_dir)
        if selected_dir:
            self.current_work_dir = selected_dir
            self.dir_btn.configure(text=self.current_work_dir)
            self.refresh_file_list()

    def refresh_file_list(self):
        # Clear existing file list buttons
        for widget in self.files_scroll_frame.winfo_children():
            widget.destroy()

        self.file_list_items = []
        try:
            if os.path.exists(self.current_work_dir):
                for item in sorted(os.listdir(self.current_work_dir)):
                    full_path = os.path.join(self.current_work_dir, item)
                    if os.path.isfile(full_path):
                        self.file_list_items.append(item)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read directory: {e}")

        self.populate_file_buttons(self.file_list_items)

    def populate_file_buttons(self, files):
        for widget in self.files_scroll_frame.winfo_children():
            widget.destroy()

        for filename in files:
            btn = ctk.CTkButton(
                self.files_scroll_frame,
                text=filename,
                anchor="w",
                fg_color="transparent",
                text_color=("black", "white"),
                hover_color=("gray75", "gray25"),
                command=lambda f=filename: self.open_file(f)
            )
            btn.pack(fill="x", padx=2, pady=2)

    def filter_file_list(self):
        query = self.search_var.get().lower()
        filtered = [f for f in self.file_list_items if query in f.lower()]
        self.populate_file_buttons(filtered)

    def open_file(self, filename):
        self.current_file_name = filename
        self.current_file_path = os.path.join(self.current_work_dir, filename)
        
        self.raw_filename_lbl.configure(text=self.current_file_name)
        self.proc_filename_lbl.configure(text=self.current_file_name)

        try:
            with open(self.current_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.raw_textbox.delete("1.0", "end")
            self.raw_textbox.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file {filename}: {e}")

    def save_raw_file(self):
        if not self.current_file_path:
            file_path = filedialog.asksaveasfilename(initialdir=self.current_work_dir, defaultextension=".txt")
            if not file_path:
                return
            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)
            self.raw_filename_lbl.configure(text=self.current_file_name)
            self.proc_filename_lbl.configure(text=self.current_file_name)

        try:
            content = self.raw_textbox.get("1.0", "end-1c")
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"File saved successfully: {self.current_file_name}")
            self.refresh_file_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def save_processed_file(self):
        file_path = filedialog.asksaveasfilename(initialdir=self.current_work_dir, defaultextension=".md")
        if not file_path:
            return
        try:
            content = self.processed_textbox.get("1.0", "end-1c")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Processed output saved to {os.path.basename(file_path)}")
            self.refresh_file_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save processed output: {e}")

    def toggle_markdown_view(self):
        self.is_rendered_markdown = not self.is_rendered_markdown
        if self.is_rendered_markdown:
            self.toggle_btn.configure(text="Toggle: Plain Text")
            # Convert text to markdown html
            text_content = self.processed_textbox.get("1.0", "end-1c")
            html_content = markdown.markdown(text_content)
            self.html_label.set_html(html_content)
            
            # Hide textbox, show html wrapper
            self.processed_textbox.grid_remove()
            self.html_wrapper.grid(row=0, column=0, sticky="nsew")
        else:
            self.toggle_btn.configure(text="Toggle: Markdown")
            # Hide html wrapper, show textbox
            self.html_wrapper.grid_remove()
            self.processed_textbox.grid(row=0, column=0, sticky="nsew")

    def process_text(self):
        # Placeholder / Integration stub for LLM processing
        raw_text = self.raw_textbox.get("1.0", "end-1c")
        if not raw_text.strip():
            messagebox.showwarning("Warning", "Raw text is empty.")
            return

        # Simulate async background task or direct update
        self.processed_textbox.delete("1.0", "end")
        self.processed_textbox.insert("1.0", f"# Processed Output\\n\\nHere is the transformed version of your text:\\n\\n> {raw_text}\\n\\n*(Stubbed response - connect lm_client here)*")
        
        if self.is_rendered_markdown:
            # Refresh markdown view if active
            text_content = self.processed_textbox.get("1.0", "end-1c")
            self.html_label.set_html(markdown.markdown(text_content))

    def send_prompt(self):
        prompt_text = self.prompt_entry.get()
        if not prompt_text.strip():
            return
        
        # Append prompt query to processed textbox as additional instruction stub
        current_content = self.processed_textbox.get("1.0", "end-1c")
        new_content = current_content + f"\\n\\n**User Prompt:** {prompt_text}\\n*LLM response to prompt...*"
        self.processed_textbox.delete("1.0", "end")
        self.processed_textbox.insert("1.0", new_content)
        self.prompt_entry.delete(0, "end")

        if self.is_rendered_markdown:
            self.html_label.set_html(markdown.markdown(self.processed_textbox.get("1.0", "end-1c")))

    def open_settings(self):
        # Settings window popup
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("400x300")
        settings_win.grab_set()

        lbl = ctk.CTkLabel(settings_win, text="Application Settings", font=("Arial", 16, "bold"))
        lbl.pack(padx=20, pady=20)

        theme_lbl = ctk.CTkLabel(settings_win, text="Appearance Mode:")
        theme_lbl.pack(padx=20, anchor="w")

        theme_menu = ctk.CTkOptionMenu(
            settings_win,
            values=["System", "Light", "Dark"],
            command=lambda mode: ctk.set_appearance_mode(mode)
        )
        theme_menu.pack(padx=20, pady=10, anchor="w")
        theme_menu.set(ctk.get_appearance_mode())

if __name__ == "__main__":
    app = App()
    app.mainloop()
