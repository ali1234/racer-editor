import collections
import functools


class UndoException(Exception):
    pass


def with_undo(name):
    def dec(f):
        @functools.wraps(f)
        def _with_undo(self, *args, **kwargs):
            snapshot = self.create_snapshot()
            f(self, *args, **kwargs)
            self.push_undo(name, snapshot)
        return _with_undo
    return dec


class UndoStack:
    def __init__(self):
        self._undo = collections.deque()
        self._redo = collections.deque()

    def create_snapshot(self):
        raise NotImplementedError

    def restore_snapshot(self, snapshot):
        raise NotImplementedError

    def clear_all_undo(self):
        self._undo.clear()
        self._redo.clear()

    def push_undo(self, name, snapshot=None):
        if snapshot is None:
            snapshot = self.create_snapshot()
        self._undo.append((name, snapshot))
        self._redo.clear()

    def undo(self):
        try:
            name, snapshot = self._undo.pop()
        except IndexError:
            raise UndoException("Nothing to undo.")
        else:
            self._redo.append((name, self.create_snapshot()))
            self.restore_snapshot(snapshot)

    def redo(self):
        try:
            name, snapshot = self._redo.pop()
        except IndexError:
            raise UndoException("Nothing to redo.")
        else:
            self._undo.append((name, self.create_snapshot()))
            self.restore_snapshot(snapshot)
