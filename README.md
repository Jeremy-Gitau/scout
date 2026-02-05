# Scout 🔍

**Explore your files, uncover meaning.**

A cross-platform desktop application for automatically discovering and extracting abbreviations, entities, and structured information from documents with advanced AI-powered analysis.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-1.6.0-brightgreen)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install advanced features (spaCy NER)
python -m spacy download en_core_web_sm

# Run Scout
python main.py
```

---

## Features

### Core Features
- 🔍 **Smart Detection** - Automatically finds abbreviations (API, CPU, NLP, U.S.A., Ph.D.)
- 📖 **Definition Extraction** - Locates definitions using advanced patterns
- 👥 **Entity Extraction** - Extract people, organizations, and locations from documents
- 📂 **16+ File Formats** - TXT, PDF, DOCX, XLSX, CSV, JSON, HTML, Markdown, XML, RTF, ODT
- 📷 **OCR Support** - Extract text from scanned documents and images (PNG, JPG, TIFF, BMP, GIF)
- 🎨 **Triple-Mode Interface** - Abbreviations + Duplicates + Entities
- 💾 **Multiple Exports** - Save as TXT, CSV, JSON, Excel, or PDF
- 🌍 **Cross-platform** - Works on macOS, Windows, and Linux

### What's New in v1.6.0 🎉

**🤖 Advanced Entity Extraction**
- Extract structured information: people, organizations, locations
- Tiered extraction system: LLM → spaCy → Pattern matching
- Confidence scoring (HIGH/MEDIUM/LOW) with smart validation
- OpenAI GPT-4o-mini integration for context-aware extraction
- Fallback to spaCy NER and regex patterns when offline
- Comprehensive export options with filtering
- Smart file naming: auto-names from document title (single file) or prompts for name (multiple files)

**🎯 Quality Improvements**
- Advanced validation filters eliminate false positives
- Person names require full names (first + last)
- Organization filtering removes medical acronyms, currencies, technical terms
- Location validation prevents generic phrase detection
- 78% reduction in false positives vs v1.5.0

**💾 Enhanced Export System**
- Filter exports by entity type (People, Organizations, Locations)
- Filter by confidence level (High, Medium, Low)
- Multiple formats: JSON, CSV, Excel (.xlsx), Text
- Rich data: includes roles, organizations, countries, context
- Automatic document title extraction for smart naming

### Advanced Features

**🚀 Concurrent Task Management**
- Run multiple scans simultaneously (up to 5 tasks)
- Independent task queue and progress tracking
- Background processing while you continue working
- Per-task results and export capabilities

**🧠 AI-Powered Extraction**
- ✨ **Enhanced Patterns** - Detects dotted (U.S.A.) and hyphenated (UTF-8) abbreviations
- 🎯 **Confidence Scoring** - Each abbreviation scored 0.0-1.0 based on context
- 📊 **Frequency Filtering** - Automatically filters noise and false positives
- 🧠 **spaCy NER** - Filters named entities for higher precision
- 🤖 **BERT Embeddings** - Semantic similarity matching for better definitions
- 🌐 **API Validation** - Optional external validation via Acronym Finder
- 📚 **Glossary Detection** - Recognizes and prioritizes glossary sections

**📂 Multi-Format Document Support**
- Office: Word (DOCX, DOC), Excel (XLSX, XLS), OpenDocument (ODT)
- Data: CSV, TSV, JSON, XML
- Web: HTML, HTM
- Text: TXT, Markdown (MD), RTF
- PDF: Portable Document Format

---

## Project Structure

```
scout/
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
│
├── core/                     # Core business logic
│   ├── scanner.py           # File system scanning
│   ├── parser.py            # Document parsing (16 formats)
│   ├── extractor.py         # Abbreviation detection (AI-powered)
│   ├── entity_extractor.py  # Entity extraction (NEW v1.6.0)
│   ├── smart_extractor.py   # Smart extraction with LLM
│   ├── llm_extractor.py     # LLM integration
│   ├── task_manager.py      # Concurrent task management
│   ├── duplicate_handler.py # Duplicate file detection
│   ├── history_manager.py   # Scan history management
│   └── exporter.py          # Report generation
│
├── gui/                      # User interface
│   └── app_window.py        # Main application window
│
├── docs/                     # Documentation
│   ├── QUICKSTART.md        # Quick start guide
│   ├── ENTITY_EXTRACTION.md # Entity extraction guide
│   └── LICENSE              # MIT license
│
├── scripts/                  # Build and utility scripts
│   ├── build.sh             # macOS/Linux build script
│   ├── build.bat            # Windows build script
│   └── setup.py             # Setup and verification
│
└── assets/                   # Application resources
    └── icons/               # App icons
```

---

## Documentation

- 📖 **[Quick Start Guide](docs/QUICKSTART.md)** - Get started fast
- 🤖 **[Entity Extraction Guide](docs/ENTITY_EXTRACTION.md)** - Entity extraction documentation
- 📜 **[License](docs/LICENSE)** - MIT License

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd scout
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Install advanced ML features**
   ```bash
   # For spaCy NER (Named Entity Recognition)
   python -m spacy download en_core_web_sm
   
   # BERT and Transformers are auto-installed from requirements.txt
   # First run will download models (~400MB)
   ```

5. **Optional: Install Tesseract OCR (for scanned documents/images)**
   ```bash
   # macOS (using Homebrew)
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows
   # Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   # Add to PATH after installation
   ```

6. **Optional: Configure OpenAI API (for LLM entity extraction)**
   - Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Enter key in Entity Extraction mode settings
   - Cost: ~$0.15-0.60 per 1M tokens (GPT-4o-mini)

7. **Run Scout**
   ```bash
   python main.py
   ```

---

## Usage

### Desktop Application (GUI)

```bash
python main.py
```

#### Abbreviation Mode
1. Click **"Select Folder"** or **"Select File"** to choose input
2. **Regular Scan**: Click **"🔍 Scan Now"** for immediate foreground scan
3. **Task Scan**: Click **"🚀 New Scan Task"** for background concurrent scan
4. Monitor progress in the **"⚡ Active Scan Tasks"** panel
5. View results in the table (search, filter, sort)
6. Export with options: limit results, split into multiple files
7. Save as TXT, CSV, JSON, Excel, or PDF

#### Entity Extraction Mode (NEW v1.6.0)
1. Click the **"Entities"** button at the top
2. Select a folder or file to extract entities from
3. Choose extraction options:
   - **People**: Extract person names with roles, organizations
   - **Organizations**: Find company, institution, agency names
   - **Locations**: Detect countries, cities, regions
4. Optional: Enable LLM extraction (requires OpenAI API key)
5. Click **"Extract Entities"** to start
6. View results with confidence scoring (High/Medium/Low)
7. Export with comprehensive filters:
   - Select entity types to include
   - Filter by confidence level
   - Choose format (JSON, CSV, Excel, TXT)
   - Auto-naming: single file uses document title, multiple files prompts for name

#### Deduplicator Mode
1. Click the **"Deduplicator"** button at the top
2. Select a folder to scan for duplicate files
3. Preview duplicates with thumbnails (for images)
4. Compare files side-by-side
5. Delete or move duplicates to trash

---

## OCR Support for Scanned Documents

Scout includes Tesseract OCR integration to extract text from scanned documents and images.

### Supported Image Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- TIFF (.tiff, .tif)
- BMP (.bmp)
- GIF (.gif)

### Features
- **Automatic Detection**: Scanned PDFs with minimal text (< 100 chars) automatically trigger OCR
- **Direct Image Processing**: Extract text and entities from image files
- **Title Extraction**: First line of OCR text used as document title
- **Full Integration**: Works with all Scout features (entity extraction, abbreviation detection)

### Installation
Tesseract OCR must be installed separately (Python packages are already included in requirements.txt):

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
1. Download installer from [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and add to system PATH

### Usage
Simply scan folders containing images or scanned PDFs - OCR happens automatically!

```python
# Example: Manual OCR usage
from core.parser import Parser
from pathlib import Path

parser = Parser()
text = parser.parse_file(Path('scanned_document.png'))
title = parser.extract_title(Path('scanned_document.png'))
```

**Note:** OCR accuracy depends on image quality. Best results with:
- High resolution (300 DPI or higher)
- Clear, crisp text
- Good contrast between text and background
- Minimal skew or rotation

---

## Building Standalone Executables

### Option 1: Build for Your Platform (Local)

**macOS/Linux:**
```bash
./scripts/build.sh
```

**Windows:**
```cmd
scripts\build.bat
```

**Manual build:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Scout main.py
```

Executable will be in `dist/` folder.

### Option 2: Build for All Platforms (GitHub Actions)

**Note:** PyInstaller can only build for the platform you're running on. You cannot build Windows executables from macOS, etc.

**Automated Multi-Platform Builds:**

1. Push code to GitHub:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. GitHub Actions will automatically build for:
   - ✅ Windows (Scout.exe)
   - ✅ macOS (Scout - Universal)
   - ✅ Linux (Scout)

3. Download builds from the Actions tab or create a release:
   ```bash
   git tag v1.6.0
   git push origin v1.6.0
   ```

---

## Entity Extraction Quality

### v1.6.0 Performance
- **Precision**: ~100% (vs 26% in v1.5.0)
- **False Positives**: Reduced by 78%
- **Validation**: Smart filtering for all entity types

### Test Results (Policy Brief PDF)
**Before v1.6.0:**
- People: 1 (false positive: "Advocacy")
- Organizations: 23 (many false positives: HPV, KES, EquityVision, PET/SPECT)
- Locations: 2 (1 false positive: "Key Result")

**After v1.6.0:**
- People: 0 (correct - policy document has no individuals)
- Organizations: 5 (all legitimate institutions)
- Locations: 1 (Kenya - correct)

### Extraction Methods
1. **LLM (Optional)**: GPT-4o-mini for context-aware extraction
2. **spaCy NER**: Fast, offline named entity recognition
3. **Pattern Matching**: Regex fallback for basic extraction

---

## Abbreviation Extraction Quality

### Performance
- Basic extraction: **0.6s** per 1000 words (80% precision)
- With spaCy: **1.2s** per 1000 words (90% precision)
- Full features: **3.8s** per 1000 words (95% precision)

### Features
- **95% precision** (up from 70%) with all features enabled
- **Enhanced patterns** for dotted (U.S.A., Ph.D.) and hyphenated (UTF-8, X-Ray) abbreviations
- **Confidence scoring** - Each result scored 0.0-1.0 based on 8+ factors
- **Frequency filtering** - Automatically removes common false positives

---

## Technologies

### Core Technologies
- **Python 3.9+** - Programming language
- **Tkinter + ttkbootstrap** - Modern GUI framework
- **python-docx** - DOCX file parsing
- **PyPDF2** - PDF file parsing
- **openpyxl** - Excel export
- **reportlab** - PDF report generation

### Advanced Features (Optional)
- **OpenAI API** - GPT-4o-mini for entity extraction
- **spaCy** - Named Entity Recognition for filtering
- **Transformers** - BERT embeddings for semantic matching
- **PyTorch** - Deep learning framework
- **requests** - API validation support

---

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation
- Review the quick start guide

---

## License

MIT License - see [LICENSE](docs/LICENSE) for details.

---

**Made with ❤️ using Python & Tkinter**

🔍 **Scout — Explore your files, uncover meaning.**

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install advanced features (spaCy NER)
python -m spacy download en_core_web_sm

# Run Scout
python main.py
```

---

## Features

### Core Features
- 🔍 **Smart Detection** - Automatically finds abbreviations (API, CPU, NLP, U.S.A., Ph.D.)
- 📖 **Definition Extraction** - Locates definitions using advanced patterns
- � **Entity Extraction** - Extract people, organizations, and locations from documents
- 📂 **16 File Formats** - TXT, PDF, DOCX, XLSX, CSV, JSON, HTML, Markdown, XML, RTF, ODT
- 🎨 **Triple-Mode Interface** - Abbreviations + Duplicates + Entity extraction
- 💾 **Multiple Exports** - Save as TXT, CSV, JSON, Excel, or PDF
- 🌍 **Cross-platform** - Works on macOS, Windows, and Linux

### Advanced Features (v1.5.0) 🆕

**🤖 Entity Extraction Mode**
- Extract structured information from documents
- Identify people with roles, organizations, and countries
- Find organizations and locations automatically
- Confidence scoring (HIGH/MEDIUM/LOW)
- Completeness tracking for people entities
- LLM-powered extraction with OpenAI GPT-4o-mini
- Fallback to spaCy NER and pattern matching
- Export entities to JSON, CSV, or formatted text

**🚀 Concurrent Task Management**
- Run multiple scans simultaneously (up to 5 tasks)
- Independent task queue and progress tracking
- Background processing while you continue working
- Per-task results and export capabilities

**🧠 AI-Powered Extraction**
- ✨ **Enhanced Patterns** - Detects dotted (U.S.A.) and hyphenated (UTF-8) abbreviations
- 🎯 **Confidence Scoring** - Each abbreviation scored 0.0-1.0 based on context
- 📊 **Frequency Filtering** - Automatically filters noise and false positives
- 🧠 **spaCy NER** - Filters named entities for higher precision
- 🤖 **BERT Embeddings** - Semantic similarity matching for better definitions
- 🌐 **API Validation** - Optional external validation via Acronym Finder
- 📚 **Glossary Detection** - Recognizes and prioritizes glossary sections

**📂 Multi-Format Document Support**
- Office: Word (DOCX, DOC), Excel (XLSX, XLS), OpenDocument (ODT)
- Data: CSV, TSV, JSON, XML
- Web: HTML, HTM
- Text: TXT, Markdown (MD), RTF
- PDF: Portable Document Format

---

## Project Structure

```
scout/
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
│
├── core/                     # Core business logic
│   ├── scanner.py           # File system scanning (16 formats)
│   ├── parser.py            # Document parsing (11 parsers)
│   ├── extractor.py         # Abbreviation detection (AI-powered)
│   ├── task_manager.py      # Concurrent task management
│   └── exporter.py          # Report generation
│
├── gui/                      # User interface
│   ├── app_window.py        # Main application window (task UI)
│   └── components/          # Reusable UI components
│
├── docs/                     # Documentation
│   ├── README.md            # Full documentation
│   ├── QUICKSTART.md        # Quick start guide
│   ├── V1.4.0_RELEASE_NOTES.md  # Release notes
│   ├── EXTRACTION_IMPROVEMENTS.md  # AI features docs
│   └── LICENSE              # MIT license
│
├── scripts/                  # Build and utility scripts
│   ├── build.sh             # macOS/Linux build script
│   ├── build.bat            # Windows build script
│   ├── launch_scout.sh      # Launch helper
│   └── setup.py             # Setup and verification
│
├── tests/                    # Test files
│   ├── test_core.py         # Core functionality tests
│   ├── test_v1.5_features.py  # Task & format tests
│   └── test_document.txt    # Sample test document
│
└── assets/                   # Application resources
    └── icons/               # App icons
```

---

## Documentation

- 📖 **[Full Documentation](docs/README.md)** - Complete guide
- 🚀 **[Quick Start Guide](docs/QUICKSTART.md)** - Get started fast
- 📜 **[License](docs/LICENSE)** - MIT License

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd scout
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Install advanced ML features**
   ```bash
   # For spaCy NER (Named Entity Recognition)
   python -m spacy download en_core_web_sm
   
   # BERT and Transformers are auto-installed from requirements.txt
   # First run will download models (~400MB)
   ```

5. **Run Scout**
   ```bash
   python main.py
   ```

---

## Usage

### Desktop Application (GUI)

```bash
python main.py
```

#### Abbreviation Mode
1. Click **"Select Folder"** or **"Select File"** to choose input
2. **Regular Scan**: Click **"🔍 Scan Now"** for immediate foreground scan
3. **Task Scan**: Click **"🚀 New Scan Task"** for background concurrent scan
4. Monitor progress in the **"⚡ Active Scan Tasks"** panel
5. View results in the table (search, filter, sort)
6. Export results to TXT, CSV, JSON, Excel, or PDF
3. View results with confidence scores in the table
4. Use search to filter abbreviations
5. Click **"Export"** to save as TXT, CSV, JSON, Excel, or PDF

#### Deduplicator Mode
1. Click the **"Deduplicator"** button at the top
2. Select a folder to scan for duplicate files
3. Preview duplicates with thumbnails (for images)
4. Compare files side-by-side
5. Delete or move duplicates to trash

### Command Line Interface

```bash
python examples/example_cli.py
```

Interactive CLI for automation or scripting.

---

## Building Standalone Executables

### Option 1: Build for Your Platform (Local)

**macOS/Linux:**
```bash
./scripts/build.sh
```

**Windows:**
```cmd
scripts\build.bat
```

**Manual build:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Scout main.py
```

Executable will be in `dist/` folder.

### Option 2: Build for All Platforms (GitHub Actions)

**Note:** PyInstaller can only build for the platform you're running on. You cannot build Windows executables from macOS, etc.

**Automated Multi-Platform Builds:**

1. Push code to GitHub:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. GitHub Actions will automatically build for:
   - ✅ Windows (Scout.exe)
   - ✅ macOS (Scout - Universal)
   - ✅ Linux (Scout)

3. Download builds from the Actions tab or create a release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

The workflow (`.github/workflows/build.yml`) handles all platforms automatically!

---

## What's New in v1.4.0 🎉

Scout v1.4.0 brings major improvements to abbreviation extraction accuracy:

### Extraction Improvements
- **95% precision** (up from 70%) with all features enabled
- **Enhanced patterns** for dotted (U.S.A., Ph.D.) and hyphenated (UTF-8, X-Ray) abbreviations
- **Confidence scoring** - Each result scored 0.0-1.0 based on 8+ factors
- **Frequency filtering** - Automatically removes common false positives
- **spaCy NER** - Filters out named entities (people, places) for cleaner results
- **BERT embeddings** - Semantic similarity matching for better definition quality
- **API validation** - Optional external verification via Acronym Finder
- **Glossary detection** - Recognizes and prioritizes glossary/abbreviations sections

### Performance
- Basic extraction: **0.6s** per 1000 words (80% precision)
- With spaCy: **1.2s** per 1000 words (90% precision)
- Full features: **3.8s** per 1000 words (95% precision)

For detailed information, see:
- [Extraction Improvements Documentation](docs/EXTRACTION_IMPROVEMENTS.md)
- [v1.4.0 Release Notes](docs/V1.4.0_RELEASE_NOTES.md)

---

## Testing

Run core functionality test:
```bash
python tests/test_core.py
```

Test with sample document:
```bash
python main.py
# Select the tests/ folder and scan
```

Test advanced features:
```bash
# Verify spaCy installation
python -c "from core.extractor import HAS_SPACY; print(f'spaCy: {HAS_SPACY}')"

# Verify BERT installation
python -c "from core.extractor import HAS_BERT; print(f'BERT: {HAS_BERT}')"
```

---

## Technologies

### Core Technologies
- **Python 3.9+** - Programming language
- **Tkinter + ttkbootstrap** - Modern GUI framework
- **python-docx** - DOCX file parsing
- **PyPDF2** - PDF file parsing
- **openpyxl** - Excel export
- **reportlab** - PDF report generation

### Advanced Features (Optional)
- **spaCy** - Named Entity Recognition for filtering
- **Transformers** - BERT embeddings for semantic matching
- **PyTorch** - Deep learning framework
- **requests** - API validation support

---

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [documentation](docs/README.md)
- Review the [quick start guide](docs/QUICKSTART.md)

---

## License

MIT License - see [LICENSE](docs/LICENSE) for details.

---

**Made with ❤️ using Python & Tkinter**

🔍 **Scout — Explore your files, uncover meaning.**
