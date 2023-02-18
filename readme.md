# joplin-sticky-notes

## FAQ

Why PySide and not Gtk?

The first implementation was done in Gtk. However, there were a few obstacles:

- There seems to be no viable cross platform module. "StatusIcon" is deprecated and "AppIndicator" is linux only. See also: https://stackoverflow.com/questions/41917903/gtk-3-statusicon-replacement
- PySide has better markdown support. For Gtk, a WebKit2 had to be used. There is no usable python port for Windows and Macos.
