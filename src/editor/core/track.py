import json
import math
import numpy as np

from . import hermite
from .undo import UndoStack, with_undo


def Watcher(callback):
    class _Watcher(np.ndarray):
        def __setitem__(self, item, value):
            super().__setitem__(item, value)
            callback()
    return _Watcher


class TrackException(Exception):
    pass


class Track(UndoStack):
    def __init__(self, data=None):
        super().__init__()
        self.set_data(data)

    def data_set(self):
        """
        Called when data is set by loading.
        """
        pass

    def data_modified(self):
        """
        Called when values in self._data have been modified.
        The array referenced by self._data has not changed.
        """
        pass

    def data_moved(self):
        """
        Called when self._data has been moved.
        """
        pass

    def set_data(self, data, styles=None):
        if data is None or len(data) < 3:
            rads = [math.radians(d) for d in range(0, 360, 36)]
            dist = 500 / math.pi
            data = [(dist * math.sin(r), dist * math.cos(r)) for r in rads]
        self._data = np.zeros((len(data), 4, 3), dtype=np.float32)
        self._data[:, 0, :len(data[0])] = data
        if styles is None:
            self._styles = np.zeros((len(data), ), dtype=np.uint32)
        else:
            self._styles = np.array(styles, dtype=np.uint32)
        self._selection = np.zeros((self._data.shape[0] + 1,), dtype=np.int32)
        self._tan = None
        self._len = None
        self._distances = None
        self.clear_all_undo()
        self.construct(keep=False)
        self.optimize()
        self.data_set()

    @property
    def P(self):
        return self._data[:, 0].view(Watcher(self.data_modified))

    @property
    def M(self):
        return self._data[:, 1]

    @property
    def A(self):
        return self._data[:, 2]

    @property
    def B(self):
        return self._data[:, 3]

    @property
    def S(self):
        return self._styles

    @property
    def total_length(self):
        return self._distances[-1, 1]

    def _update_distances(self):
        self._distances[0, 0] = 0
        self._distances[:, 1] = np.cumsum(self._len)
        self._distances[1:, 0] = self._distances[:-1, 1]

    def construct(self, keep=True):
        if not keep:
            self._tan = None
            self._len = None
        self.M[:], self.A[:], self.B[:], self._tan, self._len = hermite.construct(
            self._data[:, 0], self._tan, self._len
        )
        self._distances = np.empty((self._data.shape[0], 2), dtype=np.float32)
        self._update_distances()

    def optimize(self, max_opt_its=20, opt_steps=32):
        self.M[:], self.A[:], self.B[:], self._tan, self._len = hermite.optimize(
            self._data[:, 0], self._tan, self._len,
            max_opt_its, opt_steps
        )
        self._update_distances()

    def select(self, selection, multi=False):
        if not multi:
            self._selection[:] = 0
        self._selection[selection] ^= 1
        self._selection[-1] = self._selection[0]

    @property
    def selected(self):
        return np.where(self._selection[:-1])[0]

    @property
    def selected_segments(self):
        return np.where(self._selection[:-1] & self._selection[1:])[0]

    def create_snapshot(self):
        return self._data.copy(), self._styles.copy(), self._selection.copy()

    def restore_snapshot(self, snapshot):
        self._data, self._styles, self._selection = snapshot
        self.construct(keep=False)
        self.optimize()
        self.data_moved()

    @property
    def selected_inner(self):
        return np.where(self._selection[:-1] & self._selection[1:] & np.roll(self._selection[:-1], 1))[0]

    def _subdivide(self, segments):
        if not len(segments):
            raise TrackException("Nothing to subdivide.")
        p, dp, ddp = hermite.eval(self.P, self.M, self.A, self.B, self._len, [0.5])
        newdata = np.zeros((len(segments), 4, 3), dtype=np.float32)
        newdata[:, 0] = p[segments, 0]
        self._data = np.insert(self._data, segments+1, newdata, axis=0)
        self._styles = np.insert(self._styles, segments+1, self._styles[segments], axis=0)
        self._selection = np.insert(self._selection, segments+1, 1, axis=0)
        self._selection[-1] = self._selection[0]
        self.construct(keep=False)
        self.optimize()
        self.data_moved()

    @with_undo("Subdivide Segments")
    def subdivide(self):
        if not len(self.selected_segments):
            raise TrackException("No segments selected.")
        self._subdivide(self.selected_segments)

    @with_undo("Add After Control Points")
    def add_after(self):
        if not len(self.selected):
            raise TrackException("No control points selected.")
        self._subdivide(self.selected)

    @with_undo("Add Before Control Points")
    def add_before(self):
        if not len(self.selected):
            raise TrackException("No control points selected.")
        self._subdivide(self.selected - 1)

    def _delete(self, points):
        if not len(points):
            raise TrackException("Nothing to delete.")
        if self._data.shape[0] - len(points) < 3:
            raise TrackException("There must be at least three points at all times.")
        self._data = np.delete(self._data, points, axis=0)
        self._styles = np.delete(self._styles, points, axis=0)
        self._selection = np.delete(self._selection, points, axis=0)
        self._selection[-1] = self._selection[0]
        self.construct(keep=False)
        self.optimize()
        self.data_moved()

    @with_undo("Delete Control Points")
    def delete(self):
        if not len(self.selected):
            raise TrackException("No control points selected.")
        self._delete(self.selected)

    @with_undo("Dissolve Segments")
    def dissolve(self):
        if not len(self.selected_inner):
            raise TrackException("Nothing to dissolve.")
        self._delete(self.selected_inner)

    def serialize(self):
        data = []
        for n in range(self._data.shape[0]):
            data.append((*self._data[n, 0].astype(float), self._styles[n].astype(float)))
        return json.dumps(data, indent=4)

    def deserialize(self, jsonstr):
        j = json.loads(jsonstr)
        data = []
        styles = []
        for row in j:
            data.append(row[:3])
            styles.append(row[3])
        self.set_data(data, styles)
