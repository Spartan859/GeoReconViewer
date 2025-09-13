import pdb
import sys
import os
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

import logging

# local components
from viewer_3d import ModelViewer
from obj_loader import ObjLoader
from devtools import DevToolsWindow

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')



# Optional 3D view dependencies (pyqtgraph)
try:
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    import numpy as np
    HAS_3D = True
except Exception as e:
    print("3D view dependencies not found:", e)
    HAS_3D = False


class MapBridge(QtCore.QObject):
    """Bridge between Python and the web map (JS)."""

    jsToPy = QtCore.Signal(float, float)

    @QtCore.Slot(float, float)
    def fromJs_click(self, lat, lon):
        print(f"Map clicked at: {lat}, {lon}")
        self.jsToPy.emit(lat, lon)

    @QtCore.Slot(float, float)
    def highlight(self, lat, lon):
        # called from Python to ask JS to highlight a point
        # kept for completeness; actual highlighting will be done by calling JS function from Python
        print(f"Request to highlight at {lat},{lon}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoReconViewer - Demo")
        self._setup_ui()
        self._setup_menus()
        self._setup_map()
        self._setup_webchannel()

    def _setup_ui(self):
        # Single central viewer (ModelViewer)
        self.viewer = ModelViewer(parent=self)
        self.setCentralWidget(self.viewer)

    def _setup_menus(self):
        menubar = self.menuBar()
        self._file_menu = menubar.addMenu('File')
        self._view_menu = menubar.addMenu('View')
        self._debug_menu = menubar.addMenu('Debug')

        self._obj_loader = ObjLoader()
        load_action = QAction('Load .obj', self)
        load_action.triggered.connect(self._on_load_obj)
        self._file_menu.addAction(load_action)

        # add highlight action to the debug menu (rename of previous '测试')
        hl_action = QAction('Highlight sample on map', self)
        hl_action.triggered.connect(self._do_highlight)
        self._debug_menu.addAction(hl_action)

        # add Map action in View menu (click to show if hidden)
        self._map_action = QAction('Map', self)
        # not checkable: clicking shows the map if it's not already visible
        self._map_action.triggered.connect(self._toggle_map_window)
        self._view_menu.addAction(self._map_action)

    def _setup_map(self):
        # create web view and load local map
        self._web = QWebEngineView()
        try:
            s = self._web.settings()
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        except Exception:
            pass
        assets = Path(__file__).resolve().parent / "assets"
        map_html = assets / "map.html"
        self._web.load(QtCore.QUrl.fromLocalFile(str(map_html)))

        # Put the web view into its own top-level window so it runs separately
        try:
            self._web_window = QtWidgets.QMainWindow()
            self._web_window.setWindowTitle('Map')
            # create a 'Debug' menu for the map window and add the devtools action there
            try:
                menu_bar = self._web_window.menuBar()
                map_debug_menu = menu_bar.addMenu('Debug')
                self._devtools_action = QAction('Toggle DevTools', self)
                self._devtools_action.triggered.connect(self._toggle_devtools)
                map_debug_menu.addAction(self._devtools_action)
            except Exception:
                # fallback: already present in main window
                pass
            container = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._web)
            self._web_window.setCentralWidget(container)
            self._web_window.resize(900, 600)
            self._web_window.show()
        except Exception:
            # fallback: attach web view as a dock widget to main window
            try:
                dock = QtWidgets.QDockWidget('Map', self)
                dock.setWidget(self._web)
                self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
                self._web_dock = dock
            except Exception:
                pass

    # no inline test button; highlight action is in the '测试' menu

    def _setup_webchannel(self):
        # keep a reference to the channel so we can clean it up on close
        self._web_channel = QWebChannel()
        self._bridge = MapBridge()
        self._web_channel.registerObject("pyBridge", self._bridge)
        self._web.page().setWebChannel(self._web_channel)
        self._bridge.jsToPy.connect(self._on_map_clicked)

    def _on_load_obj(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open OBJ', str(Path.cwd()), 'OBJ Files (*.obj)')
        if not path:
            return
        verts, faces = self._obj_loader.load(path)
        try:
            self.viewer.set_mesh(verts, faces)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Load error', str(e))

    def _toggle_devtools(self):
        if getattr(self, '_devtools', None) and not self._devtools.isHidden():
            self._devtools.close()
            self._devtools = None
            return
        self._devtools = DevToolsWindow(self._web.page(), parent=self._web_window)
        self._devtools.show()

    def _do_highlight(self):
        lat, lon = 31.109995, 121.066074
        js = f"jsHighlight({lat}, {lon});"
        self._web.page().runJavaScript(js)
    
    def _toggle_map_window(self, checked=None):
        # When invoked: if the map window/dock is already visible, do nothing.
        # Otherwise show (or create then show) the map window/dock.
        try:
            # prefer the separate window
            if getattr(self, '_web_window', None):
                try:
                    if not self._web_window.isVisible():
                        self._web_window.show()
                except Exception:
                    pass
                return

            # fallback to dock widget
            if getattr(self, '_web_dock', None):
                try:
                    if not self._web_dock.isVisible():
                        self._web_dock.show()
                except Exception:
                    pass
                return

            # if web exists but no window/dock (edge case), create a new window and show it
            if getattr(self, '_web', None):
                try:
                    self._web_window = QtWidgets.QMainWindow()
                    self._web_window.setWindowTitle('Map')
                    try:
                        menu_bar = self._web_window.menuBar()
                        map_debug_menu = menu_bar.addMenu('Debug')
                        map_debug_menu.addAction(self._devtools_action)
                    except Exception:
                        pass
                    container = QtWidgets.QWidget()
                    layout = QtWidgets.QVBoxLayout(container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(self._web)
                    self._web_window.setCentralWidget(container)
                    self._web_window.resize(900, 600)
                    self._web_window.show()
                except Exception:
                    pass
        except Exception:
            pass

    def _on_map_clicked(self, lat, lon):
        msg = f"Map clicked: lat={lat:.6f}, lon={lon:.6f}"
        print(msg)
        logging.info(msg)

    def closeEvent(self, event):
        """
        Gracefully shut down QWebEngineView and its child processes.
        """
        logging.info("Main window close event triggered. Cleaning up web engine.")

        # 1. Clean up the DevTools window if it exists.
        if hasattr(self, '_devtools') and self._devtools:
            self._devtools.close()
            self._devtools = None

        # 2. Clean up the WebEngine components. This is the crucial part.
        if hasattr(self, '_web') and self._web:
            try:
                # Disconnect the web channel to sever the Python/JS link.
                try:
                    self._web.page().setWebChannel(None)
                except Exception:
                    pass

                # If the web view was placed in its own window, close and delete that window
                if hasattr(self, '_web_window') and self._web_window:
                    try:
                        self._web_window.close()
                    except Exception:
                        pass
                    try:
                        self._web_window.deleteLater()
                    except Exception:
                        pass
                    self._web_window = None

                # Schedule the web view for deletion
                try:
                    self._web.deleteLater()
                except Exception:
                    pass
            finally:
                self._web = None

        # 3. Accept the event and allow the parent class to perform its default actions,
        # which will lead to a clean application exit.
        super().closeEvent(event)


def make_window():
    app = QtWidgets.QApplication(sys.argv)
    # QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)
    win = MainWindow()
    return app, win


if __name__ == "__main__":
    app, win = make_window()
    win.show()
    sys.exit(app.exec())
