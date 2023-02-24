import asyncio
import tempfile
import unittest

from PySide6.QtCore import Qt, QRect, QSettings
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from joplin_sticky_notes.app import Tray, NoteManager


class QtTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # https://github.com/jopohl/urh/blob/71153babe497a1dafa12f8dd371ed0adc305a8bb/tests/QtTestCase.py
        cls.app = QApplication([])

        # settings
        cls.settings_folder = tempfile.TemporaryDirectory()
        QSettings.setPath(
            QSettings.defaultFormat(), QSettings.UserScope, cls.settings_folder.name
        )
        # only to get the filename
        cls.settings = NoteManager().settings
        cls.settings.clear()

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
        del cls.app
        cls.settings_folder.cleanup()


class Settings(QtTestCase):
    def test_note_from_settings(self):

        # TODO: Default width is much bigger on windows and mac.
        geometry = QRect(100, 100, 500, 500)
        note_visible = True
        body_visible = True
        title = "title"
        content = "content"
        id_ = "test id"

        self.settings.beginWriteArray("notes", size=1)
        for index in range(1):
            self.settings.setArrayIndex(index)
            self.settings.setValue("geometry", geometry)
            self.settings.setValue("note_visible", note_visible)
            self.settings.setValue("body_visible", body_visible)
            self.settings.setValue("title", title)
            self.settings.setValue("content", content)
            self.settings.setValue("id", id_)
        self.settings.endArray()

        # settings are loaded in the note manager
        nm = NoteManager()

        self.assertEqual(len(self.app.allWindows()), 1)
        self.assertEqual(len(nm.notes), 1)
        self.assertEqual(nm.notes[0].geometry(), geometry)
        self.assertEqual(nm.notes[0].isVisible(), note_visible)
        self.assertEqual(nm.notes[0].note_body.isVisible(), body_visible)
        self.assertEqual(nm.notes[0].title_bar.label.text(), title)
        self.assertEqual(nm.notes[0].note_body.toMarkdown().strip(), content)
        self.assertEqual(nm.notes[0].joplin_id, id_)
