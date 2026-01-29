"""
Scanner module for traversing directories and finding documents.
Cross-platform file scanning with support for multiple document formats.
"""

import os
from pathlib import Path
from typing import List, Set


class Scanner:
    """Scans directories for supported document files."""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}
    
    def __init__(self):
        self.files_found: List[Path] = []
        self.total_size: int = 0
        
    def scan_directory(self, directory_path: str) -> List[Path]:
        """
        Recursively scan a directory for supported documents.
        
        Args:
            directory_path: Path to the directory to scan
            
        Returns:
            List of Path objects for found documents
        """
        self.files_found = []
        self.total_size = 0
        
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")
        
        # Recursively walk through directory
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories (cross-platform)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file has supported extension
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    try:
                        # Check if file is readable
                        if os.access(file_path, os.R_OK):
                            self.files_found.append(file_path)
                            self.total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        # Skip files that can't be accessed
                        continue
        
        return self.files_found
    
    def scan_multiple_directories(self, directory_paths: List[str]) -> List[Path]:
        """
        Scan multiple directories and return combined results.
        
        Args:
            directory_paths: List of directory paths to scan
            
        Returns:
            Combined list of found documents (duplicates removed)
        """
        all_files: Set[Path] = set()
        self.total_size = 0
        
        for directory_path in directory_paths:
            try:
                files = self.scan_directory(directory_path)
                all_files.update(files)
            except (FileNotFoundError, NotADirectoryError) as e:
                print(f"Warning: {e}")
                continue
        
        self.files_found = sorted(list(all_files))
        
        # Recalculate total size
        self.total_size = sum(f.stat().st_size for f in self.files_found)
        
        return self.files_found
    
    def get_stats(self) -> dict:
        """
        Get statistics about the scan.
        
        Returns:
            Dictionary with scan statistics
        """
        return {
            'total_files': len(self.files_found),
            'total_size_bytes': self.total_size,
            'total_size_mb': round(self.total_size / (1024 * 1024), 2),
            'by_extension': self._count_by_extension()
        }
    
    def _count_by_extension(self) -> dict:
        """Count files by extension."""
        counts = {}
        for file_path in self.files_found:
            ext = file_path.suffix.lower()
            counts[ext] = counts.get(ext, 0) + 1
        return counts
    
    @staticmethod
    def is_supported_file(file_path: str) -> bool:
        """
        Check if a file is supported by Scout.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is supported, False otherwise
        """
        return Path(file_path).suffix.lower() in Scanner.SUPPORTED_EXTENSIONS
