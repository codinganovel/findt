# findt
**findt** is a beautiful terminal fuzzy finder with instant exact search and optional fuzzy matching. It provides a clean, blue-themed interface for discovering files with real-time previews and seamless clipboard integration.
> Find files fast. Look good doing it.
---
## ✨ Features
- Lightning-fast exact search with zero dependencies  
- Optional fuzzy matching mode (requires rapidfuzz)  
- Beautiful blue-themed TUI with file previews  
- Smart clipboard integration with graceful fallbacks  
- Vim-style navigation and keyboard shortcuts  
- Progressive file discovery with animated indexing screen  
- Inline file previews that follow your selection  
---
## 📦 Installation

[get yanked](https://github.com/codinganomel/yanked)

---
### Available Commands
| Command         | Description                          |
|----------------|--------------------------------------|
| `findt`        | Launch TUI in current directory      |
| `findt term`   | Launch TUI with pre-filled search    |
| `findt --fancy term` | Launch TUI in fuzzy mode       |
| `findt --path /dir`  | Search in specific directory   |

All interaction happens through the beautiful TUI interface with keyboard shortcuts.
---
## 🚀 Usage

### Basic Usage
```bash
$ findt
# Opens TUI file finder in current directory

$ findt config
# Opens TUI with "config" already searched

$ findt --fancy setup
# Opens TUI in fuzzy mode searching for "setup"
```

### Enhanced Mode
```bash
$ pip install rapidfuzz  # Optional: enables fuzzy matching
$ findt
# Now you can toggle between exact and fuzzy modes with 'f'
```
---
## ⌨️ Keyboard Shortcuts

### Navigation
| Key           | Action                        |
|---------------|-------------------------------|
| `j/k` or `↑/↓` | Navigate up/down through files |
| `g/G`         | Jump to top/bottom            |
| `Page Up/Down` | Scroll by page               |

### Search & Modes
| Key           | Action                        |
|---------------|-------------------------------|
| Type anything | Real-time search as you type  |
| `Backspace`   | Remove characters from search |
| `Ctrl+U`      | Clear entire search          |
| `f`           | Toggle fancy mode (if available) |

### File Actions
| Key           | Action                        |
|---------------|-------------------------------|
| `Enter`       | Select file & show preview    |
| `c`           | Copy file path to clipboard   |
| `y`           | Copy file content to clipboard |
| `p`           | Toggle preview pane on/off    |

### System
| Key           | Action                        |
|---------------|-------------------------------|
| `?`           | Show help screen              |
| `q`           | Quit application              |
| `Esc`         | Clear search or exit          |

---
## 📋 Clipboard Support & Dependencies
`findt` uses smart clipboard detection with multiple fallback methods for maximum compatibility.

### macOS  
✅ Works out of the box using built-in `pbcopy`

### Windows  
✅ Works out of the box using Windows clipboard API

### Linux  
⚠️ Install a clipboard utility for best experience:
```bash
sudo apt install xclip   # or
sudo apt install xsel
```

**Fallback:** If no clipboard support is available, file paths and content are printed to terminal instead.

---
## 🎯 Search Modes

### Normal Mode (Default)
- **Zero dependencies** - works everywhere
- **Lightning fast** - instant substring matching
- **Reliable** - handles massive directories smoothly
- **Predictable** - shows exactly what contains your search term

### Fancy Mode (Optional)
- **Install:** `pip install rapidfuzz`
- **Fuzzy matching** - handles typos and partial matches
- **Smart scoring** - most relevant results first
- **Toggle anytime** - press `f` to switch modes

The beauty is you get a perfectly functional tool without any dependencies, but can enhance it when desired!

---
## 🔍 File Discovery

findt recursively discovers files in your directory with smart filtering:

- **Includes:** Text files, code files, documents, configs
- **Excludes:** Hidden directories (`.git`, `node_modules`, `__pycache__`)
- **Progress:** Beautiful animated indexing screen for large directories
- **Memory-only:** No index files created - everything stays in RAM

---
## 💡 Pro Tips

- **Large directories:** Normal mode handles even crazy large directories smoothly
- **Preview navigation:** Preview follows your file selection, not cursor movement  
- **Quick copying:** `c` for paths (great for terminal commands), `y` for content (great for pasting code)
- **Search as you type:** No need to press enter - results update in real-time
- **Vim users:** Familiar `j/k` navigation feels natural

---
## 🐌 Performance note (for the ambitious)

If you're crazy enough to run findt in your root directory, normal mode will handle it gracefully while fancy mode might slow down. The initial file discovery shows a progress screen so you're never left wondering if it's working.

Most people run this on project directories or ~/Documents anyway, where it's instant.

---
## 📄 License

under ☕️, check out [the-coffee-license](https://github.com/codinganovel/The-Coffee-License)

I've included both licenses with the repo, do what you know is right. The licensing works by assuming you're operating under good faith.
---
## ✍️ Created with 💙 by Sam  
Because fzf is functional, but life's too short for ugly interfaces.