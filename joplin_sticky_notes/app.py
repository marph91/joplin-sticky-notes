# pylint: disable=no-name-in-module,missing-function-docstring
import os
from pathlib import Path
import subprocess
import sys

from joppy.api import Api
from markdown import Markdown
from PySide6.QtWidgets import (
    QApplication,
    QTextBrowser,
    QWidget,
    QSystemTrayIcon,
    QMenu,
    QSizePolicy,
    QSizeGrip,
    QFrame,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QToolButton,
    QLabel,
    QStyle,
    QMessageBox,
)
from PySide6.QtCore import Qt, QRect, QSettings, QTimer, QUrl
from PySide6.QtGui import QAction, QIcon, QDesktopServices
import requests

from .api_helper import create_hierarchy, request_api_token
from .note_selection import NoteSelection


class NoteManager:
    def __init__(self):
        # https://doc.qt.io/qtforpython/PySide6/QtCore/QSettings.html#locations-where-application-settings-are-stored
        self.settings = QSettings("joplin-sticky-notes", "joplin-sticky-notes")

        self.notes = []
        self.md = Markdown(extensions=["nl2br", "sane_lists", "tables"])
        self.resource_path = Path(self.settings.fileName()).parent / "resources"
        self.resource_path.mkdir(exist_ok=True, parents=True)

        for index in range(self.settings.beginReadArray("notes")):
            self.settings.setArrayIndex(index)
            self.new_note(
                self.settings.value("geometry"),
                # QSettings seems to not support bool properly.
                self.settings.value("body_visible") in ("true", "True", True),
                self.settings.value("title"),
                self.settings.value("content"),
                self.settings.value("id"),
            )
        self.settings.endArray()

    def new_note(
        self,
        geometry=QRect(40, 40, 400, 300),
        body_visible=True,
        title="New Note",
        content="",
        id_=None,
    ):

        window = NoteWindow(id_, self)
        window.title_bar.info_id.setText(f"ID: {window.joplin_id}")
        window.setGeometry(geometry)
        window.note_body.setVisible(body_visible)
        window.grip.setVisible(body_visible)
        window.title_bar.label.setText(title)
        window.note_body.setHtml(content)
        window.show()
        window.activateWindow()
        window.raise_()

        # Identify by window, since the windows can have the same title or id.
        self.notes.append(window)

    def save_notes(self):
        self.settings.beginWriteArray("notes", size=len(self.notes))
        for index, window in enumerate(self.notes):
            self.settings.setArrayIndex(index)
            self.settings.setValue("geometry", window.geometry())
            self.settings.setValue("body_visible", window.note_body.isVisible())
            self.settings.setValue("title", window.title_bar.label.text())
            self.settings.setValue("content", window.note_body.toHtml())
            self.settings.setValue("id", window.joplin_id)
        self.settings.endArray()


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QHBoxLayout()
        self.layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # note title
        self.label = QLabel("New Note")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # configure menu
        self.configure_menu = QMenu()

        self.hide = QAction("Hide")
        self.hide.triggered.connect(self.parent.hide)
        self.configure_menu.addAction(self.hide)

        self.toggle_body = QAction("Toggle Body")
        self.toggle_body.triggered.connect(self.on_toggle_body_clicked)
        self.configure_menu.addAction(self.toggle_body)

        self.choose_note = QAction("Choose Joplin Note")
        self.choose_note.triggered.connect(self.on_choose_note_clicked)
        self.configure_menu.addAction(self.choose_note)

        self.update = QAction("Update")
        self.update.triggered.connect(self.on_update_hierarchy_clicked)
        self.configure_menu.addAction(self.update)

        self.open_joplin = QAction("Open in Joplin")
        self.open_joplin.triggered.connect(self.on_open_joplin_clicked)
        self.configure_menu.addAction(self.open_joplin)

        self.information_menu = QMenu("Information")
        self.info_parent = QAction("Parent")
        self.info_parent.setEnabled(False)
        self.information_menu.addAction(self.info_parent)
        self.info_id = QAction("ID")
        self.info_id.setEnabled(False)
        self.information_menu.addAction(self.info_id)
        self.info_created = QAction("Created")
        self.info_created.setEnabled(False)
        self.information_menu.addAction(self.info_created)
        self.info_due = QAction("Due")
        self.info_due.setEnabled(False)
        self.information_menu.addAction(self.info_due)
        self.configure_menu.addMenu(self.information_menu)

        # configure button
        self.configure_button = QToolButton()
        self.configure_button.setDefaultAction(self.choose_note)
        configure_pixmap = QStyle.StandardPixmap.SP_FileDialogDetailedView
        configure_icon = self.style().standardIcon(configure_pixmap)
        self.configure_button.setIcon(configure_icon)
        self.configure_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.configure_button.setMenu(self.configure_menu)
        self.layout.addWidget(self.configure_button)

        # clone button
        self.clone_button = QPushButton()
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clone_button.setSizePolicy(size_policy)
        clone_pixmap = QStyle.StandardPixmap.SP_TitleBarNormalButton
        clone_icon = self.style().standardIcon(clone_pixmap)
        self.clone_button.setIcon(clone_icon)
        self.clone_button.setToolTip("Clone Note")
        self.layout.addWidget(self.clone_button)

        # delete button
        self.delete_button = QPushButton()
        self.delete_button.setSizePolicy(size_policy)
        delete_pixmap = QStyle.StandardPixmap.SP_TitleBarCloseButton
        delete_icon = self.style().standardIcon(delete_pixmap)
        self.delete_button.setIcon(delete_icon)
        self.delete_button.setToolTip("Delete Note")
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

        # callbacks
        self.clone_button.clicked.connect(self.on_clone_clicked)
        self.delete_button.clicked.connect(self.on_close_clicked)

        self.height_before = 0

    def on_toggle_body_clicked(self):
        target_visibility = not self.parent.note_body.isVisible()
        self.parent.note_body.setVisible(target_visibility)
        self.parent.grip.setVisible(target_visibility)

        width_before = self.parent.geometry().width()
        if not target_visibility:
            # Save the height if the note is going to be hidden.
            self.height_before = self.parent.geometry().height()
            new_height = 0
        else:
            new_height = self.height_before
        # shrink the window after body isn't visible anymore
        self.parent.adjustSize()

        # TODO: look for clean solution
        self.parent.resize(width_before, new_height)

    def on_clone_clicked(self):
        window = self.window()
        # move clone slightly
        geometry = window.geometry()
        geometry.adjust(20, 20, 20, 20)
        self.parent.nm.new_note(
            geometry,
            window.note_body.isVisible(),
            window.title_bar.label.text(),
            window.note_body.toHtml(),
            window.joplin_id,
        )

    def on_close_clicked(self):
        self.parent.nm.notes.remove(self.parent)
        self.parent.close()

    def on_open_joplin_clicked(self):
        # https://joplinapp.org/external_links
        QDesktopServices.openUrl(
            QUrl(f"joplin://x-callback-url/openNote?id={self.parent.joplin_id}")
        )

    def on_choose_note_clicked(self):
        NoteSelection(note_hierarchy, self)

    def set_note(self, note_title, note_id):
        # get the note
        joplin_note = joplin_api.get_note(note_id, fields="body")
        self.parent.joplin_id = note_id

        # get attached resources
        body_markdown = joplin_note.body
        resources = joplin_api.get_all_resources(note_id=note_id, fields="id")
        for resource in resources:
            if not Path(resource.id).exists():
                resource_binary = joplin_api.get_resource_file(resource.id)
                with open(self.parent.nm.resource_path / resource.id, "wb") as outfile:
                    outfile.write(resource_binary)
            # Replace joplin's local link with the path to the just downloaded resource.
            body_markdown = body_markdown.replace(
                f":/{resource.id}", str(self.parent.nm.resource_path / resource.id)
            )

        # convert note to html, since resources are not displayed when using
        # setMarkdown(). See: https://forum.qt.io/post/461601
        body_html = self.parent.nm.md.convert(body_markdown)

        # update ui
        self.label.setText(note_title)
        self.parent.note_body.setHtml(body_html)
        self.info_id.setText(f"ID: {note_id}")

    def on_update_hierarchy_clicked(self):
        global note_hierarchy
        note_hierarchy = create_hierarchy(joplin_api)


class NoteWindow(QFrame):
    def __init__(self, joplin_id, note_manager):
        super().__init__()

        # no titlebar
        # no taskbar (in windows)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)

        self.nm = note_manager

        # small border
        self.setFrameStyle(QFrame.Box | QFrame.Plain)

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SetDefaultConstraint)

        # note title and buttons
        self.title_bar = TitleBar(self)
        self.layout.addWidget(self.title_bar)

        # note body
        self.note_body = QTextBrowser()
        # Open the links manually, because else PDF files are opened inside the
        # QTextBrowser and it would crash.
        self.note_body.setOpenLinks(False)
        self.note_body.anchorClicked.connect(
            lambda link: QDesktopServices.openUrl(link)
        )
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.note_body.setSizePolicy(size_policy)
        self.note_body.setFrameShadow(QFrame.Sunken)
        self.note_body.setReadOnly(True)
        self.layout.addWidget(self.note_body)

        # grip at bottom right
        self.grip_size = 20
        self.grip = QSizeGrip(self)
        self.grip.resize(self.grip_size, self.grip_size)

        self.setLayout(self.layout)

        # for moving
        self.click_pos = None

        # some joplin specific infos
        self.joplin_id = joplin_id

    def show(self):
        # don't show in taskbar
        try:
            # Workaround to get multiple windows without task bar on X11.
            # See: https://stackoverflow.com/a/75584018/7410886
            # fmt: off
            subprocess.check_call([
                "xprop",
                "-f", "_NET_WM_STATE", "32a",
                "-id", str(self.winId()),
                "-set", "_NET_WM_STATE", "_NET_WM_STATE_SKIP_TASKBAR",
            ])
            # fmt: on
        except FileNotFoundError:
            pass  # Probably on windows/mac.

        super().show()

    # def changeEvent(self, event):
    #     # https://stackoverflow.com/a/74052370/7410886
    #     if event.type() == QEvent.WindowStateChange:
    #         self.title_bar.windowStateChanged(self.windowState())

    def resizeEvent(self, event):  # pylint: disable=invalid-name
        rect = self.rect()
        self.grip.move(
            rect.right() - self.grip.width(), rect.bottom() - self.grip.height()
        )
        # Reset click position to avoid unwanted moving after resizing on windows.
        self.click_pos = None

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        if event.button() == Qt.LeftButton:
            self.click_pos = event.scenePosition().toPoint()

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        if self.click_pos is not None:
            self.window().move(event.globalPosition().toPoint() - self.click_pos)


class Tray(QSystemTrayIcon):
    def __init__(self, parent, note_manager):
        super().__init__(parent)

        self.parent = parent
        self.nm = note_manager

        # icon
        self.setIcon(QIcon("img/logo_96_blue.png"))
        self.setVisible(True)

        # menu
        self.tray_menu = QMenu()

        # joplin status
        # self.joplin_status = QAction("Joplin Status: Not Connected")
        # self.joplin_status.setEnabled(False)
        # self.tray_menu.addAction(self.joplin_status)

        # new note
        self.new_note = QAction("New Note")
        self.new_note.triggered.connect(note_manager.new_note)
        self.tray_menu.addAction(self.new_note)

        # notes
        self.notes_menu = QMenu("All Notes")
        self.show_all = QAction("Show")
        self.show_all.triggered.connect(self.show_all_notes)
        self.notes_menu.addAction(self.show_all)
        self.hide_all = QAction("Hide")
        self.hide_all.triggered.connect(self.hide_all_notes)
        self.notes_menu.addAction(self.hide_all)
        self.close_all = QAction("Close")
        self.close_all.triggered.connect(self.close_all_notes)
        self.notes_menu.addAction(self.close_all)
        self.tray_menu.addMenu(self.notes_menu)

        # quit
        self.quit_ = QAction("Quit")
        self.quit_.triggered.connect(self.parent.quit)
        self.tray_menu.addAction(self.quit_)

        self.setContextMenu(self.tray_menu)

    def show_all_notes(self):
        # https://stackoverflow.com/a/26316185/7410886

        for note in self.nm.notes:
            note.show()
            note.activateWindow()
            note.raise_()

    def hide_all_notes(self):
        for note in self.nm.notes:
            note.hide()

    def close_all_notes(self):
        for note in self.nm.notes:
            note.close()
        self.nm.notes.clear()


def main():
    global joplin_api
    global note_hierarchy

    # TODO: how to test light mode?
    # app = QApplication(['-platform', 'windows:lightmode=2'])
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    nm = NoteManager()

    is_test = bool(os.getenv("TEST"))
    if is_test:
        stop_test_timer = QTimer()
        stop_test_timer.singleShot(10000, app.quit)
    else:
        # Try to get the token either from savefile or through Joplin.
        if (api_token := nm.settings.value("api_token", None)) is None:
            QMessageBox.information(
                None,
                "Connect to Joplin",
                "Please open Joplin, activate the webclipper. "
                "Then click ok and accept the request.",
            )
            api_token = request_api_token()
        if api_token is None:
            QMessageBox.critical(
                None,
                "Connect to Joplin",
                "Couldn't obtain API token. "
                "Please start Joplin and activate the webclipper.",
            )
            sys.exit(1)
        nm.settings.setValue("api_token", api_token)
        joplin_api = Api(token=api_token)

        # Check if the connection is working.
        try:
            joplin_api.ping()
            note_hierarchy = create_hierarchy(joplin_api)
        except requests.ConnectionError:
            note_hierarchy = []
            QMessageBox.warning(
                None,
                "Connect to Joplin",
                "Couldn't connect to Joplin. Check if it's running and "
                "the webclipper is activated.\n"
                "Starting anyway.",
            )

    # tray menu
    Tray(app, nm)

    # timer
    save_timer = QTimer()
    save_timer.timeout.connect(nm.save_notes)
    save_timer.start(5000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
