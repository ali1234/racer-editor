import numpy as np
from PySide6 import QtOpenGLWidgets
import OpenGL.GL as gl

from .mouse import MouseInteraction
from .camera import Camera, LockedCamera
from .shaders import ShaderProgram, Buffer


class BaseView(QtOpenGLWidgets.QOpenGLWidget):
    Camera = Camera
    description = "???"
    _grid_data = np.array(((1, 1), (-1, 1), (1, -1), (-1, -1)), dtype=np.float32) * 2000

    def __init__(self, parent, track):
        super().__init__(parent)
        self._track = track
        self._track.visualChanged.connect(self.update)
        self._track.selectionChanged.connect(self.update)
        self._camera = self.Camera()
        self._camera.moved.connect(self.update)
        self._interaction = None

    def initializeGL(self):
        self._track.add_to_widget(self)
        self._grid = ShaderProgram('grid.vert', 'grid.frag')
        self._grid_vbo = Buffer(self._grid_data)

    def resizeGL(self, w, h):
        self._camera.resize(w, h)

    def draw_grid(self):
        self._grid.bind()
        self._grid.setAttribute('position', self._grid_vbo, gl.GL_FLOAT, 2)
        self._grid.setUniform('matrix', self._camera.proj * self._camera.view)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

    def paintGL(self):
        gl.glClearColor(0.24, 0.24, 0.24, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.draw_grid()

    def project_track(self, scrn):
        scrn_np = np.array(scrn.data()).reshape(4, 4)
        return (np.matmul(self._track.P, scrn_np[:3]) + scrn_np[3])[:, :2]

    def wheelEvent(self, event):
        if not self._interaction:
            self._camera.zoom(event.angleDelta().y() * 0.01)

    def mousePressEvent(self, event):
        if not self._interaction:
            self._interaction = MouseInteraction(self, event, self._camera)
            if self._interaction:
                self._interaction.finished.connect(self._interaction_finished)

    def _interaction_finished(self):
        self._interaction = None

    def mouseReleaseEvent(self, event):
        if self._interaction:
            self._interaction.release(event)

    def mouseMoveEvent(self, event):
        if self._interaction:
            self._interaction.drag(event)

    def translate_points(self, x, y):
        self._track.P[self._track.selected, :2] += (x, y)

    def reset_view_rotation(self):
        self._camera._rotation = 0
        self._camera._pitch = 0
        self.update()

class View3D(BaseView):
    description = "XY"

    def paintGL(self):
        super().paintGL()
        self._track.draw(self._camera.proj * self._camera.view, mode=0)


class View1D(BaseView):
    Camera = LockedCamera
    description = "Z"
    _grid_data = np.array(((10, 1), (0, 1), (10, -1), (0, -1)), dtype=np.float32) * 2000

    def paintGL(self):
        super().paintGL()
        self._track.draw(self._camera.proj * self._camera.view, mode=4)

    def project_track(self, scrn):
        scrn_np = np.array(scrn.data()).reshape(4, 4)
        return (
                       np.matmul(self._track._distances[:, 0:1], scrn_np[0:1])
                       + np.matmul(self._track.P[:, 2:], scrn_np[1:2]) + scrn_np[3]
               )[:, :2]

    def translate_points(self, x, y):
        self._track.P[self._track.selected, 2] += y
