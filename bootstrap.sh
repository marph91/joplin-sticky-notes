#!/bin/sh

# https://pygobject.readthedocs.io/en/latest/getting_started.html
if [ "$1" = "linux" ]; then
    sudo apt install libgirepository1.0-dev gir1.2-gtk-3.0 gir1.2-webkit2-4.1
elif [ "$1" = "macos" ]; then
    brew install pygobject3 gtk+3
elif [ "$1" = "windows" ]; then
    pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3 mingw-w64-x86_64-python3-gobject
else
    exit 1
fi
