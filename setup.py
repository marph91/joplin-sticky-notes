"""
https://cx-freeze.readthedocs.io/en/latest/setup_script.html#setup-script
https://github.com/achadwick/hello-cxfreeze-gtk/blob/master/setup.py
"""

import sys
from cx_Freeze import setup, Executable


# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": [
        "joppy",
        "gi",
        # markdown related
        "markdown",
        "html",
    ],
    "include_files": ["note.glade", "tray.glade", "style.css"],
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="joplin-sticky-notes",
    version="0.1",
    description="Joplin Sticky Notes",
    options={"build_exe": build_exe_options},
    executables=[Executable("joplin_sticky_notes.py", base=base)],
)
