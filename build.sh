#!/bin/sh

# setup venv
if [ ! -d .venv ]; then
    python3 -m venv --system-site-packages .venv
    . .venv/bin/activate
    python -m pip install -r requirements.txt
else
    . .venv/bin/activate
fi

# clear and build
rm -rf dist
python -OO -m PyInstaller pyinstaller_files/build_linux.spec --noconfirm

# exit venv
deactivate
