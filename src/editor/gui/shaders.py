import pathlib
import numpy as np

from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader, QOpenGLBuffer
import OpenGL.GL as gl
import ctypes

SHADER_PATH = pathlib.Path(__file__).parent / 'shaders'


def shader_path(f):
    return str(SHADER_PATH / f)


class ShaderProgram(QOpenGLShaderProgram):

    def __init__(self, vert_prog, frag_prog, geom_prog=None):
        super().__init__()
        self.addShaderFromSourceFile(QOpenGLShader.ShaderTypeBit.Vertex, shader_path(vert_prog))
        self.addShaderFromSourceFile(QOpenGLShader.ShaderTypeBit.Fragment, shader_path(frag_prog))
        if geom_prog is not None:
            self.addShaderFromSourceFile(QOpenGLShader.ShaderTypeBit.Geometry, shader_path(geom_prog))
        self.link()

        # now introspect the variable names from the shaders
        self._loc = {}
        progid = self.programId()

        for i in range(gl.glGetProgramiv(progid, gl.GL_ACTIVE_ATTRIBUTES)):
            name, size, type_enum = gl.glGetActiveAttrib(progid, i)
            #print(name, size)
            loc = self.attributeLocation(name)
            self._loc[name.decode('utf8')] = loc

        for i in range(gl.glGetProgramiv(progid, gl.GL_ACTIVE_UNIFORMS)):
            name, size, type_enum = gl.glGetActiveUniform(progid, i)
            #print(name, size)
            loc = self.uniformLocation(name)
            self._loc[name.decode('utf8')] = loc

    def setUniform(self, name, value):
        loc = self._loc[name]
        self.setUniformValue(loc, value)

    def setUniform1f(self, name, value):
        loc = self._loc[name]
        self.setUniformValue1f(loc, value)

    def setUniform1i(self, name, value):
        loc = self._loc[name]
        self.setUniformValue1i(loc, value)

    def setAttribute(self, name, buffer, type, tupleSize, stride=None, offset=0, divisor=0):
        if stride is None:
            stride = tupleSize * 4
        loc = self._loc[name]
        buffer.bind()
        if type == gl.GL_INT:
            gl.glVertexAttribIPointer(loc, tupleSize, type, stride, ctypes.c_void_p(offset))
        else:
            self.setAttributeBuffer(loc, type, offset, tupleSize, stride)
        gl.glVertexAttribDivisor(loc, divisor)
        self.enableAttributeArray(loc)
        buffer.release()


class Buffer(QOpenGLBuffer):
    def __init__(self, data, alloc_size=4096):
        super().__init__(QOpenGLBuffer.Type.VertexBuffer)
        self._data = data
        self._modified = True
        self._grown = True
        self._buf_size = 0
        self._alloc_size = alloc_size
        self.create()
        self.bind()
        self.release()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, newdata: np.ndarray):
        if newdata is not self._data:
            if newdata.nbytes > self._buf_size:
                self._grown = True
            self._data = newdata
        self.modified()

    def modified(self):
        self._modified = True

    def bind(self):
        super().bind()
        if self._modified:
            if self._grown:
                self._buf_size = ((self._data.nbytes // self._alloc_size) + 1) * self._alloc_size
                self.allocate(self._buf_size)
                self._grown = False
            self.write(0, self._data, self._data.nbytes)
            self._modified = False
