import pytest

from editor.core import undo


class UndoTester(undo.UndoStack):
    def __init__(self):
        super().__init__()
        self._value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    @undo.with_undo("setter")
    def value(self, v):
        self._value = v

    def create_snapshot(self):
        return self._value

    def restore_snapshot(self, snapshot):
        self._value = snapshot


def test_undo():
    u = UndoTester()
    u.value = 1
    u.undo()
    assert u.value == 0


def test_redo():
    u = UndoTester()
    u.value = 1
    u.undo()
    u.redo()
    assert u.value == 1


def test_empty_undo():
    u = UndoTester()
    with pytest.raises(undo.UndoException):
        u.redo()


def test_empty_redo():
    u = UndoTester()
    with pytest.raises(undo.UndoException):
        u.undo()


def test_clearing():
    u = UndoTester()
    u.value = 1
    u.value = 2
    u.undo()
    u.clear_all_undo()
    with pytest.raises(undo.UndoException):
        u.undo()
    with pytest.raises(undo.UndoException):
        u.redo()


def test_drop_redo():
    u = UndoTester()
    u.value = 1
    u.undo()
    u.value = 3
    with pytest.raises(undo.UndoException):
        u.redo()


def test_not_implemented():
    u = undo.UndoStack()
    with pytest.raises(NotImplementedError):
        u.create_snapshot()
    with pytest.raises(NotImplementedError):
        u.restore_snapshot(None)


def test_push_none():
    u = UndoTester()
    u.push_undo("auto")
    u._value = 1
    u.undo()
    assert u.value == 0
