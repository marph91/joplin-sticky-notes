# joplin-sticky-notes

Stick your Joplin notes to the desktop.

[![build](https://github.com/marph91/joplin-sticky-notes/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/build.yml)
[![lint](https://github.com/marph91/joplin-sticky-notes/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/lint.yml)
[![test](https://github.com/marph91/joplin-sticky-notes/actions/workflows/test.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/test.yml)

| Linux, dark theme | Windows, light theme |
| - | - |
| ![example_linux_dark_theme.png](img/example_linux_dark_theme.png) | ![example_windows_light_theme.png](img/example_windows_light_theme.png) |

## Motivation

Keeping important notes in mind, even when the Joplin app is in background or closed.

Related topics:

- <https://discourse.joplinapp.org/t/sticky-notes/3997/8>
- <https://discourse.joplinapp.org/t/sticky-notes-on-desktop/13767>
- <https://discourse.joplinapp.org/t/lock-joplin-to-forefront/21527>

## Features

### What can this application do?

- Display Joplin notes, even when Joplin is offline
- Remember position, content, etc. of the notes across script and pc restarts
- Display images
- Open links and PDF files in an external application on click
- Open the note directly in Joplin

### What can't this application do?

- Modify notes
- Render special cases, like for example mermaid code blocks
- Render checkboxes properly, since they aren't in the [supported subset](https://doc.qt.io/qt-6/richtext-html-subset.html) of QTextBrowser

## Installation

There are two ways for installation:

1. Single file executable from the releases page: [**Linux**](https://github.com/marph91/joplin-sticky-notes/releases/latest/download/joplin-sticky-notes-linux) | [**Windows**](https://github.com/marph91/joplin-sticky-notes/releases/latest/download/joplin-sticky-notes-windows.exe) | [**MacOS**](https://github.com/marph91/joplin-sticky-notes/releases/latest/download/joplin-sticky-notes-darwin).
   - Recommended if you don't have experience in installing python modules.
2. `pip install git+https://github.com/marph91/joplin-sticky-notes.git`
   - Recommended if you have a working python environment and know how to install modules.

The single file executable seems to be convenient, but has some disadvantages:

1. It is really cumbersome to get the ci to work and maintain it.
2. The executable is greater than 30 MB, since the whole python interpreter and QT are contained.
3. It may be wrongly flagged as virus from windows.

## Usage

1. Activate Joplin's webclipper
2. `python -m joplin_sticky_notes`
3. Authorize the request in Joplin
4. Add the first note through the tray icon

To start the script automatically after boot, you can add it to the autostart of your OS. Make sure it starts after Joplin.

Examples:

- [Linux/KDE](integration/joplin-sticky-notes.desktop)
- [Windows 10](integration/joplin-sticky-notes.vbs)

## Development

```sh
git clone https://github.com/marph91/joplin-sticky-notes.git
cd joplin-sticky-notes
pip install -e .
python -m unittest -v
```

## Lessons learned

### PySide or Gtk?

The first implementation was done in Gtk. However, there were a few obstacles:

1. There seems to be no viable cross platform module for the tray. "StatusIcon" is deprecated and "AppIndicator" is linux only. See also: <https://stackoverflow.com/questions/41917903/gtk-3-statusicon-replacement>
2. PySide has better markdown support. For Gtk, a WebKit2 had to be used. There is no viable python port for Windows and Macos.
