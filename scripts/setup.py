#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

def print_header(text):
    
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")

def check_python_version():
    
    print_header("Checking Python Version")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required!")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_dependencies():
    
    print_header("Installing Dependencies")
    
    packages = [
        'ttkbootstrap>=1.10.1',
        'python-docx>=0.8.11',
        'PyPDF2>=3.0.0'
    ]
    
    print("Installing:")
    for package in packages:
        print(f"  • {package}")
    
    print()
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("\n✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install dependencies")
        return False

def verify_imports():
    
    print_header("Verifying Imports")
    
    modules = {
        'tkinter': 'Tkinter (GUI framework)',
        'ttkbootstrap': 'ttkbootstrap (Modern UI)',
        'docx': 'python-docx (DOCX parsing)',
        'PyPDF2': 'PyPDF2 (PDF parsing)'
    }
    
    all_ok = True
    
    for module_name, description in modules.items():
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except ImportError as e:
            print(f"❌ {description} - {e}")
            all_ok = False
    
    return all_ok

def run_test():
    
    print_header("Running Quick Test")
    
    try:
        from core.scanner import Scanner
        from core.parser import Parser
        from core.extractor import Extractor
        
        print("Testing core modules...")
        
        # Test scanner
        scanner = Scanner()
        print("✅ Scanner initialized")
        
        # Test parser
        parser = Parser()
        print("✅ Parser initialized")
        
        # Test extractor
        extractor = Extractor()
        print("✅ Extractor initialized")
        
        # Test on sample document
        test_file = Path('test_document.txt')
        if test_file.exists():
            print(f"\nTesting with {test_file.name}...")
            content = parser.parse_file(test_file)
            
            if content:
                extractor.extract_from_text(content, str(test_file))
                stats = extractor.get_statistics()
                
                print(f"✅ Found {stats['total_abbreviations']} abbreviations")
                print(f"   • With definitions: {stats['with_definitions']}")
                print(f"   • Without definitions: {stats['without_definitions']}")
                print(f"   • Coverage: {stats['coverage_percent']}%")
                
                # Show a few examples
                print("\n   Sample abbreviations:")
                for i, (abbrev, info) in enumerate(list(extractor.abbreviations.items())[:5]):
                    definition = info['definition'] or "No definition"
                    print(f"     {abbrev}: {definition}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    
    print("""
    ┌─────────────────────────────────────────┐
    │                                         │
    │      🔍 Scout Setup & Test             │
    │                                         │
    │   Explore your files, uncover meaning   │
    │                                         │
    └─────────────────────────────────────────┘
    
✅ Scout is ready to use!

To launch Scout:
    python main.py

To try the CLI version:
    python example_cli.py

To build standalone executable:
    ./build.sh          (macOS/Linux)
    build.bat           (Windows)

For more information:
    • README.md         - Complete documentation
    • QUICKSTART.md     - Quick start guide
    • PROJECT_OVERVIEW.md - Project structure

Happy exploring! 🔍
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
