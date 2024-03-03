import pathlib
import functools
from PySide6 import QtCore, QtWidgets


def ask_if_unsaved(f):
    @functools.wraps(f)
    def _ask_if_unsaved(self):
        if self.warning():
            return f(self)
    return _ask_if_unsaved


class OpenSaveController(QtCore.QObject):
    changed = QtCore.Signal()

    def __init__(self, document_type):
        super().__init__()
        self._document_type = document_type
        self._filepath = None
        self._unsaved = False

    @property
    def filename(self):
        if self._filepath is None:
            return f'New {self._document_type}'
        else:
            return self._filepath.name

    @property
    def unsaved(self):
        return self._unsaved

    @unsaved.setter
    def unsaved(self, value):
        self._unsaved = value
        self.changed.emit()

    def set_unsaved(self):
        self.unsaved = True

    def warning(self):
        if self.unsaved:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle(f"The {self._document_type} has been modified.")
            msg.setText("Do you want to save your changes?")
            msg.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel
            )
            msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Save)
            ret = msg.exec()
            if ret == QtWidgets.QMessageBox.StandardButton.Save:
                return self.save()
            elif ret == QtWidgets.QMessageBox.StandardButton.Discard:
                return True
            else:
                return False
        else:
            return True

    @ask_if_unsaved
    def new(self):
        self._filepath = None
        self.unsaved = False
        return True

    @ask_if_unsaved
    def open(self):
        path, filter = QtWidgets.QFileDialog.getOpenFileName()
        self._filepath = pathlib.Path(path)
        self.unsaved = False
        return self._filepath

    def saveas(self):
        path, filter = QtWidgets.QFileDialog.getSaveFileName()
        if path:
            self._filepath = pathlib.Path(path)
            self.unsaved = False
            return self._filepath
        else:
            return None

    def save(self):
        if self._filepath is None:
            return self.saveas()
        else:
            self.unsaved = False
            return self._filepath
