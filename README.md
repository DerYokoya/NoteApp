# NoteApp

A modular, desktop rich-text editor built with Python and PyQt6, designed to explore how real-world document editors manage state, formatting, and user interaction.

---

## Video Showcase

https://github.com/user-attachments/assets/1527588c-eb6e-4ff5-95ea-7a55aedc036c

## Screenshots
![Main window](screenshots/screenshot_main.png)
![Fonts panel](screenshots/screenshot_fonts.png)
![Text formatting](screenshots/screenshot_formatting.png)
![Table formatting](screenshots/screenshot_table_format.png)
![Image function available](screenshots/screenshot_image.png)
![Search bar](screenshots/screenshot_search.png)

---

## Overview

NoteApp is a feature-rich desktop editor that supports multi-document workflows, structured content (tables, images), and persistent sessions.

The goal of this project was not just to replicate common editor features, but to **design a system that handles document state, formatting consistency, and user interaction at scale**.

---

## Architecture

The application is structured around separation of concerns between UI, document state, and persistence:

- **UI Layer (MainWindow / Widgets)**
  - Handles layout, toolbars, and user interactions
  - Dispatches actions to the editor and document logic
  - Custom widgets: SearchBar, StatusBarWidget, TablePropertiesDialog, TextOrientationDialog

- **Editor / Document Layer**
  - Manages text state, cursor behavior, and formatting operations
  - Encapsulates each document per tab for isolation

- **Persistence Layer**
  - Handles saving/loading documents (HTML and TXT)
  - Ensures formatting is preserved across sessions

- **Session Manager**
  - Stores open tabs and restores them on launch
  - Maintains continuity across application restarts

---

## Key Technical Decisions

- **HTML as storage format**
  - Chosen to preserve rich text, images, and structure without designing a custom format

- **Multi-tab document model**
  - Each tab maintains independent state to avoid cross-document interference

- **Local-first design**
  - No external dependencies or cloud integration, which ensures performance and reliability

- **PyQt6 for UI**
  - Enables fine-grained control over desktop interactions and complex widgets

---

## Challenges & Solutions

- **Rich text consistency**
  - Managing overlapping styles (bold, headings, colors) without conflicts required careful formatting control

- **Dynamic table manipulation**
  - Supporting row/column updates and styling without breaking layout integrity

- **Session persistence**
  - Ensuring tabs, file paths, and UI state are safely restored across launches

- **State synchronization**
  - Keeping UI indicators (e.g., unsaved ●) consistent with actual document changes

---

## Features (Selected)

### Document System
- Multi-tab editing with drag reordering
- Session recovery on restart
- HTML and plain text file support
- Drag & drop file opening

### Editing & Formatting
- Rich text styling (headings, inline formatting, colors)
- Lists, indentation, and alignment controls
- Clear formatting system
- Superscript & Subscript support
- Code blocks with monospace formatting
- Line spacing control (Single, 1.5x, Double)

### Structured Content
- Fully editable tables (rows, columns, styling)
- Image insertion with resizing and scaling
- Hyperlink creation and editing (Ctrl+Click navigation)
- Horizontal line separators

### Navigation & UX
- Find & replace with match tracking
- **Replace functionality (Ctrl+H)**
- Status bar (cursor position, word count)
- Keyboard-first workflow across all major actions
- Print support with PDF export

---

## System Design

The application is structured as a layered desktop system where user interactions flow from the UI into document logic and persistence.

### High-Level Flow
```
[User Actions]
    ↓
(MainWindow)

[MainWindow (app/main_window.py)]
    ↓
    ├─→ handles keyboard shortcuts
    ├─→ handles menu clicks
    ├─→ handles toolbar buttons
    ├─→ handles drag & drop
    ↓
    ├─→ _setup_ui
    ├─→ _create_menu_bar
    ├─→ _create_formatting_toolbar
    ├─→ _setup_shortcuts
    └─→ _setup_timers
    ↓
    ├─→ owns tab list
    ├─→ wires signals
    └─→ drives UI state
    ↓
    ↓
    ├───────────────┬────────────────┬────────────────┬────────────────┐
    ↓               ↓                ↓                ↓
[models/]     [services/]       [widgets/]        [config/]
    ↓               ↓                ↓                ↓
    │               │                │                │
    │               │                │                └─→ constants (AppConfig, StyleSheet)
    │               │                │
    │               │                └─→ SearchBar, StatusBarWidget,
    │               │                     TablePropertiesDialog,
    │               │                     
    │               │
    │               └─→ FileOperations (read/write/delete),
    │                    SettingsManager (geometry, recent files, session restore)
    │
    └─→ Document state, DocumentTab,
         LinkAwareTextEdit,
         is_modified, mark_saved,
         get_content_html

(models/services/widgets/config all interact with ↓)

[Qt Document (in‑memory)]
    ↓
    ├─→ QTextDocument
    ├─→ undo/redo stack
    ├─→ rich‑text cursor
    └─→ embedded images

[Filesystem]
    ↑   ↓
    ├─→ .html
    ├─→ .txt
    ├─→ .bak backups
    └─→ UTF‑8 / latin‑1 encoding

[QSettings]
    ↑   ↓
    ├─→ window geometry
    ├─→ open tabs
    └─→ recent files

```
---

## Keyboard Shortcuts

A full list of keyboard shortcuts is available in [SHORTCUTS.md](SHORTCUTS.md).

---

## File Support

- **HTML (.html)** — Full formatting and structure preserved  
- **TXT (.txt)** — Plain text fallback  
- Automatic mode detection on load  

---

## What This Project Demonstrates

- Designing a **stateful desktop application**
- Managing **multiple documents concurrently**
- Handling **structured content (tables, media)**
- Building **persistent systems (session recovery)**
- Creating **responsive and intuitive UI workflows**

---

## Future Improvements

- **Plugin system for extensibility**
- **Performance optimization for large documents**
- **Refactor more toward MVC/MVVM architecture**
- **More Export options (besides PDF, which has been implemented)**
- **Dark/Light theme toggle**
- **Cloud sync and backup**
- **Spell checking**
- **Auto-save recovery**

---

## Testing

The application includes a comprehensive test suite using pytest and pytest-qt:

```
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/test_document_tab.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

---

## Installation

### Requirements
- Python 3.10+
- PyQt6
- pytest (optional, for running tests)

### Setup
```
git clone https://github.com/DerYokoya/NoteApp.git
cd NoteApp
pip install -r requirements.txt
python main.py

# Run tests (optional)
pip install pytest pytest-qt
pytest tests/ -v
```
