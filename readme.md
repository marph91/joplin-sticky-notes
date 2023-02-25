# joplin-sticky-notes

Stick your Joplin notes to the desktop.

[![build](https://github.com/marph91/joplin-sticky-notes/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/build.yml)
[![lint](https://github.com/marph91/joplin-sticky-notes/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/lint.yml)
[![tests](https://github.com/marph91/joplin-sticky-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/marph91/joplin-sticky-notes/actions/workflows/tests.yml)

## Motivation

Keeping important notes in mind, even when the Joplin app is in background or closed.

Related topics:

- <https://discourse.joplinapp.org/t/sticky-notes/3997/8>
- <https://discourse.joplinapp.org/t/sticky-notes-on-desktop/13767>
- <https://discourse.joplinapp.org/t/lock-joplin-to-forefront/21527>

## Installation

Recommended: `pip install git+https://github.com/marph91/joplin-sticky-notes.git`

There are some executables as output of the [build workflow](https://github.com/marph91/joplin-sticky-notes/actions/workflows/build.yml). They are untested and should be considered as experimental.

## Usage

1. Activate Joplin's webclipper
2. `python -m joplin_sticky_notes`
3. Authorize the request in Joplin
4. Add the first note through the tray icon

## Development

```sh
git clone https://github.com/marph91/joplin-sticky-notes.git
cd joplin-sticky-notes
pip install -e .
python -m unittest -v
```

## FAQ

### Why is there no single executable?

1. It is really cumbersome to get the ci to work and maintain it.
2. The executable is greater than 30 MB, since the whole python interpreter and QT are contained.

### Why PySide and not Gtk?

The first implementation was done in Gtk. However, there were a few obstacles:

- There seems to be no viable cross platform module. "StatusIcon" is deprecated and "AppIndicator" is linux only. See also: <https://stackoverflow.com/questions/41917903/gtk-3-statusicon-replacement>
- PySide has better markdown support. For Gtk, a WebKit2 had to be used. There is no usable python port for Windows and Macos.
