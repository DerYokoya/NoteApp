# NoteApp

A professional, feature-rich desktop note-taking application built with Python and PyQt6.

Designed as a real-world alternative to Word and Notepad++, with full rich text editing, tables, images, and more.

## Video Showcase

https://github.com/user-attachments/assets/1527588c-eb6e-4ff5-95ea-7a55aedc036c

## Screenshots
![Main window](screenshots/screenshot_main.png)
![Fonts panel](screenshots/screenshot_fonts.png)
![Text formatting](screenshots/screenshot_formatting.png)
![Table formatting](screenshots/screenshot_table_format.png)
![Image function available](screenshots/screenshot_image.png)
![Search bar](screenshots/screenshot_search.png)

## ✨ Features

### Document Management
- 📝 **Multi-tab editing** — Open multiple documents in tabs, drag to reorder
- 💾 **Local file persistence** — Save as HTML (with formatting) or plain text
- 🔄 **Session recovery** — Automatically restores open tabs on launch
- 📂 **Drag & drop** — Open files by dragging them onto the window
- ⏱️ **Auto-save indicator** — Visual indicator (●) shows unsaved changes

### Text Formatting & Styles
- **Text styles** — Normal, Title, Subtitle, Heading 1-6 (auto-sized)
- **Character formatting** — Bold, Italic, Underline, Strikethrough
- **Text color** — Choose any color for text with live preview
- **Highlight color** — Apply background highlighting to selections
- **Text alignment** — Left, Center, Right, Justify (with keyboard shortcuts)
- **Clear formatting** — Remove all formatting with one click

### Content Organization
- 📋 **Lists** — Bullet lists and numbered lists with automatic indentation
- 📊 **Tables** — Insert tables with full control over:
  - Rows and columns (add/remove dynamically)
  - Cell padding and spacing
  - Column widths (percentage-based)
  - Border style, width, and color
  - Background colors
- **Horizontal lines** — Insert visual separators with a single click
- **Indentation controls** — Increase/decrease indent for paragraphs

### Media & Links
- 🖼️ **Image insertion** — Insert PNG, JPG, GIF, BMP with:
  - Custom sizing dialog (width, height, aspect ratio locking)
  - Right-click resize after insertion
  - Automatic scaling for large images
- 🔗 **Hyperlinks** — Create clickable links with:
  - Smart detection of existing links
  - Edit mode for updating URLs
  - **Ctrl+Click to open** in default browser

### Search & Navigation
- 🔍 **Find & replace** — Fast in-document search with:
  - Case-sensitive matching option
  - Visible highlighting (readable dark gold + black text)
  - Match counter (e.g., "3/10")
  - Find next/previous navigation
- 📍 **Status bar** — Shows current line, column, word count, character count

### User Interface
- 🎨 **Professional dark theme** — Easy on the eyes, modern design
- 🧭 **Two-row toolbar** — Organized formatting controls:
  - Row 1: Font, size, styles, colors, link, clear
  - Row 2: Alignment, lists, indent, tables, line, image
- ⌨️ **Right-click context menu** — Table operations, alignment, formatting
- 💾 **Auto-save** — Settings and session state saved automatically

## 📖 Keyboard Shortcuts

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
| `Esc` | Close Search Bar |

### Text Formatting
| Shortcut | Action |
|----------|--------|
| `Ctrl + B` | Bold |
| `Ctrl + I` | Italic |
| `Ctrl + U` | Underline |
| `Ctrl + K` | Insert/Edit Link |
| `Ctrl + \` | Clear Formatting |

### Alignment
| Shortcut | Action |
|----------|--------|
| `Ctrl + L` | Align Left |
| `Ctrl + E` | Center |
| `Ctrl + R` | Align Right |
| `Ctrl + J` | Justify |

### Lists & Tables
| Shortcut | Action |
|----------|--------|
| `Ctrl + Shift + L` | Bullet List |
| `Ctrl + Shift + N` | Numbered List |
| `Ctrl + T` | Insert Table |
| `Ctrl + Shift + T` | Table Properties |
| `Tab` | Increase Indent |
| `Shift + Tab` | Decrease Indent |

### Tab Navigation
| Shortcut | Action |
|----------|--------|
| `Ctrl + 1` through `Ctrl + 8` | Switch to Tab 1-8 |
| `Ctrl + 9` | Switch to Last Tab |

## 🔗 Links

**Creating Links:**
1. Select text (or just position cursor)
2. Press `Ctrl + K` or click the 🔗 button
3. Enter the URL
4. Done! Text appears blue and underlined

**Editing Links:**
1. Click on the linked text
2. Press `Ctrl + K` again
3. Edit dialog shows current URL
4. Update and confirm

**Opening Links:**
- Hold `Ctrl` and click on any link
- Opens in your default browser automatically

## 🖼️ Images

**Inserting Images:**
1. Click the 🖼️ button or go to Format → Insert Image
2. Select an image file
3. Size dialog appears with aspect ratio locking
4. Click OK to insert

**Resizing Images:**
1. Right-click on an image
2. Select "Resize Image…"
3. Adjust width/height (aspect ratio can be locked)
4. Apply changes

## 📊 Tables

**Creating Tables:**
1. Click ⊞ Table button or press `Ctrl + T`
2. Enter rows and columns
3. Table inserted with basic styling

**Table Properties:**
1. Click inside the table
2. Click ⊟ Props button or press `Ctrl + Shift + T`
3. Adjust:
   - **Structure**: Width, padding, spacing, add/remove rows & columns
   - **Borders**: Style, width, color, background color
   - **Columns**: Individual column widths (percentage-based)
4. Apply changes

**In-Table Shortcuts:**
- Right-click for context menu (insert/delete rows/columns)
- Increase cell spacing in Structure tab for grid effect

## 💡 Tips & Tricks

- **Session Recovery**: Close the app and your open tabs are restored on next launch
- **Rich Files**: Save as `.html` to preserve all formatting, or `.txt` for plain text
- **Search Highlighting**: Easily visible with dark gold background
- **Style Shortcuts**: Use the Text Styles dropdown for instant Heading/Title formatting
- **Grid Tables**: Increase cell spacing in Table Properties for a full grid look
- **Ctrl+Click Links**: The fastest way to open URLs while editing

## 📋 Status Bar

The status bar at the bottom shows:
- **File path** — Current document location (or "No file" if unsaved)
- **Line & Column** — Current cursor position
- **Word count** — Number of words and characters
- **Encoding** — Always UTF-8

Unsaved changes are marked with **●** in the tab title.

## ⚙️ Installation

### Requirements
- Python 3.10+
- PyQt6

### Setup
```bash
git clone https://github.com/DerYokoya/NoteApp.git
cd NoteApp
pip install -r requirements.txt
python main.py
```

## 📁 File Support

- **HTML** (.html) — Full formatting preserved (recommended for rich text)
- **Plain Text** (.txt) — Simple text without formatting
- **Auto-detection** — Opens in appropriate mode based on file type

## 🎯 Use Cases

Perfect for:
- ✍️ Writing and note-taking
- 📑 Document editing with rich formatting
- 📊 Quick table creation and data organization
- 🔗 Reference documents with hyperlinks
- 📸 Mixed media documents (text + images)
- 💼 Professional writing with full control

## 🚀 What Makes NoteApp Different

Unlike basic text editors, NoteApp provides:
- **Professional formatting**
- **Lightweight & fast** — No unnecessary dependencies
- **Local-first** — All files saved locally, no cloud required
- **Session persistence** — Your work survives crashes
- **User-friendly toolbar** — Everything organized logically
- **Keyboard-first** — Every major feature has a shortcut
- **Dark theme** — Easy on the eyes for long editing sessions

## 🤝 Contributing

Contributions welcome! Feel free to report issues or suggest features.

## 📄 License

This project is open source and available under the MIT License.

---

**NoteApp** — Professional note-taking, designed for distraction-free writing.
