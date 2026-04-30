# NoteApp

A lightweight, fast desktop note-taking application built with Python and PyQt6.

Designed for distraction-free writing with tabs, instant search, and local file storage.

## Features
- 📝 Create, edit, and manage notes
- 🗂 Tab-based document system
- 🔍 Fast in-app search
- 💾 Local file persistence
- ⚙️ Persistent user settings
- 🧪 Unit-tested core logic

## Showcase
https://github.com/user-attachments/assets/2838af1d-1bfd-46d8-8056-4906c39c8ab4

## Screenshots
![Main window](screenshots/screenshot_main.png)
![Search bar](screenshots/screenshot_search.png)

## Keyboard Shortcuts

### File Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl + N` | New Tab |
| `Ctrl + O` | Open File |
| `Ctrl + S` | Save |
| `Ctrl + Shift + S` | Save As |
| `Ctrl + W` | Close Tab |
| `Ctrl + Delete` | Delete File |
| `Ctrl + Q` | Quit Application |

### Edit Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo |
| `Ctrl + Y` | Redo |
| `Ctrl + F` | Find |
| `F3` | Find Next |
| `Shift + F3` | Find Previous |
| `Esc` | Close Search Bar (or Quit if search bar hidden) |

### Text Formatting
| Shortcut | Action |
|----------|--------|
| `Ctrl + B` | Bold |
| `Ctrl + I` | Italic |
| `Ctrl + U` | Underline |
| `Ctrl + \` | Clear Formatting |

### Lists & Tables
| Shortcut | Action |
|----------|--------|
| `Ctrl + Shift + L` | Bullet List |
| `Ctrl + Shift + N` | Numbered List |
| `Ctrl + T` | Insert Table |

### Tab Navigation
| Shortcut | Action |
|----------|--------|
| `Ctrl + 1` through `Ctrl + 8` | Switch to Tab 1-8 |
| `Ctrl + 9` | Switch to Last Tab |

## Status Indicators
- **●** (bullet symbol) in tab title indicates unsaved changes
- Status bar shows:
  - Current file path
  - Line and column position
  - Word and character count

## Tips
- Files can be opened as HTML (with formatting) or plain text
- Recent files are accessible from **File → Open Recent**
- Session automatically saves open tabs on exit and restores them on launch

## Installation

### Requirements
- Python 3.10+
- PyQt6

### Setup
```bash
git clone https://github.com/DerYokoya/NoteApp.git
cd NoteApp
pip install -r requirements.txt
python main.py
