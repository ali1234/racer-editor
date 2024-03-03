import numpy as np
from PySide6 import QtCore, QtGui


class Camera(QtCore.QObject):
    moved = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self._x = 0
        self._y = 0
        self._pitch = 0
        self._rotation = 0
        self._zoom = 6
        self.rotation_locked = False

    def resize(self, w, h):
        self._w = w
        self._h = h
        self._aspect = w / h
        self._proj = QtGui.QMatrix4x4()
        self._proj.setToIdentity()
        self._proj.ortho(-1 * self._aspect, 1 * self._aspect, -1, 1, -100, 100)
        self._scrn = QtGui.QMatrix4x4()
        self._scrn.scale(self._w / 2, -self._h / 2, 1)
        self._scrn.translate(1, -1, 0)
        self._scrn *= self._proj

    def unproject(self, x, y):
        """Projects screen coordinates back to the world xy plane."""
        scrn_np_i = np.array(self.scrn.inverted()[0].data()).reshape(4, 4)
        sv = np.array(((x, y, 0, 1), (x, y, 1, 1)))
        wv = np.matmul(sv, scrn_np_i)
        a = wv[1, :3] - wv[0, :3]
        if a[2] == 0:
            return 0, 0
        dx = a[0] / a[2]
        dy = a[1] / a[2]
        return wv[0, 0] - dx * wv[0, 2], wv[0, 1] - dy * wv[0, 2]

    @property
    def scrn(self):
        """QMatrix4x4 representing the transformation between world space and screen space."""
        return self._scrn * self.view

    @property
    def proj(self):
        """QMatrix4x4 representing the projection matrix."""
        return self._proj

    @property
    def view(self):
        """QMatrix4x4 representing the view matrix."""
        view = QtGui.QMatrix4x4()
        view.scale(1 / (self._zoom**3))
        view.rotate(self._pitch, -1, 0, 0)
        view.rotate(self._rotation, 0, 0, 1)
        view.translate(-self._x, -self._y, 0)
        return view

    def zoom(self, z):
        self._zoom = min(12, max(1, self._zoom - z))
        self.moved.emit()

    def translate(self, x, y):
        self._x -= x
        self._y -= y
        self.moved.emit()

    def rotate(self, dx, dy):
        if not self.rotation_locked:
            self._rotation += dx * 0.3
            self._pitch -= dy * 0.3
            self._pitch = max(0, min(80, self._pitch))
            self.moved.emit()


class LockedCamera(Camera):
    def __init__(self):
        super().__init__()
        self._x = 500

    def rotate(self, dx, dy):
        pass
