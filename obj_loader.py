from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ObjLoader:
    """Minimal OBJ loader that returns vertices and triangular faces as numpy arrays.

    Usage:
        verts, faces = ObjLoader().load(path)
    """
    def load(self, path):
        path = Path(path)
        verts = []
        faces = []
        with path.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    parts = line.strip().split()[1:]
                    face = [int(p.split('/')[0]) - 1 for p in parts if p]
                    if len(face) >= 3:
                        for i in range(1, len(face)-1):
                            faces.append([face[0], face[i], face[i+1]])

        if len(verts) == 0 or len(faces) == 0:
            logger.warning('OBJ %s contains no geometry (verts=%d, faces=%d)', path, len(verts), len(faces))
        return np.array(verts), np.array(faces)
