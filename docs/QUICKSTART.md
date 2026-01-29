# Quick Start Guide for Scout

## Installation

1. **Install Python 3.9 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python3 --version` or `python --version`

2. **Install dependencies**
   ```bash
   cd scout
   pip install -r requirements.txt
   ```
   
   Or install globally:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run Scout**
   ```bash
   python main.py
   ```
   
   Or on some systems:
   ```bash
   python3 main.py
   ```

## Platform-Specific Notes

### macOS
- Use `python3` and `pip3` commands
- May need to install Xcode Command Line Tools
- No additional dependencies needed

### Windows
- Use `python` and `pip` commands
- Install from python.org (ensure "Add Python to PATH" is checked)
- No additional dependencies needed

### Linux (Ubuntu/Debian)
```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip python3-tk

# Install Scout dependencies
pip3 install -r requirements.txt

# Run Scout
python3 main.py
```

### Linux (Fedora/RHEL)
```bash
# Install Python and pip
sudo dnf install python3 python3-pip python3-tkinter

# Install Scout dependencies
pip3 install -r requirements.txt

# Run Scout
python3 main.py
```

## Usage

1. **Launch Scout** - Run `python main.py`
2. **Select Folder** - Click "Select Folder" and choose a directory
3. **Scan** - Click "🔍 Scan Files" button
4. **View Results** - Browse abbreviations in the table
5. **Search** - Use the search box to filter results
6. **Export** - Click "💾 Export Report" to save findings

## Troubleshooting

### "No module named 'ttkbootstrap'"
```bash
pip install ttkbootstrap
```

### "No module named 'docx'"
```bash
pip install python-docx
```

### "No module named 'PyPDF2'"
```bash
pip install PyPDF2
```

### GUI doesn't appear
- Ensure tkinter is installed (usually comes with Python)
- On Linux, install python3-tk package

### Permission errors
- Run with appropriate permissions
- On macOS/Linux, may need to allow access to folders in System Preferences

## Building Standalone Executable

### Install PyInstaller
```bash
pip install pyinstaller
```

### Build for your platform
```bash
pyinstaller --onefile --windowed --name Scout main.py
```

The executable will be in the `dist/` folder.

### Advanced build options

**macOS with icon:**
```bash
pyinstaller --onefile --windowed --name Scout --icon=assets/icon.icns main.py
```

**Windows with icon:**
```bash
pyinstaller --onefile --windowed --name Scout --icon=assets/icon.ico main.py
```

**Linux:**
```bash
pyinstaller --onefile --name Scout main.py
```

## Getting Help

- Check the [README.md](README.md) for full documentation
- Report issues on GitHub
- Contact support team

## Next Steps

- Customize theme in [main.py](main.py#L18) (line 18)
- Adjust abbreviation detection in [core/extractor.py](core/extractor.py)
- Add custom file formats in [core/parser.py](core/parser.py)

Happy exploring! 🔍
