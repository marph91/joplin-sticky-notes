# pylint: disable=no-name-in-module,missing-function-docstring
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt


class NoteSelection(QTreeWidget):
    def __init__(self, hierarchy, parent):
        super().__init__(parent)
        self.parent = parent
        self.setEnabled(True)

        self.setWindowFlags(Qt.Dialog)

        self.setWindowTitle("Choose Note")

        self.hierarchy = hierarchy

        self.setColumnCount(2)
        self.setColumnHidden(1, True)
        self.setHeaderHidden(True)
        self.setAlternatingRowColors(True)
        self.setExpandsOnDoubleClick(False)
        self.fill_tree()
        self.itemDoubleClicked.connect(self.on_item_clicked)
        self.show()
        self.activateWindow()
        self.raise_()

    def fill_tree(self):
        def populate_store_from_hierarchy(hierarchy, root=self):
            for item in hierarchy:
                new_root = QTreeWidgetItem(root)
                new_root.setText(0, item.data.title)
                new_root.setText(1, None)
                new_root.setExpanded(True)
                populate_store_from_hierarchy(item.child_items, new_root)
                for note in item.child_notes:
                    item = QTreeWidgetItem(new_root)
                    item.setText(0, note.title)
                    item.setText(1, note.id)

        populate_store_from_hierarchy(self.hierarchy)

    def on_item_clicked(self, item):
        if item.text(1):
            self.parent.set_note(item.text(0), item.text(1))
            self.close()
