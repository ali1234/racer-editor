import functools

from PySide6 import QtCore, QtWidgets
from pyqtconsole.console import PythonConsole

from .opensave import OpenSaveController
from .menu import MenuController
from .trackglsl import TrackGLSL
from .view import View3D, View1D
from .preview import Preview


class TrackEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._track = TrackGLSL()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, self)
        view3d = View3D(self, self._track)
        view3d.setMinimumSize(640, 480)
        splitter.addWidget(view3d)
        view1d = View1D(self, self._track)
        view1d.setMinimumSize(640, 160)
        splitter.addWidget(view1d)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        preview = PreviewDock(self._track, self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, preview)
        stats = StatsDock(self._track, self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, stats)
        segment = SegmentDock(self._track, self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, segment)
        console = ConsoleDock({'track': self._track}, self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, console)
        console.hide()

        self.statusBar()

        self._menu = MenuController()
        self._menu.build_menu(self.menuBar(), [
            ('&File', [
                ('New...', self.new, 'Ctrl+N'),
                ('Open...', self.open, 'Ctrl+O'),
                (None, None, None),
                ('Save', self.save, 'Ctrl+S'),
                ('Save As...', self.saveas, 'Ctrl+Shift+S'),
                (None, None, None),
                ('Quit', self.quit, 'Ctrl+Q'),
            ], None),
            ('&Edit', [
                ('Undo', self._track.undo, 'Ctrl+Z'),
                ('Redo', self._track.redo, 'Ctrl+Shift+Z'),
            ], None),
            ('&View', [
                ('Preview', preview.toggleViewAction(), 'Ctrl+P'),
                ('Stats', stats.toggleViewAction(), None),
                ('Segment', segment.toggleViewAction(), None),
                ('Console', console.toggleViewAction(), 'Ctrl+D'),
                (None, None, None),
                ('Top View', view3d.reset_view_rotation, 'Ctrl+T'),
            ], None),
            ('&Select', [
                ('All', functools.partial(self._track.select, None), 'Ctrl+A'),
                ('None', functools.partial(self._track.select, slice(0, 0)), 'Ctrl+Shift+A'),
                ('Invert', functools.partial(self._track.select, None, multi=True), None),
            ], None),
            ('&Control Points', [
                ('Add After', self._track.add_after, None),
                ('Add Before', self._track.add_before, None),
                ('Delete', self._track.delete, None),
            ], None),
            ('S&egments', [
                ('Subdivide', self._track.subdivide, None),
                ('Dissolve', self._track.dissolve, None),
            ], None),
            ('&Help', [
                #('&Website', lambda x: webbrowser.open_new_tab('https://github.com/ali1234/vhs-teletext'), None),
                ('&About', None, None),
            ], None),
        ])
        self._menu.exception.connect(self._show_exception)

        self._opensave = OpenSaveController("track")
        self._track.dataChanged.connect(self._opensave.set_unsaved)
        self._opensave.changed.connect(self._set_window_title)
        self._set_window_title()

    def _show_exception(self, e):
        self.statusBar().showMessage(str(e), 2000)

    def _set_window_title(self):
        self.setWindowTitle(f'{self._opensave.filename}[*] - Track Editor')
        self.setWindowModified(self._opensave.unsaved)

    def new(self):
        if self._opensave.new():
            self._track.set_data(None)

    def open(self):
        filepath = self._opensave.open()
        if filepath:
            self._track.deserialize(filepath.read_text())

    def save(self):
        filepath = self._opensave.save()
        if filepath:
            filepath.write_text(self._track.serialize())
        return filepath

    def saveas(self):
        filepath = self._opensave.saveas()
        if filepath:
            filepath.write_text(self._track.serialize())
        return filepath

    def quit(self):
        if self._opensave.warning():
            self.close()


class PreviewDock(QtWidgets.QDockWidget):

    def __init__(self, track, parent=None):
        super().__init__("Preview", parent)
        self._preview = Preview(track)
        self._preview.setScaledContents(True)
        self._preview.setFixedSize(320, 240)
        self.setWidget(self._preview)
        self.topLevelChanged.connect(self.update_size)
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.update_time)
        self._timer.start(1000 // 30)

    def update_size(self):
        if self.isFloating():
            if self.topLevelWidget() is self:
                self._preview.setFixedSize(640, 480)
        else:
            self._preview.setFixedSize(320, 240)

    def update_time(self):
        self._preview.move(100)
        if self.isVisible():
            self._preview.redraw()


class StatsDock(QtWidgets.QDockWidget):
    def __init__(self, track, parent=None):
        super().__init__("Stats", parent)
        self.form = QtWidgets.QFormLayout()
        self._rows = {}
        self.add_row('Control points:')
        self.add_row('Total length:')
        widget = QtWidgets.QWidget()
        widget.setLayout(self.form)
        self.setWidget(widget)
        self.track = track
        self.track.visualChanged.connect(self.update)
        self.update()

    def add_row(self, title):
        self._rows[title] = QtWidgets.QLabel()
        self.form.addRow(title, self._rows[title])

    def set_row(self, title, value):
        self._rows[title].setText(str(value))

    def update(self):
        self.set_row('Control points:', self.track.P.shape[0])
        self.set_row('Total length:', f'{round(self.track.total_length/1000, 2)}km')


class SegmentDock(QtWidgets.QDockWidget):
    def __init__(self, track, parent=None):
        super().__init__('Segment', parent)
        self.form = QtWidgets.QFormLayout()
        self._rows = {}
        self.add_row('Selected:', QtWidgets.QLabel())
        self.style = QtWidgets.QSpinBox()
        self.style.valueChanged.connect(self.update_style)
        self.add_row('Style:', self.style)
        widget = QtWidgets.QWidget()
        widget.setLayout(self.form)
        self.setWidget(widget)
        self.track = track
        self.track.selectionChanged.connect(self.update)
        self.update()

    def add_row(self, title, widget):
        self._rows[title] = widget
        self.form.addRow(title, self._rows[title])

    def set_row(self, title, value):
        self._rows[title].setText(str(value))

    def update_style(self):
        if len(self.track.selected) == 1:
            self.track.S[self.track.selected[0]] = self.style.value()

    def update(self):
        if len(self.track.selected) == 1:
            self.set_row('Selected:', str(self.track.selected[0]))
            self.style.setValue(self.track.S[self.track.selected[0]])
            self.style.show()
        else:
            self.set_row('Selected:', str(self.track.selected))
            self.style.hide()


class ConsoleDock(QtWidgets.QDockWidget):
    def __init__(self, locals, parent=None):
        super().__init__("Debug Console", parent)
        console = PythonConsole(locals=locals)
        console.eval_queued()
        self.setWidget(console)


def run():
    import sys
    #QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    app = QtWidgets.QApplication(sys.argv)
    view = TrackEditor()
    view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run()
