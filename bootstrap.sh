#!/bin/sh

# https://pygobject.readthedocs.io/en/latest/getting_started.html
if [ "$1" = "linux" ]; then
    sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
elif [ "$1" = "macos" ]; then
    brew install pygobject3 gtk+3
elif [ "$1" = "windows" ]; then
    pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3 mingw-w64-x86_64-python3-gobject
else
    exit 1
fi
