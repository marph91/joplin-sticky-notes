# pylint: disable=no-name-in-module,missing-function-docstring
import os
import sys
import webbrowser

from PySide6.QtWidgets import (
    QApplication,
    QTextEdit,
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
    QMainWindow
)
from PySide6.QtCore import Qt, QRect, QSettings, QTimer
from PySide6.QtGui import QIcon, QAction
import requests

from joplin_api_helper import setup_joplin, create_hierarchy
from note_selection import NoteSelection


class NoteManager:
    def __init__(self):
        # self.dummy_parent = QMainWindow()
        # self.dummy_parent.setWindowFlags(Qt.Tool)
        # self.dummy_parent.hide()

        self.notes = []

        # https://doc.qt.io/qtforpython/PySide6/QtCore/QSettings.html#locations-where-application-settings-are-stored
        self.settings = QSettings("joplin-sticky-notes", "joplin-sticky-notes")
        for index in range(self.settings.beginReadArray("notes")):
            self.settings.setArrayIndex(index)
            self.new_note(
                self.settings.value("geometry"),
                # QSettings seems to not support bool properly.
                self.settings.value("visible") == "true",
                self.settings.value("title"),
                self.settings.value("content"),
                self.settings.value("id"),
            )
        self.settings.endArray()

    def check_joplin_status(self, timer):
        # TODO: Communicate via notification?

        try:
            joplin_api.ping()
            connected = True
            timer.stop()
            print("Joplin Status: Connected")
        except requests.exceptions.ConnectionError:
            connected = False
            print("Connect Joplin")

        return not connected  # Invert to keep the loop running if not connected.

    def new_note(
        self,
        geometry=QRect(40, 40, 400, 300),
        visible=True,
        title="New Note",
        content="",
        id_=None,
    ):

        window = NoteWindow()
        window.setGeometry(geometry)
        window.note_body.setVisible(visible)
        window.grip.setVisible(visible)
        window.title_bar.label.setText(title)
        window.note_body.setMarkdown(content)
        window.show()
        window.activateWindow()
        window.raise_()

        self.notes.append(
            {
                "window": window,
                "title": title,
                "content": content,
                "id": id_,
            }
        )

    def delete_note(self, note_window):
        self.notes = [note for note in self.notes if note["window"] != note_window]

    def save_notes(self):
        print("save", len(self.notes))

        self.settings.beginWriteArray("notes", size=len(self.notes))
        for index, note in enumerate(self.notes):
            self.settings.setArrayIndex(index)
            self.settings.setValue("geometry", note["window"].geometry())
            self.settings.setValue("visible", note["window"].note_body.isVisible())
            self.settings.setValue("title", note["title"])
            self.settings.setValue("content", note["content"])
            self.settings.setValue("id", note["id"])
        self.settings.endArray()


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QHBoxLayout()
        self.layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # toggle body button
        self.toggle_body_button = QPushButton()
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_body_button.setSizePolicy(size_policy)
        icon = QIcon(QIcon.fromTheme("view-fullscreen"))
        self.toggle_body_button.setIcon(icon)
        self.layout.addWidget(self.toggle_body_button)

        # note title
        self.label = QLabel("New Note")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # configure menu
        self.configure_menu = QMenu()

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
        icon1 = QIcon(QIcon.fromTheme("preferences-system"))
        self.configure_button.setIcon(icon1)
        self.configure_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.configure_button.setMenu(self.configure_menu)
        self.layout.addWidget(self.configure_button)

        # clone button
        self.clone_button = QPushButton()
        self.clone_button.setSizePolicy(size_policy)
        icon2 = QIcon(QIcon.fromTheme("edit-copy"))
        self.clone_button.setIcon(icon2)
        self.layout.addWidget(self.clone_button)

        # delete button
        self.delete_button = QPushButton()
        self.delete_button.setSizePolicy(size_policy)
        icon3 = QIcon(QIcon.fromTheme("edit-clear"))
        self.delete_button.setIcon(icon3)
        self.delete_button.setFlat(False)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

        # callbacks
        self.toggle_body_button.clicked.connect(self.on_toggle_body_clicked)
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
        note = [note for note in nm.notes if note["window"] == window][0]
        # move clone slightly
        geometry = window.geometry()
        geometry.adjust(20, 20, 20, 20)
        nm.new_note(
            geometry,
            window.note_body.isVisible(),
            note["title"],
            note["content"],
            note["id"],
        )

    def on_close_clicked(self):
        window = self.window()
        nm.notes = [note for note in nm.notes if note["window"] != window]
        self.parent.close()

    def on_open_joplin_clicked(self):
        # https://joplinapp.org/external_links
        # TODO: more elegant way (requests doesn't work)
        webbrowser.open(
            "joplin://x-callback-url/openNote?id=6bcade4e7298483d91cff4dd854cd7a7"
        )

    def on_choose_note_clicked(self):
        # ignore any clicks on other windows
        for note in nm.notes:
            note["window"].setEnabled(False)

        NoteSelection(note_hierarchy, self)

    def set_note(self, note_title, note_id):
        # enable the other windows again
        for note in nm.notes:
            note["window"].setEnabled(True)

        joplin_note = joplin_api.get_note(note_id, fields="body")

        # update ui
        self.label.setText(note_title)
        self.parent.note_body.setMarkdown(joplin_note.body)

        # update note manager
        note = [note for note in nm.notes if note["window"] == self.window()][0]
        note["title"] = note_title
        note["content"] = joplin_note.body
        note["id"] = note_id

    def on_update_hierarchy_clicked(self):
        global note_hierarchy
        note_hierarchy = create_hierarchy(joplin_api)


class NoteWindow(QFrame):
    def __init__(self):
        super().__init__()

        # no titlebar
        # don't show in taskbar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)  #  | Qt.Tool | Qt.ToolTip

        # small border
        self.setFrameStyle(QFrame.Box | QFrame.Plain)

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SetDefaultConstraint)

        # note title
        self.title_bar = TitleBar(self)
        self.layout.addWidget(self.title_bar)

        # note body
        self.note_body = QTextEdit()
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

    # def changeEvent(self, event):
    #     # https://stackoverflow.com/a/74052370/7410886
    #     if event.type() == QEvent.WindowStateChange:
    #         self.title_bar.windowStateChanged(self.windowState())

    def resizeEvent(self, event):  # pylint: disable=invalid-name
        rect = self.rect()
        self.grip.move(
            rect.right() - self.grip.width(), rect.bottom() - self.grip.height()
        )

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        if event.button() == Qt.LeftButton:
            self.click_pos = event.scenePosition().toPoint()

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        if hasattr(self, "click_pos") and self.click_pos is not None:
            self.window().move(event.globalPosition().toPoint() - self.click_pos)


def main():
    app.setQuitOnLastWindowClosed(False)

    save_timer = QTimer()
    save_timer.timeout.connect(nm.save_notes)
    save_timer.start(5000)

    connect_timer = QTimer()
    connect_timer.timeout.connect(lambda: nm.check_joplin_status(connect_timer))
    connect_timer.start(1000)

    # TODO: check joplin status

    #################create_tray_menu(app)
    # tray: https://www.pythonguis.com/tutorials/pyside6-system-tray-mac-menu-bar-applications/
    # tray icon
    tray = QSystemTrayIcon()
    icon = QIcon("img/logo_96_blue.png")
    tray.setIcon(icon)
    tray.setVisible(True)

    # tray menu
    menu = QMenu()

    new_note = QAction("New Note")
    new_note.triggered.connect(nm.new_note)
    menu.addAction(new_note)

    def show_all_notes():
        # https://stackoverflow.com/a/26316185/7410886

        for note in nm.notes:
            note["window"].show()
            note["window"].activateWindow()
            note["window"].raise_()

    show_all = QAction("Show All")
    show_all.triggered.connect(show_all_notes)
    menu.addAction(show_all)

    def hide_all_notes():
        for note in nm.notes:
            note["window"].hide()

    hide_all = QAction("Hide All")
    hide_all.triggered.connect(hide_all_notes)
    menu.addAction(hide_all)

    quit_ = QAction("Quit")
    quit_.triggered.connect(app.quit)
    menu.addAction(quit_)

    tray.setContextMenu(menu)
    #################

    sys.exit(app.exec())


if __name__ == "__main__":
    # TODO: how to test light mode?
    # app = QApplication(['-platform', 'windows:lightmode=2'])
    app = QApplication([])

    nm = NoteManager()

    is_test = bool(os.getenv("TEST"))
    if not is_test:
        joplin_api = setup_joplin(nm.settings)
        note_hierarchy = create_hierarchy(joplin_api)

    main()
