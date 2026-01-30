import csv
import json
from pathlib import Path
from typing import Dict
from datetime import datetime

class Exporter:
    
    def __init__(self):
        self.last_export_path: Path = None
    
    def export_to_txt(self, abbreviations: Dict[str, dict], output_path: str) -> bool:
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 70 + "\n")
                f.write("SCOUT ABBREVIATION REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                
                # Statistics
                total = len(abbreviations)
                with_def = sum(1 for info in abbreviations.values() if info['definition'])
                
                f.write(f"Total Abbreviations: {total}\n")
                f.write(f"With Definitions: {with_def}\n")
                f.write(f"Without Definitions: {total - with_def}\n")
                f.write("\n" + "-" * 70 + "\n\n")
                
                # Abbreviations (sorted alphabetically)
                for abbrev in sorted(abbreviations.keys()):
                    info = abbreviations[abbrev]
                    definition = info['definition'] or "Definition not found"
                    count = info['count']
                    file_count = len(info['files'])
                    
                    # Format abbreviation entry
                    f.write(f"{abbrev}\n")
                    f.write(f"  Definition: {definition}\n")
                    f.write(f"  Occurrences: {count} time(s)\n")
                    f.write(f"  Found in: {file_count} file(s)\n")
                    
                    if info['files'] and file_count <= 3:
                        # Show all files if 3 or fewer
                        f.write(f"  Files: {', '.join(Path(fp).name for fp in info['files'])}\n")
                    elif info['files']:
                        # Show first 3 files with count of remaining
                        shown = ', '.join(Path(fp).name for fp in info['files'][:3])
                        remaining = file_count - 3
                        f.write(f"  Files: {shown} (and {remaining} more)\n")
                    
                    f.write("\n")
            
            self.last_export_path = output_file
            return True
            
        except Exception as e:
            print(f"Error exporting to TXT: {e}")
            return False
    
    def export_to_csv(self, abbreviations: Dict[str, dict], output_path: str) -> bool:
       
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Abbreviation', 'Definition', 'Occurrences', 
                               'File Count', 'Files'])
                
                # Data rows (sorted alphabetically)
                for abbrev in sorted(abbreviations.keys()):
                    info = abbreviations[abbrev]
                    definition = info['definition'] or "Definition not found"
                    count = info['count']
                    file_count = len(info['files'])
                    files = '; '.join(Path(f).name for f in info['files'])
                    
                    writer.writerow([abbrev, definition, count, file_count, files])
            
            self.last_export_path = output_file
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, abbreviations: Dict[str, dict], output_path: str) -> bool:
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data structure
            export_data = {
                'metadata': {
                    'generated': datetime.now().isoformat(),
                    'total_abbreviations': len(abbreviations),
                    'with_definitions': sum(1 for info in abbreviations.values() 
                                          if info['definition']),
                },
                'abbreviations': {}
            }
            
            # Add abbreviations
            for abbrev, info in abbreviations.items():
                export_data['abbreviations'][abbrev] = {
                    'definition': info['definition'],
                    'occurrences': info['count'],
                    'files': [str(Path(f).name) for f in info['files']]
                }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.last_export_path = output_file
            return True
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def export(self, abbreviations: Dict[str, dict], output_path: str, 
               format: str = 'txt') -> bool:
        
        format = format.lower()
        
        if format == 'txt':
            return self.export_to_txt(abbreviations, output_path)
        elif format == 'csv':
            return self.export_to_csv(abbreviations, output_path)
        elif format == 'json':
            return self.export_to_json(abbreviations, output_path)
        else:
            print(f"Unsupported format: {format}")
            return False
    
    def get_default_filename(self, format: str = 'txt') -> str:
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"scout_report_{timestamp}.{format}"
