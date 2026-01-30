

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import threading
import time
import logging
import datetime
from typing import Optional

from core.scanner import Scanner
from core.parser import Parser
from core.smart_extractor import SmartExtractor
from core.exporter import Exporter
from core.duplicate_handler import DuplicateHandler
from core.task_manager import TaskManager, TaskStatus

class ScoutApp:
    
    
    def __init__(self, root):
        self.root = root
        self.root.title("Scout — Explore your files, uncover meaning")
        self.root.geometry("1000x700")
        
        # State variables (must be set before initializing extractor)
        self.selected_directory: Optional[str] = None
        self.selected_file: Optional[str] = None
        self.is_scanning = False
        self.cancel_scan = False  # Flag to cancel ongoing scan
        self.current_results = {}
        self.log_expanded = False  # Log view collapsed by default
        self.task_panel_expanded = True  # Task panel expanded by default
        self.use_textblob = True  # TextBlob enhancement enabled by default
        
        # Duplicate scanning state
        self.is_scanning_duplicates = False
        self.duplicate_threshold = 5  # Image similarity threshold
        self.duplicate_file_type = "Images"  # File type to scan
        self.dry_run_mode = True  # Default to dry run (preview mode)
        self.move_to_trash = True  # Default to move to trash instead of delete
        self.duplicate_preview_data = []  # Store preview data
        
        # Mode state
        self.current_mode = "abbreviations"  # 'abbreviations' or 'duplicates'
        
        # Task management
        self.task_manager = TaskManager(max_concurrent=3)
        self.task_manager.start()
        self.active_tasks = {}  # task_id -> extractor instance
        self.task_refresh_timer = None
        
        # Setup logging
        self._setup_logging()
        
        # Initialize core components
        self.scanner = Scanner()
        self.parser = Parser()
        self.extractor = SmartExtractor(prefer_llm=False, use_textblob=self.use_textblob)
        self.exporter = Exporter()
        
        self._log("Scout initialized with fast pattern matching", "INFO")
        
        # Setup UI
        self._setup_ui()
        
        # Center window on screen
        self._center_window()
        
        # Check and offer to install AI features
        self.root.after(500, self._check_ai_features)
    
    def _check_ai_features(self):
        """Check if AI features are available and offer to install"""
        try:
            import spacy
            try:
                spacy.load("en_core_web_sm")
                return  # Already installed
            except OSError:
                pass  # Model not found, offer to install
        except ImportError:
            pass  # spaCy not installed
        
        # Show installation dialog
        response = messagebox.askyesno(
            "Install AI Features?",
            "Scout can use advanced AI features for better accuracy:\n\n"
            "• spaCy NER filtering (90% precision)\n"
            "• BERT semantic matching (95% precision)\n\n"
            "This will download ~50MB of models.\n\n"
            "Install now? (Recommended)",
            icon='question'
        )
        
        if response:
            self._install_spacy_model()
    
    def _install_spacy_model(self):
        """Install spaCy model in background"""
        # Create progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Installing AI Features")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text="Downloading spaCy language model...",
            font=("Helvetica", 11)
        ).pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            mode='indeterminate',
            bootstyle="success-striped"
        )
        progress_bar.pack(fill="x", padx=30)
        progress_bar.start(10)
        
        status_label = ttk.Label(
            progress_window,
            text="Please wait...",
            font=("Helvetica", 9),
            foreground="gray"
        )
        status_label.pack(pady=10)
        
        def install():
            try:
                import subprocess
                import sys
                
                # Update status
                self.root.after(0, lambda: status_label.config(text="Installing spaCy..."))
                
                # Install spacy if not installed
                try:
                    import spacy
                except ImportError:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                
                # Download model
                self.root.after(0, lambda: status_label.config(text="Downloading language model (~50MB)..."))
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                
                # Success
                self.root.after(0, lambda: progress_bar.stop())
                self.root.after(0, lambda: progress_window.destroy())
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    "AI features installed successfully!\n\nRestart Scout to use advanced extraction features."
                ))
                self._log("AI features installed successfully", "INFO")
                
            except Exception as e:
                self.root.after(0, lambda: progress_bar.stop())
                self.root.after(0, lambda: progress_window.destroy())
                self.root.after(0, lambda: messagebox.showerror(
                    "Installation Failed",
                    f"Failed to install AI features:\n\n{str(e)}\n\n"
                    "You can install manually:\n"
                    "pip install spacy\n"
                    "python -m spacy download en_core_web_sm"
                ))
                self._log(f"AI feature installation failed: {e}", "ERROR")
        
        # Run installation in thread
        thread = threading.Thread(target=install, daemon=True)
        thread.start()
    
    def _setup_logging(self):
        
        # Create custom logging handler that writes to GUI
        self.log_messages = []
        
    def _log(self, message: str, level: str = "INFO"):
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {level}: {message}"
        self.log_messages.append(formatted_msg)
        
        # Update log view if it exists
        if hasattr(self, 'log_text'):
            self.log_text.configure(state='normal')
            self.log_text.insert('end', formatted_msg + '\n')
            self.log_text.see('end')  # Auto-scroll to bottom
            self.log_text.configure(state='disabled')
    
    def _setup_ui(self):
        
        # Main container with padding
        main_container = ttk.Frame(self.root, padding=(15, 15, 15, 15))
        main_container.pack(fill='both', expand=True)
        
        # Title section
        self._create_header(main_container)
        
        # Control panel
        self._create_control_panel(main_container)
        
        # Progress section
        self._create_progress_section(main_container)
        
        # Results section
        self._create_results_section(main_container)
        
        # Log view section (expandable)
        self._create_log_section(main_container)
        
        # Status bar
        self._create_status_bar(main_container)
        
        # Initialize to abbreviations mode
        self._switch_mode("abbreviations")
    
    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Left side: Title
        title_container = ttk.Frame(header_frame)
        title_container.pack(side="left")
        
        title_label = ttk.Label(
            title_container,
            text="🔍 Scout",
            font=("Helvetica", 24, "bold"),
            bootstyle="primary"
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            title_container,
            text="Intelligent File Analysis & Management",
            font=("Helvetica", 10),
            bootstyle="secondary"
        )
        subtitle_label.pack(anchor="w")
        
        # Right side: Mode Switcher
        mode_container = ttk.Frame(header_frame)
        mode_container.pack(side="right", padx=(20, 0))
        
        ttk.Label(
            mode_container,
            text="Mode:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=(0, 10))
        
        # Mode selector buttons
        mode_frame = ttk.Frame(mode_container)
        mode_frame.pack(side="left")
        
        self.abbrev_mode_btn = ttk.Button(
            mode_frame,
            text="📝 Abbreviations",
            command=lambda: self._switch_mode("abbreviations"),
            bootstyle="primary",
            width=18
        )
        self.abbrev_mode_btn.pack(side="left", padx=(0, 5))
        
        self.dedupe_mode_btn = ttk.Button(
            mode_frame,
            text="🗂️ Deduplicator",
            command=lambda: self._switch_mode("duplicates"),
            bootstyle="secondary-outline",
            width=18
        )
        self.dedupe_mode_btn.pack(side="left")
    
    def _create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(
            parent,
            text="Controls",
        )
        control_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        inner_frame = ttk.Frame(control_frame)
        inner_frame.pack(fill='x', padx=15, pady=15)
        
        # Directory selection (common to both modes)
        dir_frame = ttk.Frame(inner_frame)
        dir_frame.pack(fill='x', pady=(0, 15))
        
        self.dir_label = ttk.Label(
            dir_frame,
            text="No folder selected",
            font=("Helvetica", 10),
            bootstyle="secondary"
        )
        self.dir_label.pack(side='left', fill='x', expand=True)
        
        select_btn = ttk.Button(
            dir_frame,
            text="📁 Select Folder",
            command=self._select_directory,
            bootstyle="success",
            width=15
        )
        select_btn.pack(side="right", padx=(10, 0))
        
        select_file_btn = ttk.Button(
            dir_frame,
            text="📄 Select File",
            command=self._select_file,
            bootstyle="success-outline",
            width=15
        )
        select_file_btn.pack(side="right", padx=(10, 0))
        
        # === ABBREVIATION MODE CONTROLS ===
        self.abbrev_controls = ttk.Frame(inner_frame)
        self.abbrev_controls.pack(fill='x')
        
        # Settings button
        settings_frame = ttk.Frame(self.abbrev_controls)
        settings_frame.pack(fill='x', pady=(0, 10))
        
        settings_btn = ttk.Button(
            settings_frame,
            text="⚙️ Extraction Settings",
            command=self._show_settings_dialog,
            bootstyle="info-outline",
            width=20
        )
        settings_btn.pack(side="left")
        
        # Action buttons for abbreviations
        abbrev_button_frame = ttk.Frame(self.abbrev_controls)
        abbrev_button_frame.pack(fill="x")
        
        self.scan_btn = ttk.Button(
            abbrev_button_frame,
            text="🔍 Scan Now",
            command=self._start_scan_as_task,
            bootstyle="success",
            width=15
        )
        self.scan_btn.pack(side="left", padx=(0, 10))
        self.scan_btn.configure(state="disabled")
        
        self.view_tasks_btn = ttk.Button(
            abbrev_button_frame,
            text="📋 Active Tasks",
            command=self._show_active_tasks,
            bootstyle="primary-outline",
            width=15
        )
        self.view_tasks_btn.pack(side="left", padx=(0, 10))
        
        self.export_btn = ttk.Button(
            abbrev_button_frame,
            text="💾 Export Report",
            command=self._show_export_menu,
            bootstyle="info-outline",
            width=20
        )
        self.export_btn.pack(side="left", padx=(0, 10))
        self.export_btn.configure(state="disabled")
        
        self.clear_btn = ttk.Button(
            abbrev_button_frame,
            text="🗑️ Clear Results",
            command=self._clear_results,
            bootstyle="secondary-outline",
            width=18
        )
        self.clear_btn.pack(side="left")
        self.clear_btn.configure(state="disabled")
        
        # === DUPLICATE MODE CONTROLS ===
        self.dedupe_controls = ttk.Frame(inner_frame)
        
        # Duplicate settings row
        dedupe_settings_frame = ttk.Frame(self.dedupe_controls)
        dedupe_settings_frame.pack(fill='x', pady=(0, 10))
        
        # File type selector
        ttk.Label(
            dedupe_settings_frame,
            text="File Type:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.file_type_var = tk.StringVar(value=self.duplicate_file_type)
        file_type_combo = ttk.Combobox(
            dedupe_settings_frame,
            textvariable=self.file_type_var,
            values=["Images", "Documents", "Videos", "All Files"],
            state="readonly",
            width=15
        )
        file_type_combo.pack(side="left", padx=(0, 20))
        file_type_combo.bind('<<ComboboxSelected>>', lambda e: self._update_duplicate_settings())
        
        # Threshold slider
        ttk.Label(
            dedupe_settings_frame,
            text="Similarity:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.threshold_var = tk.IntVar(value=self.duplicate_threshold)
        threshold_scale = ttk.Scale(
            dedupe_settings_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            bootstyle="warning",
            length=150
        )
        threshold_scale.pack(side="left", padx=(0, 10))
        
        self.threshold_label = ttk.Label(
            dedupe_settings_frame,
            text=str(self.duplicate_threshold),
            font=("Helvetica", 10, "bold"),
            width=2
        )
        self.threshold_label.pack(side="left")
        
        self.threshold_var.trace('w', self._update_threshold_label)
        
        ttk.Label(
            dedupe_settings_frame,
            text="(lower = stricter)",
            font=("Helvetica", 8),
            bootstyle="secondary"
        ).pack(side="left", padx=(5, 0))
        
        # Options row (checkboxes)
        dedupe_options_frame = ttk.Frame(self.dedupe_controls)
        dedupe_options_frame.pack(fill='x', pady=(0, 10))
        
        self.dry_run_var = tk.BooleanVar(value=self.dry_run_mode)
        dry_run_check = ttk.Checkbutton(
            dedupe_options_frame,
            text="🔍 Preview Mode (don't delete)",
            variable=self.dry_run_var,
            bootstyle="info-round-toggle",
            command=self._update_duplicate_settings
        )
        dry_run_check.pack(side="left", padx=(0, 20))
        
        self.move_to_trash_var = tk.BooleanVar(value=self.move_to_trash)
        trash_check = ttk.Checkbutton(
            dedupe_options_frame,
            text="🗑️ Move to Trash (not permanent delete)",
            variable=self.move_to_trash_var,
            bootstyle="success-round-toggle",
            command=self._update_duplicate_settings
        )
        trash_check.pack(side="left")
        
        # Action buttons for deduplication - Row 1 (Primary Actions)
        dedupe_button_frame = ttk.Frame(self.dedupe_controls)
        dedupe_button_frame.pack(fill="x", pady=(0, 5))
        
        self.scan_duplicates_btn = ttk.Button(
            dedupe_button_frame,
            text="🔎 Preview Duplicates",
            command=self._start_duplicate_scan,
            bootstyle="info",
            width=25
        )
        self.scan_duplicates_btn.pack(side="left", padx=(0, 10))
        self.scan_duplicates_btn.configure(state="disabled")
        
        self.delete_duplicates_btn = ttk.Button(
            dedupe_button_frame,
            text="🗑️ Delete Duplicates",
            command=self._confirm_and_delete_duplicates,
            bootstyle="danger",
            width=25
        )
        self.delete_duplicates_btn.pack(side="left", padx=(0, 10))
        self.delete_duplicates_btn.configure(state="disabled")
        
        self.copy_results_btn = ttk.Button(
            dedupe_button_frame,
            text="📋 Copy Results",
            command=self._copy_duplicate_results,
            bootstyle="success-outline",
            width=20
        )
        self.copy_results_btn.pack(side="left")
        self.copy_results_btn.configure(state="disabled")
        
        # Row 2 (Utility Actions)
        dedupe_utility_frame = ttk.Frame(self.dedupe_controls)
        dedupe_utility_frame.pack(fill="x")
        
        self.compare_btn = ttk.Button(
            dedupe_utility_frame,
            text="👁️ Compare Selected",
            command=self._compare_selected_duplicates,
            bootstyle="secondary-outline",
            width=20
        )
        self.compare_btn.pack(side="left", padx=(0, 10))
        self.compare_btn.configure(state="disabled")
        
        self.open_folder_btn = ttk.Button(
            dedupe_utility_frame,
            text="📁 Open Folder",
            command=self._open_duplicate_folder,
            bootstyle="secondary-outline",
            width=20
        )
        self.open_folder_btn.pack(side="left")
        self.open_folder_btn.configure(state="disabled")
        
        # Common cancel button (for both modes)
        self.cancel_btn_scan = ttk.Button(
            inner_frame,
            text="⏹️ Cancel",
            command=self._cancel_scan,
            bootstyle="danger",
            width=15
        )
        # Will be shown when scanning starts
    
    def _create_progress_section(self, parent):
        
        self.progress_frame = ttk.Frame(parent)
        self.progress_frame.pack(fill="x", pady=(0, 15))
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="Ready to scan",
            font=("Helvetica", 9)
        )
        self.progress_label.pack(anchor="w", pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            bootstyle="success-striped"
        )
        self.progress_bar.pack(fill="x")
    
    def _create_results_section(self, parent):
        
        results_frame = ttk.LabelFrame(
            parent,
            text="Results",

        )
        results_frame.pack(fill="both", expand=True, padx=5)
        
        # Inner frame for padding
        inner_frame = ttk.Frame(results_frame)
        inner_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Search bar
        search_frame = ttk.Frame(inner_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            search_frame,
            text="Search:",
            font=("Helvetica", 10)
        ).pack(side="left", padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Helvetica", 10)
        )
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Statistics
        self.stats_label = ttk.Label(
            inner_frame,
            text="No results yet",
            font=("Helvetica", 9),
            bootstyle="secondary"
        )
        self.stats_label.pack(anchor="w", pady=(0, 10))
        
        # Results table with scrollbar
        table_frame = ttk.Frame(inner_frame)
        table_frame.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        # Treeview for abbreviation results
        abbrev_columns = ('abbreviation', 'definition', 'occurrences', 'files')
        self.results_tree = ttk.Treeview(
            table_frame,
            columns=abbrev_columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            bootstyle="info"
        )
        
        # Configure scrollbar
        scrollbar.config(command=self.results_tree.yview)
        
        # Define headings for abbreviations
        self.results_tree.heading('abbreviation', text='Abbreviation')
        self.results_tree.heading('definition', text='Definition')
        self.results_tree.heading('occurrences', text='Count')
        self.results_tree.heading('files', text='Files')
        
        # Define column widths
        self.results_tree.column('abbreviation', width=120, anchor="w")
        self.results_tree.column('definition', width=400, anchor="w")
        self.results_tree.column('occurrences', width=80, anchor=CENTER)
        self.results_tree.column('files', width=80, anchor=CENTER)
        
        self.results_tree.pack(fill="both", expand=True)
        
        # Treeview for duplicate results (will be shown/hidden based on mode)
        duplicate_columns = ('file_to_delete', 'file_to_keep', 'reason', 'size_saved', 'resolution')
        self.duplicates_tree = ttk.Treeview(
            table_frame,
            columns=duplicate_columns,
            show='tree headings',
            selectmode='extended',
            yscrollcommand=scrollbar.set,
            bootstyle="warning"
        )
        
        # Define headings for duplicates
        self.duplicates_tree.heading('#0', text='✓')
        self.duplicates_tree.heading('file_to_delete', text='File to Delete')
        self.duplicates_tree.heading('file_to_keep', text='File to Keep')
        self.duplicates_tree.heading('reason', text='Reason')
        self.duplicates_tree.heading('size_saved', text='Size Saved')
        self.duplicates_tree.heading('resolution', text='Resolution')
        
        # Define column widths
        self.duplicates_tree.column('#0', width=30, anchor=CENTER)
        self.duplicates_tree.column('file_to_delete', width=300, anchor="w")
        self.duplicates_tree.column('file_to_keep', width=300, anchor="w")
        self.duplicates_tree.column('reason', width=200, anchor="w")
        self.duplicates_tree.column('size_saved', width=100, anchor="e")
        self.duplicates_tree.column('resolution', width=150, anchor="w")
        
        # Alternating row colors
        self.results_tree.tag_configure('oddrow', background='#f0f0f0')
        self.results_tree.tag_configure('evenrow', background='#ffffff')
        self.duplicates_tree.tag_configure('oddrow', background='#fff3cd')
        self.duplicates_tree.tag_configure('evenrow', background='#ffffff')
        
        # Bind selection for duplicates tree
        self.duplicates_tree.bind('<<TreeviewSelect>>', self._on_duplicate_selected)
    
    def _create_log_section(self, parent):
        
        # Container for log section
        self.log_container = ttk.Frame(parent)
        self.log_container.pack(fill='both', pady=(0, 15))
        
        # Header with toggle button
        log_header = ttk.Frame(self.log_container)
        log_header.pack(fill='x')
        
        self.log_toggle_btn = ttk.Button(
            log_header,
            text="▶ Show Logs",
            command=self._toggle_log_view,
            bootstyle="secondary-outline",
            width=15
        )
        self.log_toggle_btn.pack(side='left')
        
        ttk.Label(
            log_header,
            text="View detailed processing logs",
            font=("Helvetica", 9),
            bootstyle="secondary"
        ).pack(side='left', padx=(10, 0))
        
        # Log view frame (initially hidden)
        self.log_view_frame = ttk.Frame(self.log_container)
        
        # Scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(
            self.log_view_frame,
            height=15,
            font=("Courier", 9),
            wrap='word',
            state='disabled',
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.log_text.pack(fill='both', expand=True, pady=(10, 0))
        
        # Populate with existing logs if any
        if self.log_messages:
            self.log_text.configure(state='normal')
            for msg in self.log_messages:
                self.log_text.insert('end', msg + '\n')
            self.log_text.configure(state='disabled')
    
    def _toggle_log_view(self):
        
        if self.log_expanded:
            # Collapse
            self.log_view_frame.pack_forget()
            self.log_toggle_btn.config(text="▶ Show Logs")
            self.log_expanded = False
            self._log("Log view collapsed", "INFO")
        else:
            # Expand
            self.log_view_frame.pack(fill='both', expand=True)
            self.log_toggle_btn.config(text="▼ Hide Logs")
            self.log_expanded = True
            self._log("Log view expanded", "INFO")
    
    def _create_status_bar(self, parent):
        
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(15, 0))
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Helvetica", 9),
            bootstyle="secondary"
        )
        self.status_label.pack(side="left")
    
    def _center_window(self):
        
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _select_directory(self):
        
        directory = filedialog.askdirectory(
            title="Select Folder to Scan",
            initialdir=str(Path.home())
        )
        
        if directory:
            self.selected_directory = directory
            self.selected_file = None
            # Truncate path if too long
            display_path = directory
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            
            self.dir_label.config(text=f"📁 {display_path}")
            self.scan_btn.configure(state="normal")
            self.scan_duplicates_btn.configure(state="normal")
            self.status_label.config(text=f"Ready to scan: {Path(directory).name}")
    
    def _select_file(self):
        
        file_path = filedialog.askopenfilename(
            title="Select Document File",
            initialdir=str(Path.home()),
            filetypes=[
                ("All Supported", "*.txt *.pdf *.docx *.doc *.xlsx *.xls *.csv *.tsv *.rtf *.odt *.md *.html *.xml *.json"),
                ("Text Files", "*.txt *.md *.rtf"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx *.doc *.odt"),
                ("Excel Files", "*.xlsx *.xls"),
                ("CSV Files", "*.csv *.tsv"),
                ("Web Files", "*.html *.htm *.xml"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file = file_path
            self.selected_directory = None
            # Truncate path if too long
            display_path = file_path
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            
            self.dir_label.config(text=f"📄 {display_path}")
            self.scan_btn.configure(state="normal")
            self.scan_duplicates_btn.configure(state="disabled")
            self.status_label.config(text=f"Ready to scan: {Path(file_path).name}")
    
    def _switch_mode(self, mode: str):
        if self.is_scanning or self.is_scanning_duplicates:
            messagebox.showwarning(
                "Scan in Progress",
                "Please wait for the current scan to complete or cancel it before switching modes."
            )
            return
        
        self.current_mode = mode
        
        # Update button styles
        if mode == "abbreviations":
            self.abbrev_mode_btn.configure(bootstyle="primary")
            self.dedupe_mode_btn.configure(bootstyle="secondary-outline")
            
            # Show abbreviation controls, hide dedupe controls
            self.abbrev_controls.pack(fill='x')
            self.dedupe_controls.pack_forget()
            
            # Update UI elements
            self.status_label.config(text="Abbreviation Scanner mode - Select a folder to begin")
            self._log("Switched to Abbreviation Scanner mode", "INFO")
            
            # Show/hide appropriate sections
            self.results_tree.pack(fill="both", expand=True)
            self.duplicates_tree.pack_forget()
            self.stats_label.pack(anchor="w", pady=(0, 10))
            
        else:  # duplicates mode
            self.abbrev_mode_btn.configure(bootstyle="secondary-outline")
            self.dedupe_mode_btn.configure(bootstyle="primary")
            
            # Show dedupe controls, hide abbreviation controls
            self.dedupe_controls.pack(fill='x')
            self.abbrev_controls.pack_forget()
            
            # Update UI elements
            self.status_label.config(text="File Deduplicator mode - Select a folder to begin")
            self._log("Switched to File Deduplicator mode", "INFO")
            
            # Show duplicates table instead of abbreviations
            self.results_tree.pack_forget()
            self.duplicates_tree.pack(fill="both", expand=True)
            self.stats_label.pack(anchor="w", pady=(0, 10))
            
            # Update scan button text based on dry run mode
            self._update_scan_button_text()
        
        # Reset selection state
        if self.selected_directory:
            folder_name = Path(self.selected_directory).name
            self.status_label.config(text=f"Ready to scan: {folder_name}")
    
    def _update_threshold_label(self, *args):
        self.threshold_label.config(text=str(self.threshold_var.get()))
    
    def _update_duplicate_settings(self):
        self.duplicate_file_type = self.file_type_var.get()
        self.duplicate_threshold = self.threshold_var.get()
        self.dry_run_mode = self.dry_run_var.get()
        self.move_to_trash = self.move_to_trash_var.get()
        self._log(f"Duplicate settings updated: {self.duplicate_file_type}, threshold={self.duplicate_threshold}, dry_run={self.dry_run_mode}, move_to_trash={self.move_to_trash}", "INFO")
        self._update_scan_button_text()
    
    def _update_scan_button_text(self):
        if self.dry_run_mode:
            self.scan_duplicates_btn.config(text="🔍 Preview Duplicates", bootstyle="info")
        else:
            self.scan_duplicates_btn.config(text="🗑️ Delete Duplicates", bootstyle="danger")
    
    def _on_duplicate_selected(self, event):
        selection = self.duplicates_tree.selection()
        if selection:
            self.compare_btn.configure(state="normal")
            self.open_folder_btn.configure(state="normal")
        else:
            self.compare_btn.configure(state="disabled")
            self.open_folder_btn.configure(state="disabled")
    
    def _cancel_scan(self):
        
        if self.is_scanning or self.is_scanning_duplicates:
            self.cancel_scan = True
            scan_type = "duplicate scan" if self.is_scanning_duplicates else "scan"
            self._log(f"User requested {scan_type} cancellation", "WARN")
            self.status_label.config(text=f"Cancelling {scan_type}...")
            self.cancel_btn_scan.configure(state="disabled")
    
    def _start_scan(self):
        
        if (not self.selected_directory and not self.selected_file) or self.is_scanning:
            return
        
        self._log("="*60, "INFO")
        self._log("Starting new scan", "INFO")
        
        if self.selected_file:
            self._log(f"Target file: {self.selected_file}", "INFO")
        else:
            self._log(f"Target directory: {self.selected_directory}", "INFO")
        
        mode = "TextBlob Enhanced" if self.use_textblob else "Fast Pattern Matching"
        self._log(f"Extraction mode: {mode}", "INFO")
        
        # Reset cancel flag
        self.cancel_scan = False
        
        # Disable buttons during scan
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        
        # Show cancel button
        self.cancel_btn_scan.pack(side="left", padx=(10, 0))
        self.cancel_btn_scan.configure(state="normal")
        
        # Clear previous results
        self.extractor.clear()
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Start progress bar
        self.progress_bar.start(10)
        self.progress_label.config(text="Scanning files...")
        self.status_label.config(text="Scanning in progress...")
        
        # Run scan in separate thread
        thread = threading.Thread(target=self._perform_scan, daemon=True)
        thread.start()
    
    def _perform_scan(self):
        
        try:
            # Determine if scanning a file or directory
            if self.selected_file:
                # Single file scan
                self.root.after(0, lambda: self._log("Processing single file...", "INFO"))
                file_path = Path(self.selected_file)
                files = [file_path]
                total_files = 1
            else:
                # Directory scan
                self.root.after(0, lambda: self._log("Scanning directory for files...", "INFO"))
                files = self.scanner.scan_directory(self.selected_directory)
                total_files = len(files)
            
            self.root.after(0, lambda t=total_files: self._log(f"Found {t} document file(s)", "INFO"))
            self.root.after(0, lambda: self.progress_label.config(
                text=f"Found {total_files} file(s). Reading contents..."
            ))
            
            # Step 1: Read all file contents first (fast batch operation)
            self.root.after(0, lambda: self._log("Phase 1: Reading file contents", "INFO"))
            file_contents = []
            for i, file_path in enumerate(files, 1):
                # Check if scan was cancelled
                if self.cancel_scan:
                    self.root.after(0, lambda: self._log("Scan cancelled by user", "WARN"))
                    self.root.after(0, self._scan_cancelled)
                    return
                
                self.root.after(0, lambda idx=i, total=total_files: 
                    self.progress_label.config(
                        text=f"Reading file {idx}/{total}..."
                    ))
                
                content = self.parser.parse_file(file_path)
                file_contents.append((file_path, content))
                
                # Small sleep to allow cancel flag to be checked
                time.sleep(0.001)
                
                if content:
                    size_kb = len(content) / 1024
                    self.root.after(0, lambda p=file_path, s=size_kb: 
                        self._log(f"  Read: {p.name} ({s:.1f} KB)", "DEBUG"))
                else:
                    self.root.after(0, lambda p=file_path: 
                        self._log(f"  Skipped: {p.name} (empty or unreadable)", "WARN"))
            
            # Step 2: Process files one by one with incremental display
            self.root.after(0, lambda: self._log("Phase 2: Extracting abbreviations", "INFO"))
            self.root.after(0, lambda: self.progress_label.config(
                text="Extracting abbreviations..."
            ))
            
            for i, (file_path, content) in enumerate(file_contents, 1):
                # Check if scan was cancelled
                if self.cancel_scan:
                    self.root.after(0, lambda: self._log("Scan cancelled by user", "WARN"))
                    self.root.after(0, self._scan_cancelled)
                    return
                
                if not content:
                    continue
                
                # Update progress
                file_name = file_path.name
                self.root.after(0, lambda idx=i, total=total_files, name=file_name: 
                    self.progress_label.config(
                        text=f"Processing {name} ({idx}/{total})..."
                    ))
                
                # Small sleep to allow cancel flag to be checked
                time.sleep(0.001)
                
                # Extract abbreviations for this file
                before_count = len(self.extractor.abbreviations)
                self.extractor.extract_from_text(content, str(file_path))
                after_count = len(self.extractor.abbreviations)
                
                # Calculate new abbreviations from this file
                new_abbrevs = after_count - before_count
                
                if new_abbrevs > 0:
                    self.root.after(0, lambda fname=file_name, n=new_abbrevs: 
                        self._log(f"  {fname}: Found {n} new abbreviation(s)", "INFO"))
                else:
                    self.root.after(0, lambda fname=file_name: 
                        self._log(f"  {fname}: No new abbreviations", "DEBUG"))
                
                # Display incremental results with file info
                current_results = self.extractor.abbreviations.copy()
                self.root.after(0, lambda r=current_results, fname=file_name, new=new_abbrevs: 
                    self._update_results_incremental(r, fname, new))
            
            # Scanning complete
            self.current_results = self.extractor.abbreviations
            self.root.after(0, self._scan_complete)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._scan_error(msg))
    
    def _scan_complete(self):
        
        self.is_scanning = False
        self.progress_bar.stop()
        
        # Display final results
        self._display_results(self.current_results)
        
        # Update statistics
        stats = self.extractor.get_statistics()
        self._log("="*60, "INFO")
        self._log("Scan completed successfully!", "INFO")
        self._log(f"Total abbreviations: {stats['total_abbreviations']}", "INFO")
        self._log(f"With definitions: {stats['with_definitions']}", "INFO")
        self._log(f"Without definitions: {stats['without_definitions']}", "INFO")
        self._log(f"Coverage: {stats['coverage_percent']}%", "INFO")
        
        self.stats_label.config(
            text=f"Found {stats['total_abbreviations']} abbreviations | "
                 f"{stats['with_definitions']} with definitions | "
                 f"{stats['without_definitions']} without definitions | "
                 f"{stats['coverage_percent']}% coverage"
        )
        
        self.progress_label.config(text="Scan complete!")
        self.status_label.config(text=f"Found {stats['total_abbreviations']} abbreviations")
        
        # Re-enable scan button and hide cancel button
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        if self.current_results:
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
        
        messagebox.showinfo(
            "Scan Complete",
            f"Found {stats['total_abbreviations']} abbreviations in {self.scanner.get_stats()['total_files']} files!"
        )
    
    def _scan_cancelled(self):
        
        self.is_scanning = False
        self.cancel_scan = False
        self.progress_bar.stop()
        
        # Get current stats
        stats = self.extractor.get_statistics()
        
        self._log("="*60, "INFO")
        self._log(f"Scan cancelled - partial results: {stats['total_abbreviations']} abbreviations", "INFO")
        
        self.progress_label.config(text="Scan cancelled")
        self.status_label.config(text=f"Cancelled - {stats['total_abbreviations']} abbreviations found")
        
        # Display partial results
        self.current_results = self.extractor.abbreviations
        self._display_results(self.current_results)
        
        # Update statistics
        if stats['total_abbreviations'] > 0:
            self.stats_label.config(
                text=f"Partial results: {stats['total_abbreviations']} abbreviations | "
                     f"{stats['with_definitions']} with definitions | "
                     f"{stats['without_definitions']} without definitions"
            )
        
        # Re-enable buttons and hide cancel
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        if self.current_results:
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
        
        messagebox.showinfo(
            "Scan Cancelled",
            f"Scan was cancelled.\n\nPartial results: {stats['total_abbreviations']} abbreviations found."
        )
    
    # ======================
    # TASK MANAGEMENT METHODS
    # ======================
    
    def _show_active_tasks(self):
        """Show active tasks in a popup window"""
        # Create popup window
        tasks_window = tk.Toplevel(self.root)
        tasks_window.title("Active Scan Tasks")
        tasks_window.geometry("700x400")
        tasks_window.transient(self.root)
        
        # Header
        header_frame = ttk.Frame(tasks_window)
        header_frame.pack(fill="x", padx=15, pady=15)
        
        ttk.Label(
            header_frame,
            text="⚡ Active Scan Tasks",
            font=("Helvetica", 14, "bold")
        ).pack(side="left")
        
        # Clear completed button
        ttk.Button(
            header_frame,
            text="🗑️ Clear Completed",
            command=lambda: [self.task_manager.clear_completed(), self._refresh_tasks_popup(tasks_window, task_list_frame)],
            bootstyle="secondary-outline"
        ).pack(side="right")
        
        # Scrollable task list
        task_canvas = tk.Canvas(tasks_window, bg="#2b2b2b", highlightthickness=0)
        task_scrollbar = ttk.Scrollbar(tasks_window, orient="vertical", command=task_canvas.yview)
        task_list_frame = ttk.Frame(task_canvas)
        
        task_list_frame.bind(
            "<Configure>",
            lambda e: task_canvas.configure(scrollregion=task_canvas.bbox("all"))
        )
        
        task_canvas.create_window((0, 0), window=task_list_frame, anchor="nw")
        task_canvas.configure(yscrollcommand=task_scrollbar.set)
        
        task_canvas.pack(side="left", fill="both", expand=True, padx=15, pady=(0, 15))
        task_scrollbar.pack(side="right", fill="y", pady=(0, 15))
        
        # Initial population
        self._refresh_tasks_popup(tasks_window, task_list_frame)
        
        # Auto-refresh every second
        def auto_refresh():
            if tasks_window.winfo_exists():
                self._refresh_tasks_popup(tasks_window, task_list_frame)
                tasks_window.after(1000, auto_refresh)
        
        auto_refresh()
    
    def _refresh_tasks_popup(self, window, task_list_frame):
        """Refresh the tasks popup window"""
        if not window.winfo_exists():
            return
        
        # Clear existing items
        for widget in task_list_frame.winfo_children():
            widget.destroy()
        
        # Get all tasks
        tasks = self.task_manager.get_all_tasks()
        
        if not tasks:
            # Show empty state
            ttk.Label(
                task_list_frame,
                text="No tasks. Click 'Scan Now' to start a background scan.",
                font=("Helvetica", 10),
                foreground="gray"
            ).pack(pady=30)
        else:
            # Show task items
            for task in tasks:
                self._create_task_item_popup(task_list_frame, task, window)
    
    def _create_task_item_popup(self, parent, task, window):
        """Create a task item in the popup window"""
        task_frame = ttk.Frame(parent)
        task_frame.pack(fill="x", pady=5, padx=10)
        
        # Status icon
        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "⚡",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.ERROR: "❌",
            TaskStatus.CANCELLED: "⏹️"
        }
        icon = status_icons.get(task.status, "❓")
        
        # Task info
        info_text = f"{icon} {task.name}"
        if task.status == TaskStatus.RUNNING:
            info_text += f" - {task.progress * 100:.0f}%"
            if task.files_processed and task.total_files:
                info_text += f" ({task.files_processed}/{task.total_files})"
        
        task_label = ttk.Label(task_frame, text=info_text, font=("Helvetica", 10))
        task_label.pack(side="left", fill="x", expand=True)
        
        # Action buttons
        if task.status == TaskStatus.RUNNING or task.status == TaskStatus.PENDING:
            cancel_btn = ttk.Button(
                task_frame,
                text="Cancel",
                command=lambda: [self.task_manager.cancel_task(task.id), self._refresh_tasks_popup(window, parent)],
                bootstyle="danger-outline",
                width=10
            )
            cancel_btn.pack(side="right", padx=2)
        
        elif task.status == TaskStatus.COMPLETED:
            export_btn = ttk.Button(
                task_frame,
                text="Export",
                command=lambda: self._export_task_results(task),
                bootstyle="success-outline",
                width=10
            )
            export_btn.pack(side="right", padx=2)
            
            view_btn = ttk.Button(
                task_frame,
                text="View",
                command=lambda: [self._view_task_results(task), window.destroy()],
                bootstyle="info-outline",
                width=10
            )
            view_btn.pack(side="right", padx=2)
        
        # Progress bar for running tasks
        if task.status == TaskStatus.RUNNING:
            progress_bar = ttk.Progressbar(
                task_frame,
                mode='determinate',
                value=task.progress * 100,
                bootstyle="success"
            )
            progress_bar.pack(fill="x", pady=(5, 0))
    
    def _start_scan_as_task(self):
        """Start a new scan as a background task"""
        if not self.selected_directory and not self.selected_file:
            return
        
        # Create task description
        if self.selected_file:
            description = f"File: {Path(self.selected_file).name}"
        else:
            description = f"Folder: {Path(self.selected_directory).name}"
        
        # Create task in queue
        task_id = self.task_manager.create_task(
            target=self.selected_file or self.selected_directory,
            name=description,
            scan_callback=self._perform_task_scan
        )
        
        self._log(f"Task {task_id} queued: {description}", "INFO")
        self.status_label.config(text=f"Background scan started: {description}")
        
        # Show notification
        messagebox.showinfo(
            "Scan Started",
            f"Background scan started: {description}\n\nClick 'Active Tasks' to monitor progress."
        )
    
    def _perform_task_scan(self, task):
        """Perform scan for a background task"""
        try:
            # Initialize scanner and parser for this task
            scanner = Scanner()
            parser = Parser()
            extractor = Extractor(use_textblob=self.use_textblob)
            
            # Determine files to scan
            target = Path(task.target)
            if target.is_file():
                files = [target]
            else:
                files = scanner.scan_directory(str(target))
            
            total_files = len(files)
            
            # Process files
            for i, file_path in enumerate(files, 1):
                # Check cancel flag
                if task.cancel_flag.is_set():
                    break
                
                content = parser.parse_file(file_path)
                if content:
                    extractor.extract_from_text(content, str(file_path))
                
                # Update progress via TaskManager
                self.task_manager.update_task_progress(
                    task.id,
                    files_processed=i,
                    total_files=total_files,
                    results=extractor.abbreviations
                )
            
            # Store final results
            task.results = {
                'abbreviations': extractor.abbreviations,
                'statistics': extractor.get_statistics(),
                'scanner_stats': scanner.get_stats()
            }
            
        except Exception as e:
            # TaskManager will handle setting ERROR status
            raise
    
    def _view_task_results(self, task):
        """View results from a completed task"""
        if not task.results:
            return
        
        # Display results in main view
        self.current_results = task.results.get('abbreviations', {})
        self._display_results(self.current_results)
        
        # Update statistics
        stats = task.results.get('statistics', {})
        self.stats_label.config(
            text=f"Task Results: {stats.get('total_abbreviations', 0)} abbreviations | "
                 f"{stats.get('with_definitions', 0)} with definitions | "
                 f"{stats.get('without_definitions', 0)} without definitions"
        )
        
        self.status_label.config(text=f"Viewing task results: {task.name}")
        self._log(f"Loaded results from task {task.id}", "INFO")
        self._log(f"Loaded results from task {task.task_id[:8]}", "INFO")
        
        # Enable export button
        self.export_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
    
    def _export_task_results(self, task):
        """Export results from a completed task"""
        if not task.results:
            return
        
        # Temporarily set current results
        original_results = self.current_results
        self.current_results = task.results.get('abbreviations', {})
        
        # Call export
        self._export_results()
        
        # Restore original results
        self.current_results = original_results
    
    def _update_results_incremental(self, results: dict, file_name: str, new_count: int):
        
        # Update the tree view with all current abbreviations
        self._display_results(results)
        
        # Update status to show progress per file
        total = len(results)
        if new_count > 0:
            self.status_label.config(
                text=f"✓ {file_name}: +{new_count} new | Total: {total} abbreviations"
            )
        else:
            self.status_label.config(
                text=f"✓ {file_name}: No new abbreviations | Total: {total}"
            )
    
    def _scan_error(self, error_msg: str):
        
        self.is_scanning = False
        self.cancel_scan = False
        self.progress_bar.stop()
        self.progress_label.config(text="Scan failed")
        self.status_label.config(text="Error occurred")
        
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        
        messagebox.showerror("Scan Error", f"An error occurred during scanning:\n\n{error_msg}")
    
    def _display_results(self, results: dict):
        
        # Clear existing results
        self.results_tree.delete(*self.results_tree.get_children())
        
        if not results:
            return
        
        # Add results
        for i, (abbrev, info) in enumerate(sorted(results.items())):
            definition = info['definition'] or "Definition not found"
            count = info['count']
            file_count = len(info['files'])
            
            # Alternate row colors
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            self.results_tree.insert(
                '',
                'end',
                values=(abbrev, definition, count, file_count),
                tags=(tag,)
            )
    
    def _on_search_changed(self, *args):
        
        query = self.search_var.get()
        
        if not query:
            # Show all results
            self._display_results(self.current_results)
        else:
            # Filter results
            filtered = self.extractor.filter_abbreviations(query)
            self._display_results(filtered)
    
    def _show_settings_dialog(self):
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x650")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg='#f5f5f5')
        
        # Center dialog
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        # Main container with scrollbar
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(main_frame, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main container
        container = ttk.Frame(scrollable_frame, padding=(30, 30, 30, 30))
        container.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(container)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text="⚙️ Settings",
            font=("Helvetica", 18, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Configure extraction and duplicate scanning",
            font=("Helvetica", 10),
            bootstyle="secondary"
        ).pack(pady=(5, 0))
        
        # ===== EXTRACTION SETTINGS =====
        extraction_frame = ttk.LabelFrame(container, text="Extraction Settings")
        extraction_frame.pack(fill="x", pady=(0, 20), padx=15, ipady=10)
        
        # TextBlob toggle
        textblob_var = tk.BooleanVar(value=self.use_textblob)
        
        ttk.Checkbutton(
            extraction_frame,
            text="✨ Enable TextBlob Enhancement",
            variable=textblob_var,
            bootstyle="success-round-toggle"
        ).pack(anchor="w")
        
        ttk.Label(
            extraction_frame,
            text="Better noun phrase extraction (~10-50ms slower per file)",
            font=("Helvetica", 9),
            bootstyle="secondary"
        ).pack(anchor="w", padx=(30, 0), pady=(0, 10))
        
        # ===== DUPLICATE SCAN SETTINGS =====
        duplicate_frame = ttk.LabelFrame(container, text="Duplicate Scan Settings")
        duplicate_frame.pack(fill="x", pady=(0, 20), padx=15, ipady=10)
        
        # File type selection
        file_type_label = ttk.Label(
            duplicate_frame,
            text="File Type:",
            font=("Helvetica", 11, "bold")
        )
        file_type_label.pack(anchor="w", pady=(0, 5))
        
        file_type_var = tk.StringVar(value=self.duplicate_file_type)
        file_type_combo = ttk.Combobox(
            duplicate_frame,
            textvariable=file_type_var,
            values=["Images", "Documents", "Videos", "All Files"],
            state="readonly",
            width=25
        )
        file_type_combo.pack(anchor="w", pady=(0, 15))
        
        # Image similarity threshold
        threshold_label = ttk.Label(
            duplicate_frame,
            text="Image Similarity Threshold:",
            font=("Helvetica", 11, "bold")
        )
        threshold_label.pack(anchor="w", pady=(0, 5))
        
        ttk.Label(
            duplicate_frame,
            text="Lower = stricter matching (0-10, default: 5)",
            font=("Helvetica", 9),
            bootstyle="secondary"
        ).pack(anchor="w", pady=(0, 5))
        
        threshold_var = tk.IntVar(value=self.duplicate_threshold)
        threshold_frame = ttk.Frame(duplicate_frame)
        threshold_frame.pack(fill="x", pady=(0, 10))
        
        threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=threshold_var,
            bootstyle="warning"
        )
        threshold_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        threshold_value_label = ttk.Label(
            threshold_frame,
            text=str(threshold_var.get()),
            font=("Helvetica", 11, "bold"),
            width=3
        )
        threshold_value_label.pack(side="left")
        
        def update_threshold_label(*args):
            threshold_value_label.config(text=str(threshold_var.get()))
        
        threshold_var.trace('w', update_threshold_label)
        
        # Info section
        info_frame = ttk.Frame(container)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            info_frame,
            text="ℹ️ Duplicate Scan Features:",
            font=("Helvetica", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        features = [
            ("🗑️", "Automatically removes duplicate files"),
            ("📸", "Keeps higher resolution images"),
            ("🔍", "Hash-based matching for exact duplicates"),
            ("🎨", "Perceptual hash for similar images")
        ]
        
        for icon, text in features:
            feature_frame = ttk.Frame(info_frame)
            feature_frame.pack(fill="x", pady=3)
            
            ttk.Label(
                feature_frame,
                text=icon,
                font=("Helvetica", 12)
            ).pack(side="left", padx=(0, 10))
            
            ttk.Label(
                feature_frame,
                text=text,
                font=("Helvetica", 10)
            ).pack(side="left", anchor="w")
        
        # Action buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(15, 0))
        
        def save_settings():
            # Save extraction settings
            old_setting = self.use_textblob
            self.use_textblob = textblob_var.get()
            
            if old_setting != self.use_textblob:
                # Reinitialize extractor with new setting
                self.extractor = SmartExtractor(prefer_llm=False, use_textblob=self.use_textblob)
                mode = "TextBlob Enhanced" if self.use_textblob else "Fast Pattern"
                self._log(f"Switched to {mode} mode", "INFO")
            
            # Save duplicate scan settings
            self.duplicate_file_type = file_type_var.get()
            self.duplicate_threshold = threshold_var.get()
            
            self._log(f"Duplicate settings updated: {self.duplicate_file_type}, threshold={self.duplicate_threshold}", "INFO")
            self.status_label.config(text="✓ Settings saved")
            
            settings_window.destroy()
        
        ttk.Button(
            button_frame,
            text="💾 Save & Apply",
            command=save_settings,
            bootstyle="success",
            width=20
        ).pack(side="left", padx=(0, 10), ipady=10)
        
        ttk.Button(
            button_frame,
            text="✕ Cancel",
            command=settings_window.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side="left", ipady=10)
        
        settings_window.bind("<Escape>", lambda e: settings_window.destroy())
    
    def _show_export_menu(self):
        
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Report")
        export_window.geometry("400x350")
        export_window.transient(self.root)
        export_window.grab_set()
        
        # Center dialog
        export_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (export_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (export_window.winfo_height() // 2)
        export_window.geometry(f"+{x}+{y}")
        
        container = ttk.Frame(export_window, padding=(20, 20, 20, 20))
        container.pack(fill="both", expand=True)
        
        ttk.Label(
            container,
            text="Select Export Format",
            font=("Helvetica", 14, "bold")
        ).pack(pady=(0, 20))
        
        # Export format buttons
        ttk.Button(
            container,
            text="📄 Export as Text (.txt)",
            command=lambda: self._export('txt', export_window),
            bootstyle="success",
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            container,
            text="📊 Export as CSV (.csv)",
            command=lambda: self._export('csv', export_window),
            bootstyle="info",
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            container,
            text="📋 Export as JSON (.json)",
            command=lambda: self._export('json', export_window),
            bootstyle="primary",
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            container,
            text="📗 Export as Excel (.xlsx)",
            command=lambda: self._export('xlsx', export_window),
            bootstyle="success-outline",
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            container,
            text="📕 Export as PDF (.pdf)",
            command=lambda: self._export('pdf', export_window),
            bootstyle="danger-outline",
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            container,
            text="Cancel",
            command=export_window.destroy,
            bootstyle="secondary",
            width=30
        ).pack(pady=(20, 0))
    
    def _export(self, format: str, dialog):
        
        if not self.current_results:
            messagebox.showwarning("No Results", "No results to export!")
            return
        
        # Get save location
        default_filename = self.exporter.get_default_filename(format)
        
        filetypes = {
            'txt': [("Text files", "*.txt"), ("All files", "*.*")],
            'csv': [("CSV files", "*.csv"), ("All files", "*.*")],
            'json': [("JSON files", "*.json"), ("All files", "*.*")]
        }
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=filetypes[format],
            initialfile=default_filename,
            title=f"Save {format.upper()} Report"
        )
        
        if filepath:
            success = self.exporter.export(self.current_results, filepath, format)
            
            if success:
                self._log(f"Exported results to {format.upper()}: {filepath}", "INFO")
                dialog.destroy()
                messagebox.showinfo(
                    "Export Successful",
                    f"Report saved to:\n{filepath}"
                )
                self.status_label.config(text=f"Exported to {Path(filepath).name}")
            else:
                self._log(f"{format.upper()} export failed", "ERROR")
                messagebox.showerror(
                    "Export Failed",
                    "Failed to export report. Please try again."
                )
    
    def _clear_results(self):
        
        result = messagebox.askyesno(
            "Clear Results",
            "Are you sure you want to clear all results?"
        )
        
        if result:
            self._log("Clearing all results", "INFO")
            self.extractor.clear()
            self.current_results = {}
            self.results_tree.delete(*self.results_tree.get_children())
            self.stats_label.config(text="No results yet")
            self.status_label.config(text="Results cleared")
            self.progress_label.config(text="Ready to scan")
            self.export_btn.configure(state="disabled")
            self.clear_btn.configure(state="disabled")
    
    def _start_duplicate_scan(self):
        
        if not self.selected_directory or self.is_scanning_duplicates:
            return
        
        self._log("="*60, "INFO")
        self._log("Starting duplicate file scan", "INFO")
        self._log(f"Target directory: {self.selected_directory}", "INFO")
        self._log(f"File type: {self.duplicate_file_type}", "INFO")
        self._log(f"Image similarity threshold: {self.duplicate_threshold}", "INFO")
        
        # Auto-expand log view for duplicate scanning
        if not self.log_expanded:
            self._toggle_log_view()
        
        # Reset cancel flag
        self.cancel_scan = False
        
        # Disable buttons during scan
        self.is_scanning_duplicates = True
        self.scan_duplicates_btn.configure(state="disabled")
        
        # Show cancel button
        self.cancel_btn_scan.pack(side="left", padx=(10, 0))
        self.cancel_btn_scan.configure(state="normal")
        
        # Start progress bar
        self.progress_bar.start(10)
        self.progress_label.config(text="Scanning for duplicates...")
        self.status_label.config(text="Duplicate scan in progress...")
        
        # Run scan in separate thread
        thread = threading.Thread(target=self._perform_duplicate_scan, daemon=True)
        thread.start()
    
    def _perform_duplicate_scan(self):
        try:
            # Initialize duplicate handler with new options
            handler = DuplicateHandler(
                duplicate_mode="delete",
                image_phash_threshold=self.duplicate_threshold,
                file_type=self.duplicate_file_type,
                dry_run=True,  # Always dry run first to preview
                move_to_trash=self.move_to_trash,
            )
            
            self.root.after(0, lambda: self._log("Duplicate handler initialized (preview mode)", "INFO"))
            
            # Count total files
            folder_path = Path(self.selected_directory)
            all_files = list(folder_path.rglob("*"))
            valid_files = [f for f in all_files if handler.is_valid_file(f)]
            total_files = len(valid_files)
            
            self.root.after(0, lambda t=total_files: self._log(f"Found {t} files to scan", "INFO"))
            
            # Before stats
            before_size = sum(f.stat().st_size for f in valid_files if f.exists())
            
            # Stats
            stats = {
                'new': 0,
                'duplicate_deleted': 0,
                'duplicate_kept_new': 0,
                'error': 0,
                'total_files': total_files,
                'before_size': before_size
            }
            
            # Process each file (in batches for better performance)
            batch_size = 100
            for batch_start in range(0, total_files, batch_size):
                # Check cancellation at batch start
                if self.cancel_scan:
                    self.root.after(0, lambda: self._log("Duplicate scan cancelled by user", "WARN"))
                    self.root.after(0, self._duplicate_scan_cancelled)
                    return
                
                batch_end = min(batch_start + batch_size, total_files)
                batch = valid_files[batch_start:batch_end]
                
                for i, file_path in enumerate(batch, batch_start + 1):
                    # Check if scan was cancelled (every file for responsive cancellation)
                    if self.cancel_scan:
                        self.root.after(0, lambda: self._log("Duplicate scan cancelled by user", "WARN"))
                        self.root.after(0, self._duplicate_scan_cancelled)
                        return
                    
                    # Update progress every 10 files
                    if i % 10 == 0:
                        progress_pct = int((i / total_files) * 100)
                        self.root.after(0, lambda idx=i, total=total_files, pct=progress_pct: 
                            self.progress_label.config(
                                text=f"Scanning... {idx}/{total} ({pct}%)"
                            ))
                    
                    # Handle duplicate
                    status, ref, dup_info = handler.handle_duplicate(file_path)
                    stats[status] = stats.get(status, 0) + 1
                    
                    # Small sleep every few files to allow cancel flag to be checked
                    if i % 5 == 0:
                        time.sleep(0.001)
                    
                    # Log preview results less verbosely
                    if status != "new" and i % 5 == 0:
                        if status == "duplicate_deleted":
                            self.root.after(0, lambda p=file_path: 
                                self._log(f"Found duplicate: {p.name}", "INFO"))
            
            # Store preview data
            self.duplicate_preview_data = handler.duplicates_found
            dup_stats = handler.get_duplicate_stats()
            stats.update(dup_stats)
            
            # Scan complete - show preview
            self.root.after(0, lambda s=stats: self._duplicate_scan_complete(s))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._duplicate_scan_error(msg))
    
    def _duplicate_scan_complete(self, stats: dict):
        self.is_scanning_duplicates = False
        self.progress_bar.stop()
        
        # Log statistics
        self._log("="*60, "INFO")
        self._log("Duplicate scan completed!", "INFO")
        self._log(f"Total files scanned: {stats.get('total_files', 0)}", "INFO")
        self._log(f"Unique files: {stats.get('new', 0)}", "INFO")
        self._log(f"Duplicates found: {stats.get('total_duplicates', 0)}", "INFO")
        self._log(f"Space that can be saved: {stats.get('size_saved_mb', 0)} MB", "INFO")
        
        # Display duplicates in tree
        self._display_duplicate_results()
        
        # Update stats label
        self.stats_label.config(
            text=f"Found {stats.get('total_duplicates', 0)} duplicates | "
                 f"Can save {stats.get('size_saved_mb', 0)} MB | "
                 f"Scanned {stats.get('total_files', 0)} files"
        )
        
        self.progress_label.config(text="Scan complete! Preview results below.")
        self.status_label.config(text=f"✓ Found {stats.get('total_duplicates', 0)} duplicates")
        
        # Re-enable buttons and hide cancel
        self.scan_duplicates_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        
        # Enable delete button and copy button if duplicates found
        if stats.get('total_duplicates', 0) > 0:
            self.delete_duplicates_btn.configure(state="normal")
            self.copy_results_btn.configure(state="normal")
        else:
            self.delete_duplicates_btn.configure(state="disabled")
            self.copy_results_btn.configure(state="disabled")
        
        messagebox.showinfo(
            "Scan Complete",
            f"Preview complete!\n\n"
            f"✓ Scanned: {stats.get('total_files', 0)} files\n"
            f"🔍 Duplicates found: {stats.get('total_duplicates', 0)}\n"
            f"💾 Space can be saved: {stats.get('size_saved_mb', 0)} MB\n\n"
            f"Review the list below and click 'Delete Duplicates' to proceed."
        )
    
    def _duplicate_scan_cancelled(self):
        
        self.is_scanning_duplicates = False
        self.cancel_scan = False
        self.progress_bar.stop()
        
        self._log("="*60, "INFO")
        self._log("Duplicate scan cancelled", "INFO")
        
        self.progress_label.config(text="Duplicate scan cancelled")
        self.status_label.config(text="Cancelled")
        
        # Re-enable buttons and hide cancel
        self.scan_duplicates_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        
        messagebox.showinfo(
            "Scan Cancelled",
            "Duplicate scan was cancelled."
        )
    
    def _duplicate_scan_error(self, error_msg: str):
        
        self.is_scanning_duplicates = False
        self.cancel_scan = False
        self.progress_bar.stop()
        
        self._log(f"Duplicate scan error: {error_msg}", "ERROR")
        
        self.progress_label.config(text="Duplicate scan failed")
        self.status_label.config(text="Error occurred")
        
        self.scan_duplicates_btn.configure(state="normal")
        self.cancel_btn_scan.pack_forget()
        
        messagebox.showerror(
            "Duplicate Scan Error",
            f"An error occurred during duplicate scanning:\n\n{error_msg}"
        )
    
    def _display_duplicate_results(self):
        # Clear existing items
        for item in self.duplicates_tree.get_children():
            self.duplicates_tree.delete(item)
        
        if not self.duplicate_preview_data:
            return
        
        for i, dup_info in enumerate(self.duplicate_preview_data):
            to_delete = dup_info['to_delete']
            to_keep = dup_info['to_keep']
            reason = dup_info['reason']
            size_mb = round(dup_info['delete_size'] / (1024 * 1024), 2)
            
            # Format resolution info if available
            if 'delete_res' in dup_info:
                res_info = f"{dup_info['delete_res']:,} → {dup_info['keep_res']:,} px"
            else:
                res_info = "N/A"
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.duplicates_tree.insert(
                '',
                'end',
                text='✓',
                values=(
                    to_delete.name,
                    to_keep.name,
                    reason,
                    f"{size_mb} MB",
                    res_info
                ),
                tags=(tag,)
            )
    
    def _confirm_and_delete_duplicates(self):
        if not self.duplicate_preview_data:
            messagebox.showwarning("No Duplicates", "No duplicates to delete. Run a scan first.")
            return
        
        total_duplicates = len(self.duplicate_preview_data)
        total_size_mb = sum(d['delete_size'] for d in self.duplicate_preview_data) / (1024 * 1024)
        
        action = "moved to trash" if self.move_to_trash else "permanently deleted"
        
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"⚠️ Warning!\n\n"
            f"You are about to delete {total_duplicates} duplicate file(s).\n"
            f"This will free up {total_size_mb:.2f} MB of space.\n\n"
            f"Files will be {action}.\n\n"
            f"Do you want to proceed?",
            icon='warning'
        )
        
        if result:
            self._delete_duplicates()
    
    def _delete_duplicates(self):
        self._log("="*60, "INFO")
        self._log("Starting deletion of duplicates...", "INFO")
        
        deleted_count = 0
        error_count = 0
        
        for dup_info in self.duplicate_preview_data:
            to_delete = dup_info['to_delete']
            
            try:
                if self.move_to_trash:
                    self._move_file_to_trash(to_delete)
                    self._log(f"Moved to trash: {to_delete.name}", "INFO")
                else:
                    to_delete.unlink()
                    self._log(f"Deleted: {to_delete.name}", "INFO")
                deleted_count += 1
            except Exception as e:
                self._log(f"Error deleting {to_delete.name}: {e}", "ERROR")
                error_count += 1
        
        # Clear preview data
        self.duplicate_preview_data = []
        self.duplicates_tree.delete(*self.duplicates_tree.get_children())
        self.delete_duplicates_btn.configure(state="disabled")
        
        self._log(f"Deletion complete: {deleted_count} deleted, {error_count} errors", "INFO")
        
        messagebox.showinfo(
            "Deletion Complete",
            f"✓ Successfully processed {deleted_count} file(s)\n"
            f"❌ Errors: {error_count}\n\n"
            f"Check the logs for details."
        )
    
    def _move_file_to_trash(self, path: Path):
        import platform
        
        if platform.system() == "Darwin":  # macOS
            from subprocess import run
            run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{path}"'], check=True)
        elif platform.system() == "Windows":
            try:
                from send2trash import send2trash
                send2trash(str(path))
            except ImportError:
                # Fallback to delete if send2trash not available
                path.unlink()
        else:  # Linux
            import shutil
            trash_dir = Path.home() / ".local" / "share" / "Trash" / "files"
            trash_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(trash_dir / path.name))
    
    def _compare_selected_duplicates(self):
        selection = self.duplicates_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select duplicate(s) to compare.")
            return
        
        if len(selection) != 1:
            messagebox.showinfo("Multiple Selection", "Please select only one duplicate pair to compare.")
            return
        
        # Get the selected item data
        item = selection[0]
        values = self.duplicates_tree.item(item, 'values')
        
        if not values:
            return
        
        # Find the corresponding duplicate info
        file_to_delete_name = values[0]
        for dup_info in self.duplicate_preview_data:
            if dup_info['to_delete'].name == file_to_delete_name:
                self._show_comparison_dialog(dup_info)
                break
    
    def _show_comparison_dialog(self, dup_info):
        compare_window = tk.Toplevel(self.root)
        compare_window.title("File Comparison")
        compare_window.geometry("900x700")
        compare_window.transient(self.root)
        
        container = ttk.Frame(compare_window, padding=(20, 20))
        container.pack(fill="both", expand=True)
        
        ttk.Label(
            container,
            text="Side-by-Side Comparison",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Create two columns
        columns_frame = ttk.Frame(container)
        columns_frame.pack(fill="both", expand=True)
        
        # Left column (file to delete)
        left_frame = ttk.LabelFrame(columns_frame, text="🗑️ To Delete")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), ipady=5)
        
        self._show_file_info(left_frame, dup_info['to_delete'], dup_info.get('delete_res'))
        
        # Right column (file to keep)
        right_frame = ttk.LabelFrame(columns_frame, text="✅ To Keep")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), ipady=5)
        
        self._show_file_info(right_frame, dup_info['to_keep'], dup_info.get('keep_res'))
        
        # Close button
        ttk.Button(
            container,
            text="Close",
            command=compare_window.destroy,
            bootstyle="secondary",
            width=15
        ).pack(pady=(20, 0))
    
    def _show_file_info(self, parent, file_path: Path, resolution=None):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill="both", expand=True)
        
        ttk.Label(info_frame, text=f"Name: {file_path.name}", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=5)
        ttk.Label(info_frame, text=f"Path: {file_path.parent}", font=("Helvetica", 9)).pack(anchor="w", pady=2)
        
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            ttk.Label(info_frame, text=f"Size: {size_mb:.2f} MB", font=("Helvetica", 9)).pack(anchor="w", pady=2)
            
            if resolution:
                ttk.Label(info_frame, text=f"Resolution: {resolution:,} pixels", font=("Helvetica", 9)).pack(anchor="w", pady=2)
            
            # Show image preview if it's an image
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(file_path)
                    img.thumbnail((350, 350))
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = ttk.Label(info_frame, image=photo)
                    img_label.image = photo  # Keep a reference
                    img_label.pack(pady=10)
                except Exception as e:
                    ttk.Label(info_frame, text=f"Cannot preview: {e}", font=("Helvetica", 9)).pack(pady=10)
        else:
            ttk.Label(info_frame, text="File not found", font=("Helvetica", 9), foreground="red").pack(anchor="w", pady=2)
    
    def _open_duplicate_folder(self):
        import subprocess
        import platform
        
        selection = self.duplicates_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a duplicate to open its folder.")
            return
        
        # Get the first selected item
        item = selection[0]
        values = self.duplicates_tree.item(item, 'values')
        
        if not values:
            return
        
        # Find the corresponding duplicate info
        file_to_delete_name = values[0]
        for dup_info in self.duplicate_preview_data:
            if dup_info['to_delete'].name == file_to_delete_name:
                file_path = dup_info['to_delete']
                
                # Open the folder containing the file
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", "-R", str(file_path)])
                elif platform.system() == "Windows":
                    subprocess.run(["explorer", "/select,", str(file_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(file_path.parent)])
                
                self._log(f"Opened folder: {file_path.parent}", "INFO")
                break
    
    def _copy_duplicate_results(self):
        if not self.duplicate_preview_data:
            messagebox.showinfo("No Results", "No duplicate results to copy.")
            return
        
        # Format results as text
        results_text = "DUPLICATE FILES REPORT\n"
        results_text += "=" * 80 + "\n\n"
        
        for i, dup_info in enumerate(self.duplicate_preview_data, 1):
            results_text += f"Duplicate #{i}\n"
            results_text += f"  To Delete: {dup_info['to_delete']}\n"
            results_text += f"  To Keep:   {dup_info['to_keep']}\n"
            results_text += f"  Reason:    {dup_info['reason']}\n"
            
            size_mb = dup_info['delete_size'] / (1024 * 1024)
            results_text += f"  Size Saved: {size_mb:.2f} MB\n"
            
            if dup_info.get('delete_res'):
                results_text += f"  Resolution (Delete): {dup_info['delete_res']:,} pixels\n"
            if dup_info.get('keep_res'):
                results_text += f"  Resolution (Keep):   {dup_info['keep_res']:,} pixels\n"
            
            results_text += "\n"
        
        # Add summary
        total_size = sum(d['delete_size'] for d in self.duplicate_preview_data) / (1024 * 1024)
        results_text += "=" * 80 + "\n"
        results_text += f"SUMMARY\n"
        results_text += f"Total Duplicates: {len(self.duplicate_preview_data)}\n"
        results_text += f"Total Space to Save: {total_size:.2f} MB\n"
        
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(results_text)
        self.root.update()
        
        self._log(f"Copied {len(self.duplicate_preview_data)} duplicate results to clipboard", "INFO")
        messagebox.showinfo("Copied", f"Successfully copied {len(self.duplicate_preview_data)} duplicate results to clipboard!")
    
    def run(self):
        
        self.root.mainloop()
