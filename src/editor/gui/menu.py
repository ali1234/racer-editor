import functools
from PySide6 import QtCore, QtGui


class MenuController(QtCore.QObject):
    exception = QtCore.Signal(Exception)

    def run_with_feedback(self, func):
        try:
            func()
        except Exception as e:
            self.exception.emit(e)

    def build_menu(self, parent_menu, menu_defs):
        for name, func, shortcut in menu_defs:
            if name is None:
                parent_menu.addSeparator()
            elif isinstance(func, list):
                m = parent_menu.addMenu(name)
                self.build_menu(m, func)
            elif isinstance(func, QtGui.QAction):
                if shortcut:
                    func.setShortcut(shortcut)
                parent_menu.addAction(func)
            else:
                action = QtGui.QAction(name, self)
                if shortcut:
                    action.setShortcut(shortcut)
                if callable(func):
                    action.triggered.connect(functools.partial(self.run_with_feedback, func))
                elif func is not None:
                    raise ValueError(f'Menu item {name}: {func} is not callable.')
                parent_menu.addAction(action)
