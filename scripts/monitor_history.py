#!/usr/bin/env python3
"""
Monitor the scan history database
"""

from core.history_manager import HistoryManager
import time

def monitor_history():
    hm = HistoryManager()
    
    print("Monitoring scan history database...")
    print(f"Database: {hm.db_path}")
    print("=" * 70)
    
    last_count = 0
    
    try:
        while True:
            stats = hm.get_statistics()
            current_count = stats.get('total_scans', 0)
            
            if current_count != last_count:
                print(f"\n[{time.strftime('%H:%M:%S')}] Database updated!")
                print(f"Total scans: {current_count}")
                
                # Show recent scans
                recent = hm.get_recent_scans(limit=3)
                print("\nRecent scans:")
                for scan in recent:
                    print(f"  #{scan['id']}: {scan['scan_type']} | "
                          f"{scan['total_results']} results | "
                          f"{scan['source_path']}")
                
                print("-" * 70)
                last_count = current_count
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_history()
