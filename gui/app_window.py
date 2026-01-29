"""
Main application window for Scout.
Modern UI using ttkbootstrap with cross-platform support.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import threading
from typing import Optional

from core.scanner import Scanner
from core.parser import Parser
from core.extractor import Extractor
from core.exporter import Exporter


class ScoutApp:
    """Main application window for Scout."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Scout — Explore your files, uncover meaning")
        self.root.geometry("1000x700")
        
        # Initialize core components
        self.scanner = Scanner()
        self.parser = Parser()
        self.extractor = Extractor()
        self.exporter = Exporter()
        
        # State variables
        self.selected_directory: Optional[str] = None
        self.is_scanning = False
        self.current_results = {}
        
        # Setup UI
        self._setup_ui()
        
        # Center window on screen
        self._center_window()
    
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
    
    def _start_scan(self):
        """Start the scanning process."""
        if not self.selected_directory or self.is_scanning:
            return
        
        # Disable buttons during scan
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
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
            files = self.scanner.scan_directory(self.selected_directory)
            total_files = len(files)
            
            self.root.after(0, lambda: self.progress_label.config(
                text=f"Found {total_files} files. Processing..."
            ))
            
            # Process each file
            for i, file_path in enumerate(files, 1):
                # Update progress
                self.root.after(0, lambda idx=i, total=total_files: 
                    self.progress_label.config(
                        text=f"Processing file {idx}/{total}..."
                    ))
                
                # Parse file
                content = self.parser.parse_file(file_path)
                
                if content:
                    # Extract abbreviations
                    self.extractor.extract_from_text(content, str(file_path))
            
            # Scanning complete
            self.current_results = self.extractor.abbreviations
            self.root.after(0, self._scan_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._scan_error(str(e)))
    
    def _scan_complete(self):
        """Handle scan completion."""
        self.is_scanning = False
        self.progress_bar.stop()
        
        # Display results
        self._display_results(self.current_results)
        
        # Update statistics
        stats = self.extractor.get_statistics()
        self.stats_label.config(
            text=f"Found {stats['total_abbreviations']} abbreviations | "
                 f"{stats['with_definitions']} with definitions | "
                 f"{stats['without_definitions']} without definitions | "
                 f"{stats['coverage_percent']}% coverage"
        )
        
        self.progress_label.config(text="Scan complete!")
        self.status_label.config(text=f"Found {stats['total_abbreviations']} abbreviations")
        
        # Re-enable buttons
        self.scan_btn.configure(state="normal")
        if self.current_results:
            self.export_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")
        
        messagebox.showinfo(
            "Scan Complete",
            f"Found {stats['total_abbreviations']} abbreviations in {self.scanner.get_stats()['total_files']} files!"
        )
    
    def _scan_error(self, error_msg: str):
        """Handle scan error."""
        self.is_scanning = False
        self.progress_bar.stop()
        self.progress_label.config(text="Scan failed")
        self.status_label.config(text="Error occurred")
        
        self.scan_btn.configure(state="normal")
        
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
                dialog.destroy()
                messagebox.showinfo(
                    "Export Successful",
                    f"Report saved to:\n{filepath}"
                )
                self.status_label.config(text=f"Exported to {Path(filepath).name}")
            else:
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
