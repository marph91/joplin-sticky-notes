# sudo apt install libgtk-3-0 libgtk-3-dev
# sudo apt install gir1.2-appindicator3-0.1 gir1.2-webkit2-4.1
# https://github.com/linuxmint/sticky/blob/8b8bf3025370be11a45b553db20e7cf193807a4a/usr/lib/sticky/sticky.py#L910
# https://github.com/nieseman/traymenu/blob/main/traymenu/gtk.py

from dataclasses import dataclass
import json
from pathlib import Path
import time

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk
from gi.repository import AppIndicator3 as appindicator
import gi.repository.WebKit2 as WebKit2
from markdown import Markdown

from joplin_api_helper import setup_joplin, create_hierarchy


def get_size_(window):
    """Convenience wrapper to get the window size as tuple:"""
    size = window.get_size()
    return (size.width, size.height)


def get_position_(window, offset=(0, 0)):
    """Convenience wrapper to get the window position as tuple:"""
    position = window.get_position()
    return (position.root_x + offset[0], position.root_y + offset[1])


class NoteManager:
    """Load and save notes."""

    def __init__(self):
        # Needed to prevent:
        # gi.repository.GLib.GError: gtk-builder-error-quark: note.glade:255:1 Invalid type function 'webkit_settings_get_type' (0)
        WebKit2.WebView

        self.notes = []
        self.md = Markdown(extensions=["nl2br", "sane_lists", "tables"])

        with open("ui/style.css") as infile:
            style_sheet_content = "\n".join(infile.readlines())
        self.webview_style_sheet = WebKit2.UserStyleSheet(
            style_sheet_content,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserStyleLevel.USER,
        )

        self.settings_file = Path().home() / ".joplin-sticky-notes/notes.json"
        if self.settings_file.exists():
            try:
                with open(self.settings_file) as infile:
                    saved_notes = json.load(infile)
            except json.decoder.JSONDecodeError:
                return  # no notes to import
            for note in saved_notes:
                self.new_note(**note)
        else:
            self.settings_file.parent.mkdir(exist_ok=True)

    def new_note(
        self,
        position=(40, 40),
        size=(400, 200),
        visible=True,
        title="New Note",
        content="",
        id=None,
    ):

        # Create a new builder for each note.
        builder = Gtk.Builder()
        builder.add_from_file("ui/note.glade")

        # Link the popover menu manually, since populating it doesn't work in glade.
        # https://gitlab.gnome.org/GNOME/glade/-/issues/509
        configure_menu = builder.get_object("configure_menu")
        configure_menu_button = builder.get_object("configure_menu_button")
        configure_menu_button.set_popup(configure_menu)

        # final note layout
        note_window = builder.get_object("note_body")
        title_bar = builder.get_object("note_title")
        note_window.set_titlebar(title_bar)
        note_window.move(*position)
        note_window.show_all()

        body = note_window.get_child()
        # Inject a custom style sheet to apply light/dark theme in the webview.
        content_manager = body.get_user_content_manager()
        content_manager.add_style_sheet(self.webview_style_sheet)
        # https://webkitgtk.org/reference/webkit2gtk/stable/method.WebView.load_html.html
        body.load_html(self.md.convert(content), "")

        if visible:
            note_window.resize(*size)
        else:
            note_window.resize(size[0], 1)
        body.set_visible(visible)

        note_window.set_title(title)

        self.notes.append(
            {
                "window": note_window,
                "title": title,
                "content": content,
                "id": id,
            }
        )

        builder.connect_signals(NoteHandler(note_window))

    def delete_note(self, note_window):
        self.notes = [note for note in self.notes if note["window"] != note_window]

    def save_notes(self):
        print("save", len(self.notes))
        notes_to_save = []
        for note in self.notes:
            note_window = note["window"]
            notes_to_save.append(
                {
                    "position": get_position_(note_window),
                    "size": get_size_(note_window),
                    "visible": note_window.get_child().props.visible,
                    # Store all other data except of the window.
                    **{key: note[key] for key in note if key != "window"},
                }
            )
        with open(self.settings_file, "w") as outfile:
            json.dump(notes_to_save, outfile, indent=2)

        return True  # To keep the loop running.


class NoteHandler:
    """Handles all clicks inside a note."""

    def __init__(self, note_window):
        # Default values to avoid errors after restart.
        self.position_before_hide = (40, 40)
        self.size_before_hide = (400, 200)

        self.selected_note = None

        self.note_window = note_window

    def on_show_hide_body_clicked(self, button):
        body = self.note_window.get_child()
        if body.props.visible:
            size = self.note_window.get_size()
            self.size_before_hide = (size.width, size.height)
            self.note_window.resize(size.width, 1)
        else:
            self.note_window.resize(*self.size_before_hide)
        body.set_visible(not body.props.visible)

    def on_note_selection_changed(self, selection):
        # https://stackoverflow.com/a/7938561/7410886
        model, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            self.selected_note = model[tree_iter][:]
            return  # should be a single selected value anyway

    def on_clone_clicked(self, button):
        note = [note for note in nm.notes if note["window"] == self.note_window][0]
        body = self.note_window.get_child()
        nm.new_note(
            get_position_(self.note_window, offset=(20, 20)),
            get_size_(self.note_window),
            body.props.visible,
            note["title"],
            note["content"],
            note["id"],
        )

    def on_delete_clicked(self, button):
        nm.delete_note(self.note_window)
        self.note_window.destroy()

    # Note selection window

    def on_update_notes_clicked(self, button):
        global note_hierarchy
        note_hierarchy = create_hierarchy(joplin_api)

        # TODO: simple update the treestore
        button.get_window().destroy()
        self.on_choose_joplin_note_activate()

    def on_select_note_clicked(self, button):
        if self.selected_note is not None and self.selected_note[1] is not None:

            # update the ui
            self.note_window.set_title(self.selected_note[0])
            # TODO: add other infos
            body = self.note_window.get_child()
            joplin_note = joplin_api.get_note(self.selected_note[1], fields="body")
            body.load_html(nm.md.convert(joplin_note.body), "")
            button.get_window().destroy()

            # update the note manager
            note = [note for note in nm.notes if note["window"] == self.note_window][0]
            note["title"] = self.selected_note[0]
            note["content"] = joplin_note.body
            note["id"] = self.selected_note[1]
        else:
            print("Invalid selection")

    def on_choose_joplin_note_activate(self, *args):
        # https://stackoverflow.com/a/74833667/7410886
        # https://www.tutorialspoint.com/pygtk/pygtk_treeview_class.htm
        builder = Gtk.Builder()
        builder.add_from_file("ui/note.glade")
        builder.connect_signals(self)

        # Fill tree with data.
        def populate_store_from_hierarchy(store, hierarchy, root=None):
            for item in hierarchy:
                new_root = store.append(root, [item.data.title, None])
                populate_store_from_hierarchy(store, item.child_items, new_root)
                for note in item.child_notes:
                    store.append(new_root, [note.title, note.id])

        store = builder.get_object("note_selection_store")
        populate_store_from_hierarchy(store, note_hierarchy)

        # TODO: possible from glade?
        treeview = builder.get_object("note_selection_tree")
        treeview.expand_all()
        window = builder.get_object("note_selection_window")
        window.show_all()


class TrayHandler:
    """
    Handles all tray interactions.
    The tray is the starting point to add the first note.
    """

    def __init__(self, joplin_status):
        self.joplin_status = joplin_status

    def check_joplin_status(self):
        try:
            joplin_api.ping()
            connected = True
            self.joplin_status.set_label("Joplin Status: Connected")
        except requests.exceptions.ConnectionError:
            connected = False
            self.joplin_status.set_label("Connect Joplin")
        self.joplin_status.set_sensitive(not connected)

        return not connected  # Invert to keep the loop running if not connected.

    def on_connect_joplin_activate(self, *args):
        setup_joplin()
        self.check_joplin_status()

    def on_new_note_activate(self, *args):
        nm.new_note()

    # def on_show_all_notes_activate(self, *args):
    #     # Bringing windows to foreground/background doesn't seem to work:
    #     # https://gitlab.gnome.org/GNOME/gtk/-/issues/1638
    #     for window in nm.notes:
    #         window.present()

    def on_quit_activate(self, *args):
        Gtk.main_quit()


def main():
    builder = Gtk.Builder()
    builder.add_from_file("ui/tray.glade")
    tray_handler = TrayHandler(builder.get_object("joplin_status"))
    builder.connect_signals(tray_handler)

    tray_menu = builder.get_object("tray_menu")
    indicator = appindicator.Indicator.new(
        "joplin-sticky-notes",
        str(Path(__file__).parent.parent / "img/logo_96_blue.png"),
        appindicator.IndicatorCategory.SYSTEM_SERVICES,
    )
    indicator.set_menu(tray_menu)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.get_menu().show_all()

    # Save the notes every 5 seconds.
    GLib.timeout_add_seconds(5, nm.save_notes)

    # Try to connect to joplin every 5 seconds.
    # Stops if the connection was successful.
    GLib.timeout_add_seconds(5, tray_handler.check_joplin_status)

    Gtk.main()


if __name__ == "__main__":
    joplin_api = setup_joplin()
    note_hierarchy = create_hierarchy(joplin_api)
    nm = NoteManager()
    main()
