# Scout 🔍

**Explore your files, uncover meaning.**

A cross-platform desktop application for automatically discovering and extracting abbreviations and their definitions from documents.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run Scout
python main.py
```

---

## Features

- 🔍 **Smart Detection** - Automatically finds abbreviations (API, CPU, NLP, etc.)
- 📖 **Definition Extraction** - Locates definitions in context
- 📂 **Multi-format Support** - Reads TXT, PDF, and DOCX files
- 🎨 **Modern UI** - Beautiful interface with ttkbootstrap
- 💾 **Multiple Exports** - Save as TXT, CSV, or JSON
- 🌍 **Cross-platform** - Works on macOS, Windows, and Linux

---

## Project Structure

```
scout/
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
│
├── core/                     # Core business logic
│   ├── scanner.py           # File system scanning
│   ├── parser.py            # Document parsing
│   ├── extractor.py         # Abbreviation detection
│   └── exporter.py          # Report generation
│
├── gui/                      # User interface
│   ├── app_window.py        # Main application window
│   └── components/          # Reusable UI components
│
├── docs/                     # Documentation
│   ├── README.md            # Full documentation
│   ├── QUICKSTART.md        # Quick start guide
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
│   └── test_document.txt    # Sample test document
│
├── examples/                 # Usage examples
│   └── example_cli.py       # Command-line interface example
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

4. **Run Scout**
   ```bash
   python main.py
   ```

---

## Usage

### Desktop Application (GUI)

```bash
python main.py
```

1. Click **"Select Folder"** to choose a directory
2. Click **"Scan Files"** to start processing
3. View results in the table
4. Use search to filter abbreviations
5. Click **"Export"** to save your report

### Command Line Interface

```bash
python examples/example_cli.py
```

Interactive CLI for automation or scripting.

---

## Building Standalone Executable

### Using provided scripts:

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

---

## Technologies

- **Python 3.9+** - Programming language
- **Tkinter + ttkbootstrap** - Modern GUI framework
- **python-docx** - DOCX file parsing
- **PyPDF2** - PDF file parsing

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
