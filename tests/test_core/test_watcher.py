import numpy as np

from editor.core.track import Watcher


class WatcherTester:
    def __init__(self):
        self._arr = np.arange(3)
        self.called = False

    @property
    def arr(self):
        return self._arr.view(Watcher(self.callback))

    def callback(self):
        self.called = True


def test_watcher():
    w = WatcherTester()
    w.arr[0] = 4
    assert w.called
    assert w.arr[0] == 4
