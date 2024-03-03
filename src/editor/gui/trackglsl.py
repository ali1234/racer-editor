import numpy as np
import OpenGL.GL as gl
from PySide6 import QtCore

from ..core.track import Track
from .shaders import ShaderProgram, Buffer


class TrackGLSL(Track, QtCore.QObject):
    visualChanged = QtCore.Signal()
    dataChanged = QtCore.Signal()
    selectionChanged = QtCore.Signal()

    def __init__(self, data=None):
        QtCore.QObject.__init__(self)
        self._opt_timer = QtCore.QTimer()
        self._opt_timer.setInterval(50)
        self._opt_timer.timeout.connect(self._opt_step)
        Track.__init__(self, data)
        self._widgets = []

    def _opt_step(self):
        self.optimize(max_opt_its=10)
        if hasattr(self, '_trackdata_vbo'):
            self._trackdata_vbo.data = self._data
            self._distances_vbo.data = self._distances
        self.visualChanged.emit()
        self._opt_counter += 1
        if self._opt_counter > 20:
            self._opt_timer.stop()

    def start_optimizing(self):
        self._opt_counter = 0
        if not self._opt_timer.isActive():
            self._opt_timer.start()

    def data_modified(self):
        self.construct(keep=True)
        self.visualChanged.emit()
        self.start_optimizing()
        self.dataChanged.emit()

    def data_set(self):
        if hasattr(self, '_trackdata_vbo'):
            self._trackdata_vbo.data = self._data
            self._distances_vbo.data = self._distances
            self._selection_vbo.data = self._selection
        self.visualChanged.emit()
        self.selectionChanged.emit()
        self.start_optimizing()

    def data_moved(self):
        self.data_set()
        self.dataChanged.emit()

    def select(self, selection, multi=False):
        super().select(selection, multi)
        self._selection_vbo.data = self._selection
        self.selectionChanged.emit()

    def init_shaders(self):
        self._handle_prog = ShaderProgram('handle.vert', 'handle.frag')
        self._curve_prog = ShaderProgram('curve.vert', 'curve.frag')

        self._trackdata_vbo = Buffer(self._data)
        self._distances_vbo = Buffer(self._distances)
        self._selection_vbo = Buffer(self._selection)

    def add_to_widget(self, widget):
        if not self._widgets:
            self._widgets.append(widget)
            self.init_shaders()
        elif widget.context().areSharing(self._widgets[0].context(), widget.context()):
            self._widgets.append(widget)
        else:
            raise ValueError("Cannot add to widget because it is not context sharing.")

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glEnable(gl.GL_POINT_SPRITE)
        gl.glPointSize(5)

    def draw(self, mvp, interp=20, mode=0):
        self._curve_prog.bind()
        self._curve_prog.setAttribute('p', self._trackdata_vbo, gl.GL_FLOAT, 3, offset=0,  stride=48, divisor=interp)
        self._curve_prog.setAttribute('m', self._trackdata_vbo, gl.GL_FLOAT, 3, offset=12,  stride=48, divisor=interp)
        self._curve_prog.setAttribute('a', self._trackdata_vbo, gl.GL_FLOAT, 3, offset=24,  stride=48, divisor=interp)
        self._curve_prog.setAttribute('b', self._trackdata_vbo, gl.GL_FLOAT, 3, offset=36, stride=48, divisor=interp)
        self._curve_prog.setAttribute('distance', self._distances_vbo, gl.GL_FLOAT, 2, divisor=interp)
        self._curve_prog.setAttribute('selected', self._selection_vbo, gl.GL_INT,1, divisor=interp)
        self._curve_prog.setAttribute('next_selected', self._selection_vbo, gl.GL_INT,1, offset=4, divisor=interp)
        self._curve_prog.setUniform('unselected_colour', 'green')
        self._curve_prog.setUniform('selected_colour', 'red')
        self._curve_prog.setUniform('matrix', mvp)
        self._curve_prog.setUniform1i('interp', interp//2)
        self._curve_prog.setUniform1i('mode', 1 + mode)
        gl.glLineWidth(1)
        gl.glDrawArraysInstanced(gl.GL_LINES, 0, interp, self._data.shape[0] * interp)
        self._curve_prog.setUniform1i('mode', 3 + mode)
        gl.glDrawArraysInstanced(gl.GL_LINES, 0, interp, self._data.shape[0] * interp)

        self._curve_prog.setUniform('matrix', mvp)
        self._curve_prog.setUniform1i('interp', interp)
        self._curve_prog.setUniform1i('mode', 2 + mode)
        gl.glDrawArraysInstanced(gl.GL_LINE_STRIP, 0, interp, self._data.shape[0] * interp)

        self._curve_prog.setUniform('unselected_colour', 'dimgrey')
        self._curve_prog.setUniform('selected_colour', 'orange')
        self._curve_prog.setUniform1i('mode', 0 + mode)
        gl.glLineWidth(3)
        gl.glDrawArraysInstanced(gl.GL_LINE_STRIP, 0, interp, self._data.shape[0] * interp)

        self._handle_prog.bind()
        self._handle_prog.setAttribute('position', self._trackdata_vbo, gl.GL_FLOAT, 3, stride=48)
        self._handle_prog.setAttribute('distance', self._distances_vbo, gl.GL_FLOAT, 1, stride=8)
        self._handle_prog.setAttribute('selected', self._selection_vbo, gl.GL_INT, 1)
        self._handle_prog.setUniform('unselected_colour', 'black')
        self._handle_prog.setUniform('selected_colour', 'yellow')
        self._handle_prog.setUniform('matrix', mvp)
        self._handle_prog.setUniform1i('mode', mode)
        gl.glDrawArrays(gl.GL_POINTS, 0, self._data.shape[0])
        self._handle_prog.release()
