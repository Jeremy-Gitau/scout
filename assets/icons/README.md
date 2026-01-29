# Scout Icon Assets

This directory contains icon files for Scout application.

## Required Icons

- **scout-logo.png** - Main application logo (256x256 recommended)
- **icon.ico** - Windows executable icon
- **icon.icns** - macOS application icon

## Creating Icons

You can create custom icons using any image editor or online tools.

For cross-platform compatibility:
- Use PNG format for logos and images
- Convert to .ico for Windows using online converters
- Convert to .icns for macOS using `iconutil` or online converters

## Example Icon Creation

```bash
# macOS: Create .icns from PNG
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
iconutil -c icns icon.iconset
```
