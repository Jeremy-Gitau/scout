"""
History Manager - Database handler for storing and retrieving scan history
"""

import sqlite3
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

class HistoryManager:
    """Manages scan history using SQLite database"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the history manager
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default location
        """
        if db_path is None:
            # Store in user's home directory
            home = Path.home()
            scout_dir = home / ".scout"
            scout_dir.mkdir(exist_ok=True)
            db_path = scout_dir / "scan_history.db"
        
        self.db_path = str(db_path)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    scan_date TIMESTAMP NOT NULL,
                    total_results INTEGER NOT NULL,
                    results_data TEXT NOT NULL,
                    settings TEXT,
                    notes TEXT
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scan_date 
                ON scans(scan_date DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scan_type 
                ON scans(scan_type)
            """)
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_scan(
        self,
        scan_type: str,
        source_path: str,
        source_type: str,
        results: Dict[str, Any],
        settings: Dict[str, Any] = None,
        notes: str = None
    ) -> int:
        """
        Save a scan to the history database
        
        Args:
            scan_type: Type of scan ('abbreviations' or 'duplicates')
            source_path: Path to the scanned file/directory
            source_type: 'file' or 'directory'
            results: Dictionary containing scan results
            settings: Optional dictionary of scan settings
            notes: Optional notes about the scan
        
        Returns:
            The ID of the saved scan
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            scan_date = datetime.datetime.now().isoformat()
            total_results = len(results) if isinstance(results, dict) else 0
            results_json = json.dumps(results, ensure_ascii=False)
            settings_json = json.dumps(settings) if settings else None
            
            cursor.execute("""
                INSERT INTO scans (
                    scan_type, source_path, source_type, scan_date,
                    total_results, results_data, settings, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_type, source_path, source_type, scan_date,
                total_results, results_json, settings_json, notes
            ))
            
            scan_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved scan #{scan_id}: {scan_type} of {source_path}")
            return scan_id
        except Exception as e:
            self.logger.error(f"Failed to save scan: {e}")
            raise
    
    def get_recent_scans(self, limit: int = 50, scan_type: str = None) -> List[Dict[str, Any]]:
        """
        Get recent scans from history
        
        Args:
            limit: Maximum number of scans to retrieve
            scan_type: Optional filter by scan type
        
        Returns:
            List of scan dictionaries (without full results data)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if scan_type:
                cursor.execute("""
                    SELECT id, scan_type, source_path, source_type, scan_date,
                           total_results, notes
                    FROM scans
                    WHERE scan_type = ?
                    ORDER BY scan_date DESC
                    LIMIT ?
                """, (scan_type, limit))
            else:
                cursor.execute("""
                    SELECT id, scan_type, source_path, source_type, scan_date,
                           total_results, notes
                    FROM scans
                    ORDER BY scan_date DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            scans = []
            for row in rows:
                scans.append({
                    'id': row['id'],
                    'scan_type': row['scan_type'],
                    'source_path': row['source_path'],
                    'source_type': row['source_type'],
                    'scan_date': row['scan_date'],
                    'total_results': row['total_results'],
                    'notes': row['notes']
                })
            
            return scans
        except Exception as e:
            self.logger.error(f"Failed to get recent scans: {e}")
            return []
    
    def load_scan(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a specific scan by ID
        
        Args:
            scan_id: The ID of the scan to load
        
        Returns:
            Dictionary containing full scan data, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM scans WHERE id = ?
            """, (scan_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Parse JSON data
            results_data = json.loads(row['results_data'])
            settings = json.loads(row['settings']) if row['settings'] else {}
            
            return {
                'id': row['id'],
                'scan_type': row['scan_type'],
                'source_path': row['source_path'],
                'source_type': row['source_type'],
                'scan_date': row['scan_date'],
                'total_results': row['total_results'],
                'results': results_data,
                'settings': settings,
                'notes': row['notes']
            }
        except Exception as e:
            self.logger.error(f"Failed to load scan {scan_id}: {e}")
            return None
    
    def delete_scan(self, scan_id: int) -> bool:
        """
        Delete a scan from history
        
        Args:
            scan_id: The ID of the scan to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                self.logger.info(f"Deleted scan #{scan_id}")
            return deleted
        except Exception as e:
            self.logger.error(f"Failed to delete scan {scan_id}: {e}")
            return False
    
    def clear_history(self, before_date: str = None) -> int:
        """
        Clear scan history
        
        Args:
            before_date: Optional ISO date string. If provided, only deletes scans before this date
        
        Returns:
            Number of scans deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if before_date:
                cursor.execute("DELETE FROM scans WHERE scan_date < ?", (before_date,))
            else:
                cursor.execute("DELETE FROM scans")
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {deleted} scans from history")
            return deleted
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about scan history
        
        Returns:
            Dictionary containing statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total scans
            cursor.execute("SELECT COUNT(*) FROM scans")
            total_scans = cursor.fetchone()[0]
            
            # Scans by type
            cursor.execute("""
                SELECT scan_type, COUNT(*) as count
                FROM scans
                GROUP BY scan_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Total results
            cursor.execute("SELECT SUM(total_results) FROM scans")
            total_results = cursor.fetchone()[0] or 0
            
            # First and last scan dates
            cursor.execute("SELECT MIN(scan_date), MAX(scan_date) FROM scans")
            first_scan, last_scan = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_scans': total_scans,
                'scans_by_type': by_type,
                'total_results': total_results,
                'first_scan': first_scan,
                'last_scan': last_scan
            }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def search_scans(self, query: str) -> List[Dict[str, Any]]:
        """
        Search scans by source path
        
        Args:
            query: Search query string
        
        Returns:
            List of matching scans
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, scan_type, source_path, source_type, scan_date,
                       total_results, notes
                FROM scans
                WHERE source_path LIKE ?
                ORDER BY scan_date DESC
                LIMIT 50
            """, (f"%{query}%",))
            
            rows = cursor.fetchall()
            conn.close()
            
            scans = []
            for row in rows:
                scans.append({
                    'id': row['id'],
                    'scan_type': row['scan_type'],
                    'source_path': row['source_path'],
                    'source_type': row['source_type'],
                    'scan_date': row['scan_date'],
                    'total_results': row['total_results'],
                    'notes': row['notes']
                })
            
            return scans
        except Exception as e:
            self.logger.error(f"Failed to search scans: {e}")
            return []
