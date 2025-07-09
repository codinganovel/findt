#!/usr/bin/env python3
"""
findt - Beautiful Fuzzy Finder
A terminal fuzzy finder with exact and fuzzy search modes.

Note: This tool operates entirely in-memory and creates no index files or 
temporary files on disk. File discovery is performed fresh each run.
"""

import os
import sys
import argparse
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Optional dependency detection
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Termios detection for input handling
try:
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False

# Constants
TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', 
    '.toml', '.ini', '.cfg', '.conf', '.sh', '.bash', '.zsh',
    '.html', '.css', '.xml', '.csv', '.log', '.rst', '.tex'
}

IGNORE_PATTERNS = {
    '.git', '.svn', '__pycache__', '.pytest_cache', 
    'node_modules', '.venv', 'venv', '.DS_Store',
    '.mypy_cache', '.tox', 'dist', 'build'
}

class Colors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BG_BLUE = '\033[44m'

def colored(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{Colors.RESET}"

class ClipboardManager:
    """Handle clipboard operations with fallback hierarchy."""
    
    def __init__(self):
        self.method = self._detect_clipboard_method()
    
    def _detect_clipboard_method(self) -> str:
        """Detect best available clipboard method."""
        if HAS_PYPERCLIP:
            return "pyperclip"
        elif shutil.which('pbcopy'):  # macOS
            return "pbcopy"
        elif shutil.which('xclip'):   # Linux
            return "xclip"
        elif shutil.which('xsel'):    # Linux alternative
            return "xsel"
        else:
            return "print"
    
    def copy(self, text: str) -> bool:
        """Copy text to clipboard, return success status."""
        try:
            if self.method == "pyperclip":
                pyperclip.copy(text)
                return True
            elif self.method == "pbcopy":
                subprocess.run(['pbcopy'], input=text, text=True, check=True)
                return True
            elif self.method == "xclip":
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=text, text=True, check=True)
                return True
            elif self.method == "xsel":
                subprocess.run(['xsel', '--clipboard', '--input'], 
                             input=text, text=True, check=True)
                return True
            else:
                print(f"\n📋 Clipboard content:\n{text}")
                return False
        except Exception as e:
            print(f"❌ Clipboard error: {e}")
            return False
    
    def get_status_text(self) -> str:
        """Get clipboard status for UI display."""
        if self.method in ["pyperclip", "pbcopy", "xclip", "xsel"]:
            return "📋 Clipboard ready"
        else:
            return "⚠️ Clipboard disabled"

def get_file_icon(file_path: Path) -> str:
    """Get emoji icon for file type."""
    suffix = file_path.suffix.lower()
    if file_path.is_dir():
        return "📁"
    elif suffix in ['.py']:
        return "🐍"
    elif suffix in ['.js', '.ts']:
        return "💛"
    elif suffix in ['.json', '.yaml', '.yml', '.toml']:
        return "⚙️"
    elif suffix in ['.md', '.rst']:
        return "📝"
    elif suffix in ['.txt', '.log']:
        return "📄"
    elif suffix in ['.html', '.css']:
        return "🌐"
    elif suffix in ['.sh', '.bash', '.zsh']:
        return "🔧"
    else:
        return "📄"

def format_size(size: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

def format_time_ago(timestamp: float) -> str:
    """Format time ago in human readable format."""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return "now"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes}m ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours}h ago"
    else:
        days = int(diff / 86400)
        return f"{days}d ago"

def should_include_file(filename: str, include_hidden: bool = False) -> bool:
    """Check if file should be included in search."""
    if not include_hidden and filename.startswith('.'):
        return False
    return True

def should_include_dir(dirname: str, include_hidden: bool = False) -> bool:
    """Check if directory should be traversed."""
    if dirname in IGNORE_PATTERNS:
        return False
    if not include_hidden and dirname.startswith('.'):
        return False
    return True

def discover_files_with_progress(directory: Path, include_hidden: bool = False) -> List[Path]:
    """Discover searchable files with progress display."""
    files = []
    
    def show_indexing_screen(file_count: int, current_dir: str = ""):
        """Display beautiful indexing progress screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Progress bar (simple animation)
        progress_chars = "⣾⣽⣻⢿⡿⣟⣯⣷"
        spinner = progress_chars[file_count % len(progress_chars)]
        
        # Create a simple progress bar based on file count
        bar_length = 20
        filled = min(bar_length, (file_count // 50) % (bar_length + 1))
        bar = "█" * filled + "░" * (bar_length - filled)
        
        screen = f"""╔═ findt - Beautiful Fuzzy Finder ═══════════════════════╗
║                                                         ║
║              {spinner} Discovering files...                    ║
║                                                         ║
║               {bar}                        ║
║                                                         ║
║            Found {file_count:,} files so far...                 ║"""
        
        if current_dir:
            # Truncate long directory names
            display_dir = current_dir[-45:] if len(current_dir) > 45 else current_dir
            screen += f"""║                                                         ║
║            Scanning: {display_dir:<45} ║"""
        else:
            screen += f"""║                                                         ║
║                                                         ║"""
            
        screen += """║                                                         ║
╚═════════════════════════════════════════════════════════╝"""
        
        print(colored(screen, Colors.BLUE))
    
    try:
        file_count = 0
        for root, dirs, filenames in os.walk(directory):
            # Show progress every 50 files or on directory change
            if file_count % 50 == 0:
                show_indexing_screen(file_count, str(Path(root).name))
            
            # Filter directories in-place
            dirs[:] = [d for d in dirs if should_include_dir(d, include_hidden)]
            
            # Add files
            for filename in filenames:
                if should_include_file(filename, include_hidden):
                    files.append(Path(root) / filename)
                    file_count += 1
                    
                    # Update progress frequently for slow directories
                    if file_count % 50 == 0:
                        show_indexing_screen(file_count, str(Path(root).name))
    
    except PermissionError:
        pass  # Skip directories we can't read
    
    # Final progress update
    show_indexing_screen(len(files), "Complete!")
    time.sleep(0.3)  # Brief pause to show completion
    
    return files


def discover_files(directory: Path, include_hidden: bool = False) -> List[Path]:
    """Legacy function for compatibility - now uses progress version."""
    return discover_files_with_progress(directory, include_hidden)

def exact_search(query: str, files: List[Path]) -> List[Tuple[Path, str]]:
    """Fast exact substring matching."""
    if not query:
        return [(f, "all") for f in files]
    
    results = []
    query_lower = query.lower()
    
    for file_path in files:
        # Search in filename
        if query_lower in file_path.name.lower():
            results.append((file_path, "filename"))
            continue
            
        # Search in file content (text files only)
        if file_path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1024)  # First 1KB only for speed
                    if query_lower in content.lower():
                        results.append((file_path, "content"))
            except (IOError, UnicodeDecodeError, PermissionError):
                pass
    
    return results

def fuzzy_search(query: str, files: List[Path]) -> List[Tuple[Path, str]]:
    """Enhanced fuzzy matching with rapidfuzz, content search, and proper scoring."""
    if not HAS_RAPIDFUZZ:
        return exact_search(query, files)
    
    if not query:
        return [(f, "all") for f in files]
    
    results = []
    query_lower = query.lower()
    
    for file_path in files:
        best_score = 0
        best_match_type = "filename"
        
        # Fuzzy match filename (highest priority)
        filename_score = fuzz.partial_ratio(query_lower, file_path.name.lower())
        if filename_score > best_score:
            best_score = filename_score
            best_match_type = "filename"
        
        # Fuzzy match full path (medium priority)
        path_score = fuzz.partial_ratio(query_lower, str(file_path).lower())
        if path_score > best_score:
            best_score = path_score
            best_match_type = "path"
        
        # Fuzzy match file content (lower priority, but still valuable)
        if file_path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2048).lower()  # Read more content for better fuzzy matching
                    content_score = fuzz.partial_ratio(query_lower, content)
                    # Weight content matches slightly lower than filename matches
                    weighted_content_score = content_score * 0.8
                    if weighted_content_score > best_score:
                        best_score = weighted_content_score
                        best_match_type = "content"
            except (IOError, UnicodeDecodeError, PermissionError):
                pass
        
        # Include results with score above threshold
        if best_score > 50:  # Lowered threshold for more inclusive fuzzy matching
            results.append((file_path, best_match_type, best_score))
    
    # Sort by score (highest first), then by match type priority, then by filename
    def sort_key(item):
        path, match_type, score = item
        # Priority: filename > path > content
        type_priority = {"filename": 3, "path": 2, "content": 1}
        return (-score, -type_priority.get(match_type, 0), path.name.lower())
    
    results.sort(key=sort_key)
    
    # Return in the expected format (without scores)
    return [(path, match_type) for path, match_type, score in results]

def get_file_preview(file_path: Path, lines: int = 4) -> str:
    """Get first few lines of file for preview."""
    if not file_path.suffix.lower() in TEXT_EXTENSIONS:
        return f"Binary file ({file_path.suffix})"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            preview_lines = []
            for _ in range(lines):
                line = f.readline()
                if not line:
                    break
                preview_lines.append(line.rstrip())
            return '\n'.join(preview_lines) if preview_lines else "Empty file"
    except (IOError, UnicodeDecodeError, PermissionError):
        return "Unable to preview file"

def get_file_content(file_path: Path) -> str:
    """Get full file content for clipboard copying."""
    if not file_path.suffix.lower() in TEXT_EXTENSIONS:
        return f"Cannot copy binary file: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except (IOError, UnicodeDecodeError, PermissionError) as e:
        return f"Error reading file: {e}"

class SearchMode:
    """Manage search mode state."""
    
    def __init__(self):
        self.fancy_mode = False
        self.show_preview = True
        self.show_hidden = False
    
    def toggle_fancy(self) -> bool:
        """Toggle fancy mode if available."""
        if HAS_RAPIDFUZZ:
            self.fancy_mode = not self.fancy_mode
            return True
        return False
    
    def get_mode_text(self) -> str:
        """Get mode indicator text."""
        return "🎯 Fancy" if self.fancy_mode else "🔍 Normal"

class FuzzyFinder:
    """Main fuzzy finder application."""
    
    def __init__(self, directory: Path = None, initial_query: str = ""):
        self.directory = directory or Path.cwd()
        self.query = initial_query
        self.selected_index = 0
        self.selected_file = None  # File that shows preview
        self.scroll_offset = 0
        self.mode = SearchMode()
        self.clipboard = ClipboardManager()
        
        # Discover files
        self.all_files = discover_files(self.directory, self.mode.show_hidden)
        self.filtered_files = self.search()
        
        # Fix initial selection if no files found
        if not self.filtered_files:
            self.selected_index = -1
    
    def search(self) -> List[Tuple[Path, str]]:
        """Perform search based on current mode and query."""
        if self.mode.fancy_mode:
            return fuzzy_search(self.query, self.all_files)
        else:
            return exact_search(self.query, self.all_files)
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_display_range(self, terminal_height: int = 20) -> Tuple[int, int]:
        """Get the range of files to display based on scroll offset."""
        # Reserve space for header (3 lines) and footer (1 line) and preview
        available_height = terminal_height - 6
        if self.mode.show_preview and self.selected_file:
            available_height -= 6  # Space for preview box
        
        start = self.scroll_offset
        end = min(start + available_height, len(self.filtered_files))
        return start, end
    
    def draw_ui(self):
        """Draw the main user interface."""
        self.clear_screen()
        
        # Header
        print(colored("╔═ findt - Beautiful Fuzzy Finder ═══════════════════════╗", Colors.BLUE))
        search_display = f"🔍 Search: {self.query}"
        padding = 55 - len(search_display)
        print(colored(f"║ {search_display}{' ' * padding} ║", Colors.BLUE))
        print(colored("╠═════════════════════════════════════════════════════════╣", Colors.BLUE))
        
        # File list
        terminal_height = 20  # Could be detected with shutil.get_terminal_size()
        start, end = self.get_display_range(terminal_height)
        
        for i in range(start, end):
            file_path, match_type = self.filtered_files[i]
            icon = get_file_icon(file_path)
            
            # Format entry
            is_current = (i == self.selected_index)
            is_selected = (self.selected_file == file_path)
            
            # File info
            try:
                stat = file_path.stat()
                size = format_size(stat.st_size)
                modified = format_time_ago(stat.st_mtime)
                rel_path = file_path.parent.name if file_path.parent.name != '.' else '.'
            except (OSError, PermissionError):
                size, modified, rel_path = "?", "?", "?"
            
            # Build display line
            cursor = "→" if is_current else " "
            selected_mark = "●" if is_selected else " "
            
            name_line = f"║ {cursor}[{i+1}] {icon} {file_path.name:<35} {selected_mark} ║"
            info_line = f"║    {rel_path} • {size} • {modified}{' ' * (55 - len(f'{rel_path} • {size} • {modified}'))} ║"
            
            if is_current:
                print(colored(name_line, Colors.CYAN))
                print(colored(info_line, Colors.GRAY))
            else:
                print(name_line)
                print(colored(info_line, Colors.GRAY))
            
            # Show preview for selected file right after its entry
            if is_selected and self.mode.show_preview:
                preview = get_file_preview(file_path)
                print(colored("║     ┌─ Preview ──────────────────────────────────────┐     ║", Colors.GRAY))
                for line in preview.split('\n'):
                    preview_line = f"     │ {line:<50} │"
                    print(colored(f"║{preview_line[:57]}{' ' * max(0, 57 - len(preview_line))} ║", Colors.GRAY))
                print(colored("║     └─────────────────────────────────────────────────┘     ║", Colors.GRAY))
            
            print(colored("║" + " " * 57 + "║", Colors.BLUE))
        
        # Fill remaining space if needed
        displayed_lines = (end - start) * 3  # Each file takes 3 lines
        if self.selected_file and self.mode.show_preview:
            displayed_lines += 6  # Preview takes 6 lines
        
        remaining_lines = max(0, 10 - displayed_lines)
        for _ in range(remaining_lines):
            print(colored("║" + " " * 57 + "║", Colors.BLUE))
        
        # Footer
        mode_text = self.mode.get_mode_text()
        clipboard_text = self.clipboard.get_status_text()
        file_count = len(self.filtered_files)
        status = f"{mode_text} • {clipboard_text} • {file_count} files • ?:help"
        status_padding = 55 - len(status)
        print(colored("╠═════════════════════════════════════════════════════════╣", Colors.BLUE))
        print(colored(f"║ {status}{' ' * status_padding} ║", Colors.BLUE))
        print(colored("╚═════════════════════════════════════════════════════════╝", Colors.BLUE))
    
    def show_help(self):
        """Display help overlay."""
        self.clear_screen()
        help_text = """
╔══════════════════════════════════════════════════════╗
║                    findt - Help                      ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Navigation:                                         ║
║    Ctrl+j/Ctrl+k or ↑/↓     Move up/down                  ║
║    Ctrl+g/Ctrl+E           Jump to top/bottom             ║
║    Page Up/Down  Scroll by page                      ║
║                                                      ║
║  Search:                                             ║
║    Type          Real-time search                    ║
║    Backspace     Remove characters                   ║
║    Ctrl+U        Clear search                        ║
║    Ctrl+f             Toggle fancy mode (if available)    ║
║                                                      ║
║  Actions:                                            ║
║    Enter         Select file & show preview          ║
║    Ctrl+c             Copy file path to clipboard         ║
║    Ctrl+y             Copy file content to clipboard      ║
║    Ctrl+p             Toggle preview pane                 ║
║                                                      ║
║  System:                                             ║
║    Ctrl+h             Show this help                      ║
║    Ctrl+q             Quit                                ║
║    Esc           Clear search or quit                ║
║                                                      ║
╚══════════════════════════════════════════════════════╝

Press any key to continue...
"""
        print(colored(help_text, Colors.BLUE))
        if HAS_TERMIOS:
            try:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except:
                input()
        else:
            input()
    
    def get_input(self) -> str:
        """Get single character input, handling escape sequences."""
        if not HAS_TERMIOS:
            return input()
        
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
            
            # Handle escape sequences (arrow keys, etc.)
            if char == '\x1b':
                # Read the rest of the escape sequence
                char += sys.stdin.read(2)
            
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            return char
        except:
            return input()
    
    def handle_navigation(self, key: str) -> bool:
        """Handle navigation keys. Return True if handled."""
        # Don't navigate if no files available
        if not self.filtered_files:
            return True if key in ['\x0a', '\x0b', '\x07', '\x05', '\x1b[A]', '\x1b[B]', '\x1b[5~', '\x1b[6~'] else False
    
        if key in ['\x0a', '\x1b[B']:  # Down (Ctrl+J or down arrow)
            if self.selected_index < len(self.filtered_files) - 1:
                self.selected_index += 1
            return True
        elif key in ['\x0b', '\x1b[A']:  # Up (Ctrl+K or up arrow)
            if self.selected_index > 0:
                self.selected_index -= 1
            return True
        elif key == '\x07':  # Top (Ctrl+G)
            self.selected_index = 0
            return True
        elif key == '\x05':  # Bottom (Ctrl+E for "End")
            self.selected_index = len(self.filtered_files) - 1
            return True
        elif key == '\x1b[5~':  # Page Up
            self.selected_index = max(0, self.selected_index - 10)
            return True
        elif key == '\x1b[6~':  # Page Down
            self.selected_index = min(len(self.filtered_files) - 1, self.selected_index + 10)
            return True
        return False
    
    
    def handle_action(self, key: str) -> bool:
        """Handle action keys. Return True if should continue running."""
        if key == '\r' or key == '\n':  # Enter - select file
            if self.filtered_files and 0 <= self.selected_index < len(self.filtered_files):
                self.selected_file = self.filtered_files[self.selected_index][0]
        elif key == '\x03':  # Copy path (Ctrl+C)
            if self.filtered_files and 0 <= self.selected_index < len(self.filtered_files):
                file_path = self.filtered_files[self.selected_index][0]
                success = self.clipboard.copy(str(file_path))
                if success:
                    print(f"\n📋 Copied path: {file_path}")
                time.sleep(1)
        elif key == '\x19':  # Copy content (Ctrl+Y)
            if self.filtered_files and 0 <= self.selected_index < len(self.filtered_files):
                file_path = self.filtered_files[self.selected_index][0]
                content = get_file_content(file_path)
                success = self.clipboard.copy(content)
                if success:
                    print(f"\n📋 Copied content from: {file_path}")
                else:
                    print(f"\n⚠️ Could not copy content from: {file_path}")
                time.sleep(1)
        elif key == '\x06':  # Toggle fancy mode (Ctrl+F)
            if self.mode.toggle_fancy():
                self.filtered_files = self.search()
                # Fix index after search
                if self.filtered_files:
                    self.selected_index = min(self.selected_index, len(self.filtered_files) - 1)
                else:
                    self.selected_index = -1
        elif key == '\x10':  # Toggle preview (Ctrl+P)
            self.mode.show_preview = not self.mode.show_preview
        elif key == '\x08':  # Help (Ctrl+H)
            self.show_help()
        elif key == '\x11':  # Quit (Ctrl+Q)
            return False
        elif key == '\x1b':  # Escape
            if self.query:
                self.query = ""
                self.filtered_files = self.search()
                self.selected_index = 0 if self.filtered_files else -1
            else:
                return False
        elif key == '\x15':  # Ctrl+U - clear search
            self.query = ""
            self.filtered_files = self.search()
            self.selected_index = 0 if self.filtered_files else -1
        elif key == '\x7f' or key == '\b':  # Backspace
            if self.query:
                self.query = self.query[:-1]
                self.filtered_files = self.search()
                # Fix index after search
                if self.filtered_files:
                    self.selected_index = min(self.selected_index, len(self.filtered_files) - 1)
                else:
                    self.selected_index = -1
        elif key.isprintable() and len(key) == 1:  # Regular character
            self.query += key
            self.filtered_files = self.search()
            self.selected_index = 0 if self.filtered_files else -1
    
        return True

    def run(self):
        """Main application loop."""
        while True:
            # Update scroll offset to keep selected item visible
            # Only do this if we have files and a valid selection
            if self.filtered_files and 0 <= self.selected_index < len(self.filtered_files):
                terminal_height = 20
                start, end = self.get_display_range(terminal_height)
                
                if self.selected_index < start:
                    self.scroll_offset = self.selected_index
                elif self.selected_index >= end:
                    available_height = terminal_height - 6
                    if self.mode.show_preview and self.selected_file:
                        available_height -= 6
                    self.scroll_offset = self.selected_index - available_height + 1
            else:
                # Reset scroll when no valid selection
                self.scroll_offset = 0
            
            self.draw_ui()
            
            if not self.filtered_files:
                print(colored("\n🔍 No files found. Try a different search term.", Colors.YELLOW))
            
            try:
                key = self.get_input()
                
                # Handle navigation
                if self.handle_navigation(key):
                    continue
                
                # Handle actions
                if not self.handle_action(key):
                    break
                    
            except KeyboardInterrupt:
                break
        
        print(colored("\n👋 Goodbye!", Colors.BLUE))

def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="findt - Beautiful Fuzzy Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  findt                    # Launch TUI in current directory
  findt search_term        # Launch TUI with pre-filled search
  findt --fancy term       # Launch TUI in fancy mode
  findt --help            # Show this help
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        default='',
        help='Initial search query'
    )
    
    parser.add_argument(
        '--fancy',
        action='store_true',
        help='Start in fancy fuzzy mode (requires rapidfuzz)'
    )
    
    parser.add_argument(
        '--path',
        type=Path,
        default=Path.cwd(),
        help='Directory to search in (default: current directory)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='findt 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not args.path.exists() or not args.path.is_dir():
        print(colored(f"❌ Error: Directory '{args.path}' does not exist", Colors.RED))
        sys.exit(1)
    
    # Create and run finder
    finder = FuzzyFinder(args.path, args.query)
    
    if args.fancy:
        if HAS_RAPIDFUZZ:
            finder.mode.fancy_mode = True
        else:
            print(colored("⚠️ Warning: rapidfuzz not available, using normal mode", Colors.YELLOW))
    
    try:
        finder.run()
    except KeyboardInterrupt:
        print(colored("\n👋 Goodbye!", Colors.BLUE))
    except Exception as e:
        print(colored(f"❌ Error: {e}", Colors.RED))
        sys.exit(1)

if __name__ == "__main__":
    main()