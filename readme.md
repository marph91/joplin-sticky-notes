# joplin-sticky-notes

## FAQ

### Why is there no single executable?

1. It is really cumbersome to get the ci to work and maintain it.
2. The executable is greater than 30 MB, since the whole python interpreter and QT are contained.

### Why PySide and not Gtk?

The first implementation was done in Gtk. However, there were a few obstacles:

- There seems to be no viable cross platform module. "StatusIcon" is deprecated and "AppIndicator" is linux only. See also: https://stackoverflow.com/questions/41917903/gtk-3-statusicon-replacement
- PySide has better markdown support. For Gtk, a WebKit2 had to be used. There is no usable python port for Windows and Macos.
