---
title: "vi / Vim Editor Quick Reference & Cheat Sheet"
description: "Comprehensive quick reference for modal text editing, navigation, file I/O, search, and configuration in vi/vim."
keywords: [vi, vim, cheat sheet, editor, modal editing, navigation, commands, regex search, linux, macos, terminal, cursor motion, yank paste, ex mode]
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases: [vi cheatsheet, vim cheat sheet, vi editor commands, how to exit vi, vim shortcuts, vi reference, vi commands, terminal editor]
related:
  - _INDEX.md
  - Templates/AI-SEARCHABLE-DOC-TEMPLATE.md
---

# 📌 vi / Vim Editor Quick Reference & Cheat Sheet

> **TL;DR:** Comprehensive cheat sheet and quick reference for vi and Vim modal text editing in terminal and remote server environments. Covers mode switching, cursor navigation, text manipulation, search/replace, yanking/pasting, and environment options.
> **Use this for:** Rapid command lookup when editing files directly in terminal sessions, SSH connections, Linux containers, or macOS shells without a GUI editor.

---

## 📋 Quick Reference

| Action | Command | Mode | Notes |
|--------|---------|------|-------|
| **Save & Quit** | `:wq` or `ZZ` | Ex / Command | Writes changes to disk and exits |
| **Quit without Saving** | `:q!` or `ZQ` | Ex / Command | Discards all unsaved modifications |
| **Enter Insert Mode** | `i` or `a` | Command → Insert | Insert before cursor (`i`) or append after (`a`) |
| **Return to Command Mode** | `<Esc>` | Any → Command | Exits insert/visual mode back to normal |
| **Undo Last Change** | `u` | Command | Undo last edit (`Ctrl + r` to redo in Vim) |
| **Search Forward** | `/pattern` | Ex / Command | Search forward (`n` next, `N` previous) |
| **Delete Line** | `dd` | Command | Deletes current line into unnamed register |
| **Copy (Yank) Line** | `yy` or `Y` | Command | Copies current line into register |
| **Paste Below** | `p` | Command | Pastes register contents below cursor (`P` above) |

---

## 🔍 Quick Navigation

| Section | Description |
|---------|-------------|
| [1. Core Modes & Workflow](#1-core-modes--workflow) | Command mode vs Insert mode vs Ex mode |
| [2. Starting, Saving, and Exiting](#2-starting-saving-and-exiting) | Launching vi, write (`:w`), quit (`:q`, `:q!`, `:wq`) |
| [3. Cursor Navigation](#3-cursor-navigation) | Basic motion, word jumps, line boundaries, file navigation |
| [4. Entering Insert Mode](#4-entering-insert-mode) | Insert, append, open line above/below |
| [5. Text Editing, Deleting, and Changing](#5-text-editing-deleting-and-changing) | Character, word, and line deletion; change commands |
| [6. Copying (Yanking) and Pasting](#6-copying-yanking-and-pasting) | Line yanking, registers, pasting above/below |
| [7. Search, Replace, and Undo](#7-search-replace-and-undo) | Forward/backward search, global substitution, undo/redo |
| [8. Environment & Configuration Settings](#8-environment--configuration-settings) | Line numbering, search sensitivity, `.vimrc` options |

---

## 1. Core Modes & Workflow

The `vi` editor operates primarily across distinct operational modes:
- **Command (Normal) Mode:** Default mode upon opening a file. Keystrokes execute navigation and editing commands rather than inserting text.
- **Insert Mode:** Keystrokes enter text directly into the buffer.
- **Ex (Last-Line) Mode:** Initiated by typing `:` from Command Mode. Used for file I/O, search/replace, and global configurations.
- **Visual Mode (Vim):** Initiated with `v`, `V`, or `Ctrl + v` for highlighting text blocks.

```
       ┌───────────────────────────────┐
       │     Command (Normal) Mode     │ ◄─── (Start State)
       └───┬───────────────────────▲───┘
           │                       │
      i, a, o, s                 <Esc>
           │                       │
           ▼                       │
       ┌───────────────────────────┴───┐
       │          Insert Mode          │
       └───────────────────────────────┘
```

> **Rule of Thumb:** If unsure which mode you are in, press `<Esc>` twice to return to Command Mode.

---

## 2. Starting, Saving, and Exiting

### Launching vi
| Command | Action |
|---------|--------|
| `vi filename` | Open existing file or create new buffer with name |
| `vi +12 filename` | Open file directly at line 12 |
| `vi +/pattern filename` | Open file at first occurrence of `pattern` |
| `view filename` | Open file in read-only mode |

### Exiting and Saving (Ex Mode)
| Command | Action | Description |
|---------|--------|-------------|
| `:w` | Write | Save current changes without exiting |
| `:w filename` | Write As | Save changes to specified new file |
| `:w!` | Force Write | Overwrite read-only file (if file permissions permit) |
| `:wq` | Write & Quit | Save changes and exit editor |
| `ZZ` | Quick Save & Quit | Equivalent to `:wq` (run directly from Command Mode) |
| `:q` | Quit | Exit editor (fails if unsaved modifications exist) |
| `:q!` | Force Quit | Discard all unsaved changes and immediately exit |
| `ZQ` | Quick Discard & Quit | Equivalent to `:q!` (run directly from Command Mode) |

---

## 3. Cursor Navigation (Command Mode)

### Basic Directional Movement
| Key | Direction | Notes |
|-----|-----------|-------|
| `h` | ⬅️ Left | Move cursor one character to the left |
| `j` | ⬇️ Down | Move cursor one line down |
| `k` | ⬆️ Up | Move cursor one line up |
| `l` | ➡️ Right | Move cursor one character to the right |

### Word and Sentence Motion
| Key | Motion | Description |
|-----|--------|-------------|
| `w` | Word forward | Move to start of next alphanumeric word |
| `W` | WORD forward | Move to start of next space-delimited word |
| `b` | Word backward | Move to start of previous word |
| `B` | WORD backward | Move to start of previous space-delimited word |
| `e` / `E` | Word end | Move to end of current/next word |

### Line Boundaries
| Key | Target | Description |
|-----|--------|-------------|
| `0` | Column 0 | Jump to absolute beginning of current line |
| `^` | First non-blank | Jump to first non-whitespace character on line |
| `$` | End of line | Jump to last character of current line |

### File-Level Movement
| Command | Target | Description |
|---------|--------|-------------|
| `gg` or `1G` | File start | Jump to line 1 of file |
| `G` | File end | Jump to last line of file |
| `:<number>` or `<number>G` | Line number | Jump to specific line (e.g. `:42` or `42G`) |
| `Ctrl + f` | Page Down | Scroll forward one full screen |
| `Ctrl + b` | Page Up | Scroll backward one full screen |
| `Ctrl + d` | Half Page Down | Scroll down half a screen |
| `Ctrl + u` | Half Page Up | Scroll up half a screen |

---

## 4. Entering Insert Mode

| Key | Position | Description |
|-----|----------|-------------|
| `i` | Before cursor | Insert text immediately before current cursor position |
| `I` | Line start | Insert text at first non-whitespace character of line |
| `a` | After cursor | Append text immediately after current cursor position |
| `A` | Line end | Append text at the very end of the line |
| `o` | Open below | Open a new blank line below current line and enter insert mode |
| `O` | Open above | Open a new blank line above current line and enter insert mode |
| `s` | Substitute char | Delete character under cursor and enter insert mode |
| `S` | Substitute line | Delete entire current line and enter insert mode |

---

## 5. Text Editing, Deleting, and Changing

All delete commands store deleted text in the default register (acting like "Cut").

### Deletion Commands
| Command | Scope | Description |
|---------|-------|-------------|
| `x` | Character | Delete character directly under cursor |
| `X` | Previous char | Delete character immediately before cursor (Backspace) |
| `dw` | Word | Delete from cursor to start of next word |
| `d$` or `D` | To line end | Delete from cursor to the end of the line |
| `d0` | To line start | Delete from cursor to beginning of the line |
| `dd` | Entire line | Delete current line |
| `<n>dd` | Multiple lines | Delete `<n>` lines starting from cursor (e.g. `5dd`) |

### Change Commands (Delete + Insert Mode)
| Command | Scope | Description |
|---------|-------|-------------|
| `r<char>` | Single char | Replace character under cursor with `<char>` (stays in command mode) |
| `R` | Overwrite | Enter Replace mode (overwrites text character by character) |
| `cw` | Word | Change word: deletes to end of word and enters Insert mode |
| `cc` | Line | Change line: clears entire line and enters Insert mode |
| `C` or `c$` | To line end | Change to line end: deletes to end of line and enters Insert mode |

---

## 6. Copying (Yanking) and Pasting

In `vi`, copying is called **yanking**.

| Command | Action | Description |
|---------|--------|-------------|
| `yy` or `Y` | Yank line | Copy current line to register |
| `<n>yy` | Yank multiple | Copy `<n>` lines to register (e.g. `3yy`) |
| `yw` | Yank word | Copy from cursor to start of next word |
| `y$` | Yank to end | Copy from cursor to end of line |
| `p` | Paste after | Paste register content after cursor or below current line |
| `P` | Paste before | Paste register content before cursor or above current line |
| `"a<command>` | Named register | Use named register `a` (e.g. `"ayy` to copy, `"ap` to paste) |

---

## 7. Search, Replace, and Undo

### Search Patterns
| Command | Direction | Description |
|---------|-----------|-------------|
| `/pattern` | Forward | Search forward for regex `pattern` |
| `?pattern` | Backward | Search backward for regex `pattern` |
| `n` | Repeat | Jump to next occurrence in same search direction |
| `N` | Reverse repeat | Jump to next occurrence in opposite search direction |
| `*` | Word forward | Search forward for word currently under cursor |
| `#` | Word backward | Search backward for word currently under cursor |

### Global Search and Replace (Ex Mode)
| Syntax | Scope | Description |
|--------|-------|-------------|
| `:s/old/new/` | Current line | Replace first occurrence of `old` with `new` on current line |
| `:s/old/new/g` | Current line | Replace all occurrences of `old` with `new` on current line |
| `:%s/old/new/g` | Whole file | Replace all occurrences across entire file |
| `:%s/old/new/gc` | Whole file (prompt) | Replace all occurrences with interactive confirmation (`y/n/a/q`) |
| `:<start>,<end>s/old/new/g` | Line range | Replace across specified lines (e.g. `:10,25s/old/new/g`) |

### Undo & Redo
| Key | Action | Notes |
|-----|--------|-------|
| `u` | Undo | Undo last edit action |
| `U` | Line Undo | Restore entire current line to its original state |
| `Ctrl + r` | Redo | Redo previously undone action (standard Vim feature) |
| `.` | Repeat | Repeat last editing command |

---

## 8. Environment & Configuration Settings

Configure options dynamically in Ex Mode or save permanently in `~/.vimrc` or `~/.exrc`.

| Setting Command | Opposite Command | Effect |
|-----------------|------------------|--------|
| `:set number` (`:set nu`) | `:set nonumber` (`:set nonu`) | Display / hide line numbers |
| `:set ignorecase` (`:set ic`) | `:set noignorecase` (`:set noic`) | Case-insensitive / sensitive search |
| `:set smartcase` (`:set scs`) | `:set nosmartcase` | Case-insensitive unless uppercase letter used |
| `:set hlsearch` (`:set hls`) | `:set nohlsearch` (`:nohlsearch`) | Highlight search matches (or clear highlights) |
| `:set autoindent` (`:set ai`) | `:set noautoindent` | Preserve indentation level on new lines |
| `:set tabstop=4` (`:set ts=4`) | — | Set tab character display width to 4 spaces |
| `:set shiftwidth=4` (`:set sw=4`) | — | Set indentation shift width for `>` and `<` |
| `:set expandtab` (`:set et`) | `:set noexpandtab` | Convert tabs to spaces on insert |
| `:set wrap` | `:set nowrap` | Enable / disable visual line wrapping |
| `:syntax on` | `:syntax off` | Enable / disable syntax highlighting (Vim) |

---

## 🔗 See Also

- [Resources Knowledge Index](_INDEX.md) — Master catalog of all reference documentation
- [AI-Searchable Document Template](Templates/AI-SEARCHABLE-DOC-TEMPLATE.md) — Structural guide for markdown documentation
- [Search Router Tools Reference](copilot/search-router/TOOLS_REFERENCE.md) — Multi-index search tools across workspace

---

## 📝 Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-10-11 | Converted unformatted notes to full AI-Searchable Document Template standard | GitHub Copilot |
| 2026-03-23 | Initial raw notes compilation | thatsafact |