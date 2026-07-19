"""
threejs_viewer.py — QWebEngineView wrapper for embedded Three.js 3D viewer.

Provides a PySide6 widget with an embedded Three.js scene, QWebChannel bridge,
and a Python API for loading models, setting poses, and communicating with JS.
"""
import os
import json
from typing import Optional, Callable

from PySide6.QtCore import QObject, Slot, Signal, QUrl, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


# ======================================================================
#  Bridge Object — exposed to JavaScript via QWebChannel
# ======================================================================

class ThreeJSBridge(QObject):
    """Python-side object callable from JavaScript via QWebChannel."""

    # Signals emitted when JS calls certain bridge methods
    scene_ready = Signal()
    pose_updated = Signal(str)  # JSON pose data
    model_loaded = Signal(str)  # status message
    error_occurred = Signal(str)  # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewer: Optional["ThreeJSViewer"] = None

    def set_viewer(self, viewer: "ThreeJSViewer"):
        self._viewer = viewer

    # --- Slots callable from JavaScript ---

    @Slot(str)
    def on_scene_ready(self, msg: str):
        """Called by JS when the Three.js scene is fully initialized."""
        self.scene_ready.emit()

    @Slot(str)
    def on_pose_update(self, json_str: str):
        """Called by JS when the user interacts with the 3D mannequin."""
        self.pose_updated.emit(json_str)

    @Slot(str)
    def on_model_loaded(self, status: str):
        """Called by JS when a model finishes loading."""
        self.model_loaded.emit(status)

    @Slot(str)
    def on_error(self, msg: str):
        """Called by JS when an error occurs in the Three.js scene."""
        self.error_occurred.emit(msg)


# ======================================================================
#  ThreeJSViewer Widget
# ======================================================================

class ThreeJSViewer(QWebEngineView):
    """Embedded Three.js 3D viewer widget with Python ↔ JS bridge."""

    def __init__(self, parent=None, html_path: Optional[str] = None):
        super().__init__(parent)
        self._bridge = ThreeJSBridge(self)
        self._bridge.set_viewer(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(self._channel)

        # Locate the HTML template
        if html_path is None:
            # Default: look next to this file in the threejs/ folder
            base = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(base, "threejs", "viewer.html")

        self._html_path = html_path
        self._ready = False

        # Load the page
        self.load(QUrl.fromLocalFile(self._html_path))
        self.loadFinished.connect(self._on_load_finished)

        # Connect bridge signals
        self._bridge.scene_ready.connect(self._on_scene_ready)

        # Dark background for loading state
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def _on_load_finished(self, ok: bool):
        if not ok:
            print(f"[ThreeJSViewer] Failed to load: {self._html_path}")
            return

    def _on_scene_ready(self):
        self._ready = True
        print("[ThreeJSViewer] Scene ready")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def wait_ready(self, timeout_ms: int = 5000):
        """Simple blocking wait until the scene is ready (polling)."""
        import time
        start = time.time()
        while not self._ready and (time.time() - start) * 1000 < timeout_ms:
            time.sleep(0.1)

    # ------------------------------------------------------------------
    #  Python → JS Commands (via evaluateJavaScript)
    # ------------------------------------------------------------------

    def _call_js(self, code: str):
        """Execute JavaScript code in the Three.js page."""
        self.page().runJavaScript(code)

    def clear_scene(self):
        """Remove all objects from the 3D scene."""
        self._call_js("window.__threejs_bridge.clearScene();")

    def add_mesh(self, geometry: str, params: list = None,
                  color: int = 0x4488ff, position: list = None,
                  rotation: list = None, scale: list = None,
                  name: str = ""):
        """Add a primitive mesh to the scene.

        Args:
            geometry: 'box', 'sphere', 'cylinder', 'capsule'
            params: geometry dimensions e.g. [1,1,1] for box
            color: hex color
            position: [x, y, z]
            rotation: [x, y, z] in radians
            scale: [x, y, z]
            name: optional name for the mesh
        """
        data = {
            "geometry": {"type": geometry, "params": params or [1, 1, 1]},
            "material": {"color": color, "roughness": 0.4, "metalness": 0.1},
            "position": position or [0, 0, 0],
            "rotation": rotation or [0, 0, 0],
            "scale": scale or [1, 1, 1],
            "name": name,
        }
        self._call_js(f"window.__threejs_bridge.addMesh({json.dumps(json.dumps(data))});")

    def set_pose(self, pose_data: dict):
        """Send pose data (joint positions/angles) to the 3D mannequin.

        Args:
            pose_data: dict with joint data — format TBD in Phase 2
        """
        json_str = json.dumps(pose_data)
        self._call_js(f"window.__threejs_bridge.setPose({json.dumps(json_str)});")

    def load_model_code(self, code: str):
        """Load Three.js factory code into the scene (Phase 3).

        Args:
            code: JavaScript/TypeScript code string for a Three.js factory
        """
        escaped = json.dumps(code)
        self._call_js(f"window.__threejs_bridge.loadModelCode({escaped});")

    def set_status(self, msg: str):
        """Set the status bar text in the 3D viewer."""
        escaped = json.dumps(msg)
        self._call_js(f"window.__threejs_bridge.setStatus({escaped});")

    def screenshot(self) -> Optional[bytes]:
        """Capture the current 3D view as a PNG image.

        Returns:
            PNG bytes, or None if capture fails.
        """
        # QWebEngineView has a grab() method that captures the widget
        pixmap = self.grab()
        if pixmap and not pixmap.isNull():
            import io
            buf = io.BytesIO()
            pixmap.save(buf, "PNG")
            return buf.getvalue()
        return None

    # ------------------------------------------------------------------
    #  Convenience: Add a default mannequin placeholder
    # ------------------------------------------------------------------

    def add_default_mannequin(self):
        """Add a simple capsule-based mannequin for testing."""
        body = {
            "geometry": {"type": "capsule", "params": [0.3, 0.6, 8, 16]},
            "material": {"color": 0x6688cc, "roughness": 0.5, "metalness": 0.1},
            "position": [0, 0.6, 0],
            "name": "body"
        }
        self._call_js(f"window.__threejs_bridge.addMesh({json.dumps(json.dumps(body))});")

        head = {
            "geometry": {"type": "sphere", "params": [0.25, 24, 24]},
            "material": {"color": 0x88aadd, "roughness": 0.4},
            "position": [0, 1.25, 0],
            "name": "head"
        }
        self._call_js(f"window.__threejs_bridge.addMesh({json.dumps(json.dumps(head))});")
