# Use relative imports in __main__.py for pyinstaller compatibility.
# See: https://github.com/pyinstaller/pyinstaller/issues/2560
from joplin_sticky_notes.app import main


if __name__ == "__main__":
    main()
