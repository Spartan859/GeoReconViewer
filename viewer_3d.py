import sys
from pathlib import Path

try:
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    import numpy as np
    HAS_3D = True
except Exception as e:
    HAS_3D = False

from PySide6 import QtCore, QtWidgets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# custom interactive GL view with right-button drag
class InteractiveGLView(gl.GLViewWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_pos = None

    def mousePressEvent(self, ev):
        # store last pos on right-button press
        if ev.buttons() == QtCore.Qt.RightButton:
            self._last_pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if ev.buttons() == QtCore.Qt.RightButton and self._last_pos is not None:
            cur = ev.position() if hasattr(ev, 'position') else ev.pos()
            dx = cur.x() - self._last_pos.x()
            dy = cur.y() - self._last_pos.y()
            # perform pan: map pixel delta to world translation using distance-based scale
            try:
                dist = float(self.opts.get('distance', 40))
            except Exception:
                dist = 40.0
            # map pixel delta to world translation based on camera orientation
            factor = dist * 0.002
            move_x = -dx * factor
            move_y = dy * factor
            try:
                # compute current center
                c = self.opts.get('center', (0, 0, 0))
                try:
                    center = np.array([c.x(), c.y(), c.z()], dtype=float)
                except Exception:
                    center = np.array(tuple(c), dtype=float)

                # camera angles (degrees -> radians)
                az = np.deg2rad(self.opts.get('azimuth', 0.0))
                el = np.deg2rad(self.opts.get('elevation', 0.0))

                # approximate camera position in world coords (spherical around center)
                camx = center[0] + dist * np.cos(el) * np.cos(az)
                camy = center[1] + dist * np.cos(el) * np.sin(az)
                camz = center[2] + dist * np.sin(el)
                cam = np.array([camx, camy, camz], dtype=float)

                # forward vector (from camera to center)
                forward = center - cam
                fnorm = np.linalg.norm(forward)
                if fnorm == 0:
                    forward = np.array([0, 0, 1], dtype=float)
                else:
                    forward = forward / fnorm

                world_up = np.array([0.0, 0.0, 1.0], dtype=float)
                right = np.cross(forward, world_up)
                rnorm = np.linalg.norm(right)
                if rnorm == 0:
                    right = np.array([1.0, 0.0, 0.0], dtype=float)
                else:
                    right = right / rnorm

                up_cam = np.cross(right, forward)
                unorm = np.linalg.norm(up_cam)
                if unorm == 0:
                    up_cam = np.array([0.0, 0.0, 1.0], dtype=float)
                else:
                    up_cam = up_cam / unorm

                translation = right * move_x + up_cam * move_y

                new_center = center + translation
                try:
                    self.opts['center'] = pg.Vector(new_center[0], new_center[1], new_center[2])
                except Exception:
                    self.opts['center'] = tuple(new_center.tolist())
                # trigger redraw
                try:
                    self.update()
                except Exception:
                    pass
            except Exception:
                # fallback to simple pan
                try:
                    self.pan(move_x, move_y, 0)
                except Exception:
                    pass
            self._last_pos = cur
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self._last_pos = None
        super().mouseReleaseEvent(ev)

class ModelViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('3D Model Viewer - Minimal')
        layout = QtWidgets.QVBoxLayout(self)

        if HAS_3D:
            try:
                self.glw = InteractiveGLView()
                self.glw.opts['distance'] = 40
                # visible container
                container = QtWidgets.QFrame()
                container.setFrameShape(QtWidgets.QFrame.Box)
                container.setMinimumSize(400, 400)
                cont_layout = QtWidgets.QVBoxLayout(container)
                cont_layout.addWidget(self.glw)
                layout.addWidget(container)

                # add grid and origin marker
                try:
                    grid = gl.GLGridItem()
                    grid.scale(2, 2, 1)
                    self.glw.addItem(grid)
                except Exception:
                    pass
                try:
                    origin = np.array([[0.0, 0.0, 0.0]])
                    scatter = gl.GLScatterPlotItem(pos=origin, size=10, color=(1.0, 0.0, 0.0, 1.0))
                    self.glw.addItem(scatter)
                except Exception:
                    pass
            except Exception as e:
                layout.addWidget(QtWidgets.QLabel('Failed to create GL view: ' + str(e)))
                self.glw = None
        else:
            layout.addWidget(QtWidgets.QLabel('pyqtgraph/OpenGL not available - 3D disabled'))
            self.glw = None

    def set_mesh(self, vertices, faces):
        """Set mesh directly from arrays/lists of vertices and faces.
        vertices: Nx3 array-like, faces: Mx3 array-like (0-based indices)
        """
        if not HAS_3D or self.glw is None:
            raise RuntimeError('3D view not available')
        v = np.array(vertices)
        f = np.array(faces)
        if v.size == 0 or f.size == 0:
            raise ValueError('Empty vertices or faces')

        # center and normalize similar to load_obj
        minv = v.min(axis=0)
        maxv = v.max(axis=0)
        center = (minv + maxv) / 2.0
        scale = (maxv - minv).max()
        if scale == 0:
            scale = 1.0
        v2 = (v - center) / scale * 10.0

        # remove previous items
        try:
            for item in list(self.glw.items):
                try:
                    self.glw.removeItem(item)
                except Exception:
                    pass
        except Exception:
            pass

        meshdata = gl.MeshData(vertexes=v2, faces=f)
        mesh_item = gl.GLMeshItem(meshdata=meshdata, smooth=False, drawFaces=True, drawEdges=True, edgeColor=(0,0,0,1))
        self.glw.addItem(mesh_item)
        try:
            self.glw.opts['center'] = pg.Vector(0,0,0)
            self.glw.setCameraPosition(distance=40)
        except Exception:
            try:
                self.glw.setCameraPosition(distance=40)
            except Exception:
                pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = ModelViewer()
    w.show()
    sys.exit(app.exec())
