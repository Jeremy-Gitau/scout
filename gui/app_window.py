"""
Main application window for Scout.
Modern UI using ttkbootstrap with cross-platform support.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import threading
import logging
import datetime
from typing import Optional

from core.scanner import Scanner
from core.parser import Parser
from core.smart_extractor import SmartExtractor
from core.exporter import Exporter


class ScoutApp:
    """Main application window for Scout."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Scout — Explore your files, uncover meaning")
        self.root.geometry("1000x700")
        
        # State variables (must be set before initializing extractor)
        self.selected_directory: Optional[str] = None
        self.is_scanning = False
        self.cancel_scan = False  # Flag to cancel ongoing scan
        self.current_results = {}
        self.log_expanded = False  # Log view collapsed by default
        self.use_textblob = False  # TextBlob enhancement disabled by default
        
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
    
    def _setup_logging(self):
        """Setup logging infrastructure."""
        # Create custom logging handler that writes to GUI
        self.log_messages = []
        
    def _log(self, message: str, level: str = "INFO"):
        """Add a log message to the log view."""
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
        """Setup the user interface."""
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
    
    def _create_header(self, parent):
        """Create the header section."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ttk.Label(
            header_frame,
            text="🔍 Scout",
            font=("Helvetica", 24, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side="left")
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Explore your files, uncover meaning",
            font=("Helvetica", 11),
            bootstyle="secondary"
        )
        subtitle_label.pack(side="left", padx=(10, 0))
    
    def _create_control_panel(self, parent):
        """Create the control panel with buttons."""
        control_frame = ttk.LabelFrame(
            parent,
            text="Controls",

        )
        control_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        # Inner frame for padding
        inner_frame = ttk.Frame(control_frame)
        inner_frame.pack(fill='x', padx=15, pady=15)
        
        # Directory selection
        dir_frame = ttk.Frame(inner_frame)
        dir_frame.pack(fill='x', pady=(0, 10))
        
        self.dir_label = ttk.Label(
            dir_frame,
            text="No folder selected",
            font=("Helvetica", 10),
            bootstyle="secondary"
        )
        self.dir_label.pack(side='left', fill='x', expand=True)
        
        select_btn = ttk.Button(
            dir_frame,
            text="Select Folder",
            command=self._select_directory,
            bootstyle="success",
            width=15
        )
        select_btn.pack(side="right", padx=(10, 0))
        
        # Settings button
        settings_frame = ttk.Frame(inner_frame)
        settings_frame.pack(fill='x', pady=(0, 10))
        
        settings_btn = ttk.Button(
            settings_frame,
            text="⚙️ Settings",
            command=self._show_settings_dialog,
            bootstyle="secondary-outline",
            width=15
        )
        settings_btn.pack(side="left")
        
        # Action buttons
        button_frame = ttk.Frame(inner_frame)
        button_frame.pack(fill="x")
        
        self.scan_btn = ttk.Button(
            button_frame,
            text="🔍 Scan Files",
            command=self._start_scan,
            bootstyle="success-outline",
            width=20
        )
        self.scan_btn.pack(side="left", padx=(0, 10))
        self.scan_btn.configure(state="disabled")
        
        self.cancel_btn_scan = ttk.Button(
            button_frame,
            text="⏹️ Cancel Scan",
            command=self._cancel_scan,
            bootstyle="danger-outline",
            width=20
        )
        self.cancel_btn_scan.pack(side="left", padx=(0, 10))
        self.cancel_btn_scan.configure(state="disabled")
        
        self.export_btn = ttk.Button(
            button_frame,
            text="💾 Export Report",
            command=self._show_export_menu,
            bootstyle="info-outline",
            width=20
        )
        self.export_btn.pack(side="left", padx=(0, 10))
        self.export_btn.configure(state="disabled")
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Clear Results",
            command=self._clear_results,
            bootstyle="secondary-outline",
            width=20
        )
        self.clear_btn.pack(side="left")
        self.clear_btn.configure(state="disabled")
    
    def _create_progress_section(self, parent):
        """Create the progress bar section."""
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
        """Create the results display section."""
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
        
        # Treeview for results
        columns = ('abbreviation', 'definition', 'occurrences', 'files')
        self.results_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            bootstyle="info"
        )
        
        # Configure scrollbar
        scrollbar.config(command=self.results_tree.yview)
        
        # Define headings
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
        
        # Alternating row colors
        self.results_tree.tag_configure('oddrow', background='#f0f0f0')
        self.results_tree.tag_configure('evenrow', background='#ffffff')
    
    def _create_log_section(self, parent):
        """Create the expandable log view section."""
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
        """Toggle the log view visibility."""
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
        """Create the status bar."""
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
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(
            title="Select Folder to Scan",
            initialdir=str(Path.home())
        )
        
        if directory:
            self.selected_directory = directory
            # Truncate path if too long
            display_path = directory
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            
            self.dir_label.config(text=f"📁 {display_path}")
            self.scan_btn.configure(state="normal")
            self.status_label.config(text=f"Ready to scan: {Path(directory).name}")
    
    def _cancel_scan(self):
        """Cancel the ongoing scan."""
        if self.is_scanning:
            self.cancel_scan = True
            self._log("User requested scan cancellation", "WARN")
            self.status_label.config(text="Cancelling scan...")
            self.cancel_btn_scan.configure(state="disabled")
    
    def _start_scan(self):
        """Start the scanning process."""
        if not self.selected_directory or self.is_scanning:
            return
        
        self._log("="*60, "INFO")
        self._log("Starting new scan", "INFO")
        self._log(f"Target directory: {self.selected_directory}", "INFO")
        mode = "TextBlob Enhanced" if self.use_textblob else "Fast Pattern Matching"
        self._log(f"Extraction mode: {mode}", "INFO")
        
        # Reset cancel flag
        self.cancel_scan = False
        
        # Disable buttons during scan
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        self.cancel_btn_scan.configure(state="normal")  # Enable cancel
        self.export_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        
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
        """Perform the actual scanning (runs in separate thread)."""
        try:
            # Scan directory
            self.root.after(0, lambda: self._log("Scanning directory for files...", "INFO"))
            files = self.scanner.scan_directory(self.selected_directory)
            total_files = len(files)
            
            self.root.after(0, lambda t=total_files: self._log(f"Found {t} document files", "INFO"))
            self.root.after(0, lambda: self.progress_label.config(
                text=f"Found {total_files} files. Reading contents..."
            ))
            
            # Step 1: Read all file contents first (fast batch operation)
            self.root.after(0, lambda: self._log("Phase 1: Reading file contents", "INFO"))
            file_contents = []
            for i, file_path in enumerate(files, 1):
                self.root.after(0, lambda idx=i, total=total_files: 
                    self.progress_label.config(
                        text=f"Reading file {idx}/{total}..."
                    ))
                
                content = self.parser.parse_file(file_path)
                file_contents.append((file_path, content))
                
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
        """Handle scan completion."""
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
        
        # Re-enable scan button and disable cancel button
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.configure(state="disabled")
        if self.current_results:
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
        
        messagebox.showinfo(
            "Scan Complete",
            f"Found {stats['total_abbreviations']} abbreviations in {self.scanner.get_stats()['total_files']} files!"
        )
    
    def _scan_cancelled(self):
        """Handle scan cancellation."""
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
        
        # Re-enable buttons
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.configure(state="disabled")
        if self.current_results:
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
        
        messagebox.showinfo(
            "Scan Cancelled",
            f"Scan was cancelled.\n\nPartial results: {stats['total_abbreviations']} abbreviations found."
        )
    
    def _update_results_incremental(self, results: dict, file_name: str, new_count: int):
        """Update results display incrementally as files are processed."""
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
        """Handle scan error."""
        self.is_scanning = False
        self.cancel_scan = False
        self.progress_bar.stop()
        self.progress_label.config(text="Scan failed")
        self.status_label.config(text="Error occurred")
        
        self.scan_btn.configure(state="normal")
        self.cancel_btn_scan.configure(state="disabled")
        
        messagebox.showerror("Scan Error", f"An error occurred during scanning:\n\n{error_msg}")
    
    def _display_results(self, results: dict):
        """Display results in the tree view."""
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
        """Handle search text changes."""
        query = self.search_var.get()
        
        if not query:
            # Show all results
            self._display_results(self.current_results)
        else:
            # Filter results
            filtered = self.extractor.filter_abbreviations(query)
            self._display_results(filtered)
    
    def _show_settings_dialog(self):
        """Show extraction settings with TextBlob toggle."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Extraction Settings")
        settings_window.geometry("550x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg='#f5f5f5')
        
        # Center dialog
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        # Main container
        container = ttk.Frame(settings_window, padding=(30, 30, 30, 30))
        container.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(container)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            header_frame,
            text="⚙️ Extraction Settings",
            font=("Helvetica", 18, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Configure extraction method",
            font=("Helvetica", 10),
            bootstyle="secondary"
        ).pack(pady=(5, 0))
        
        # TextBlob toggle
        textblob_var = tk.BooleanVar(value=self.use_textblob)
        
        toggle_frame = ttk.Frame(container)
        toggle_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Checkbutton(
            toggle_frame,
            text="✨ Enable TextBlob Enhancement",
            variable=textblob_var,
            bootstyle="success-round-toggle"
        ).pack(anchor="w")
        
        ttk.Label(
            toggle_frame,
            text="Better noun phrase extraction (~10-50ms slower per file)",
            font=("Helvetica", 9),
            bootstyle="secondary"
        ).pack(anchor="w", padx=(30, 0))
        
        # Info section
        info_frame = ttk.Frame(container)
        info_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        features = [
            ("⚡", "Lightning-fast extraction (< 1ms per abbreviation)"),
            ("💾", "Zero disk space - no downloads"),
            ("✓", "Handles explicit definitions perfectly"),
            ("🚀", "Optimized for many files")
        ]
        
        for icon, text in features:
            feature_frame = ttk.Frame(info_frame)
            feature_frame.pack(fill="x", pady=5)
            
            ttk.Label(
                feature_frame,
                text=icon,
                font=("Helvetica", 14)
            ).pack(side="left", padx=(0, 10))
            
            ttk.Label(
                feature_frame,
                text=text,
                font=("Helvetica", 11)
            ).pack(side="left", anchor="w")
        
        # Action buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(15, 0))
        
        def save_settings():
            old_setting = self.use_textblob
            self.use_textblob = textblob_var.get()
            
            if old_setting != self.use_textblob:
                # Reinitialize extractor with new setting
                self.extractor = SmartExtractor(prefer_llm=False, use_textblob=self.use_textblob)
                mode = "TextBlob Enhanced" if self.use_textblob else "Fast Pattern"
                self._log(f"Switched to {mode} mode", "INFO")
                self.status_label.config(text=f"✓ Switched to {mode} mode")
            
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
        """Show export format selection menu."""
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Report")
        export_window.geometry("400x250")
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
        ).pack(pady=10)
        
        ttk.Button(
            container,
            text="📊 Export as CSV (.csv)",
            command=lambda: self._export('csv', export_window),
            bootstyle="info",
            width=30
        ).pack(pady=10)
        
        ttk.Button(
            container,
            text="📋 Export as JSON (.json)",
            command=lambda: self._export('json', export_window),
            bootstyle="primary",
            width=30
        ).pack(pady=10)
        
        ttk.Button(
            container,
            text="Cancel",
            command=export_window.destroy,
            bootstyle="secondary",
            width=30
        ).pack(pady=(20, 0))
    
    def _export(self, format: str, dialog):
        """Export results in specified format."""
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
        """Clear all results."""
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
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
