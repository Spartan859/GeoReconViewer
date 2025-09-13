from PySide6 import QtWidgets
from PySide6.QtWebEngineWidgets import QWebEngineView


class DevToolsWindow(QtWidgets.QMainWindow):
    def __init__(self, inspected_page, parent=None):
        super().__init__(parent)
        self.setWindowTitle('DevTools')
        self.resize(900, 600)
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        if inspected_page is not None:
            # If the inspected page is provided, set it
            try:
                self.view.page().setInspectedPage(inspected_page)
            except Exception:
                # fallback: try using devToolsPage
                try:
                    dev = inspected_page.devToolsPage()
                    if dev is not None:
                        self.view.setPage(dev)
                except Exception:
                    pass
