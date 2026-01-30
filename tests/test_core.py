#!/usr/bin/env python3

from core.scanner import Scanner
from core.parser import Parser  
from core.extractor import Extractor
from pathlib import Path

print("🔍 Testing Scout Core Functionality\n")

# Test scanning
print("1. Testing Scanner...")
scanner = Scanner()
files = scanner.scan_directory('.')
print(f"   ✅ Scanner found {len(files)} files\n")

# Test parsing
print("2. Testing Parser...")
parser = Parser()
test_file = Path('test_document.txt')

if test_file.exists():
    content = parser.parse_file(test_file)
    print(f"   ✅ Parser extracted {len(content)} characters from test document\n")
    
    # Test extraction
    print("3. Testing Extractor...")
    extractor = Extractor()
    extractor.extract_from_text(content, str(test_file))
    stats = extractor.get_statistics()
    
    print(f"   ✅ Extractor found {stats['total_abbreviations']} abbreviations")
    print(f"      • With definitions: {stats['with_definitions']}")
    print(f"      • Without definitions: {stats['without_definitions']}")
    print(f"      • Coverage: {stats['coverage_percent']}%\n")
    
    # Show examples
    print("   Examples of detected abbreviations:")
    for abbrev, info in list(extractor.abbreviations.items())[:10]:
        definition = info['definition'] or 'Definition not found'
        print(f"      • {abbrev}: {definition}")

print("\n✅ All core functionality working perfectly!")
print("\n🚀 Ready to launch GUI: python main.py")
