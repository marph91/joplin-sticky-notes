#!/bin/sh

# setup venv
# if [ ! -d .venv ]; then
#     python3 -m venv --system-site-packages .venv
#     . .venv/bin/activate
#     python3 -m pip install -r requirements.txt
# else
#     . .venv/bin/activate
# fi
python3 -m pip install -r requirements.txt

# clear and build
rm -rf dist
python3 -OO -m PyInstaller "pyinstaller_files/build_linux.spec" --noconfirm

# exit venv
# deactivate
