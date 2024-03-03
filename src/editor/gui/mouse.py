import numpy as np
from PySide6 import QtCore, QtWidgets


class BaseInteraction(QtCore.QObject):
    finished = QtCore.Signal()

    def __init__(self, widget, press_event, camera):
        super().__init__()
        self._widget = widget
        self._press_event = press_event.clone()
        self._mx = press_event.x()
        self._my = press_event.y()
        self._camera = camera

    def drag(self, event):
        pass

    def release(self, event):
        if event.button() == self._press_event.button():
            self.finished.emit()


class CameraTranslateInteraction(BaseInteraction):
    def drag(self, event):
        x0, y0 = self._camera.unproject(self._mx, self._my)
        x1, y1 = self._camera.unproject(event.x(), event.y())
        self._camera.translate(x1 - x0, y1 - y0)
        self._mx = event.x()
        self._my = event.y()


class CameraRotateInteraction(BaseInteraction):
    def drag(self, event):
        dx = event.x() - self._mx
        dy = event.y() - self._my
        self._mx = event.x()
        self._my = event.y()
        self._camera.rotate(dx, dy)
        self._mx = event.x()
        self._my = event.y()


class SelectInteraction(BaseInteraction):
    def __init__(self, widget, press_event, camera):
        super().__init__(widget, press_event, camera)
        self._control_points = self._widget.project_track(camera.scrn)
        self._rubber_band = None

    def drag(self, event):
        x = min(self._press_event.x(), event.x())
        y = min(self._press_event.y(), event.y())
        w = abs(event.x() - self._press_event.x())
        h = abs(event.y() - self._press_event.y())
        if w + h > 10:
            if not self._rubber_band:
                assert isinstance(self._widget, QtWidgets.QWidget)
                self._rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, self._widget)
                self._rubber_band.show()
            self._rubber_band.setGeometry(x, y, w, h)

    def release(self, event):
        if event.button() == self._press_event.button():
            multi = self._press_event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
            if self._rubber_band:
                rect = self._rubber_band.geometry()
                rx = self._control_points[:, 0] >= rect.x()
                ry = self._control_points[:, 1] >= rect.y()
                rxx = self._control_points[:, 0] <= (rect.width() + rect.x())
                ryy = self._control_points[:, 1] <= (rect.height() + rect.y())
                selected = np.where(np.logical_and(np.logical_and(rx, ry), np.logical_and(rxx, ryy)))[0]
                self._rubber_band.hide()
                self._rubber_band = None
            else:
                diff = np.linalg.norm(self._control_points - (event.x(), event.y()), axis=1)
                best = np.argmin(diff)
                if diff[best] < 25:
                    selected = best
                else:
                    selected = slice(0, 0)
            self._widget._track.select(selected, multi)
            self.finished.emit()


class TransformInteraction(BaseInteraction):
    def __init__(self, widget, press_event, camera):
        super().__init__(widget, press_event, camera)
        self._snapshot = self._widget._track.create_snapshot()
        self._modified = False

    def drag(self, event):
        x0, y0 = self._camera.unproject(self._mx, self._my)
        x1, y1 = self._camera.unproject(event.x(), event.y())
        self._widget.translate_points(x1 - x0, y1 - y0)
        self._mx = event.x()
        self._my = event.y()
        self._modified = True

    def release(self, event):
        if self._modified:
            name = f"Move Control Points {self._widget.description}"
            self._widget._track.push_undo(name, self._snapshot)
        super().release(event)


def MouseInteraction(widget, press_event, camera):
    if press_event.button() == QtCore.Qt.MouseButton.MiddleButton:
        return CameraTranslateInteraction(widget, press_event, camera)
    elif press_event.button() == QtCore.Qt.MouseButton.RightButton:
        return CameraRotateInteraction(widget, press_event, camera)
    elif press_event.button() == QtCore.Qt.MouseButton.LeftButton:
        if press_event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if len(widget._track.selected):
                return TransformInteraction(widget, press_event, camera)
        else:
            return SelectInteraction(widget, press_event, camera)
    return None
