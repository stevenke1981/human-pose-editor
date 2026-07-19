"""
threejs_viewer.py — QWebEngineView wrapper for embedded Three.js 3D viewer.

Provides a PySide6 widget with an embedded Three.js scene, QWebChannel bridge,
and a Python API for loading models, setting poses, generating props, and more.
"""
import os
import json
from typing import Optional, Callable

from PySide6.QtCore import QObject, Slot, Signal, QUrl, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from prop_generator import generate_prop_code, generate_json_spec


# ======================================================================
#  Bridge Object — exposed to JavaScript via QWebChannel
# ======================================================================

class ThreeJSBridge(QObject):
    """Python-side object callable from JavaScript via QWebChannel."""

    # Signals emitted when JS calls certain bridge methods
    scene_ready = Signal()
    pose_updated = Signal(str)      # JSON pose data from JS
    model_loaded = Signal(str)       # status message
    error_occurred = Signal(str)     # error message
    prop_generation_requested = Signal()  # JS clicked "Generate Prop"

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

    @Slot()
    def on_generate_prop(self):
        """Called by JS when the user clicks 'Generate Prop' in the 3D toolbar."""
        self.prop_generation_requested.emit()


# ======================================================================
#  ThreeJSViewer Widget
# ======================================================================

class ThreeJSViewer(QWebEngineView):
    """Embedded Three.js 3D viewer widget with Python ↔ JS bridge."""

    def __init__(self, parent=None, html_path: Optional[str] = None,
                 on_generate_prop: Optional[Callable] = None):
        super().__init__(parent)
        self._bridge = ThreeJSBridge(self)
        self._bridge.set_viewer(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(self._channel)

        # Store external callback for prop generation
        self._on_generate_prop_callback = on_generate_prop

        # Locate the HTML template
        if html_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(base, "threejs", "viewer.html")

        self._html_path = html_path
        self._ready = False

        # Load the page
        self.load(QUrl.fromLocalFile(self._html_path))
        self.loadFinished.connect(self._on_load_finished)

        # Connect bridge signals
        self._bridge.scene_ready.connect(self._on_scene_ready)
        self._bridge.prop_generation_requested.connect(self._on_prop_requested)

        # Dark background for loading state
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)

        # Track parent window for dialogs
        self._parent_window = parent

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def _on_load_finished(self, ok: bool):
        if not ok:
            print(f"[ThreeJSViewer] Failed to load: {self._html_path}")

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

    def set_pose(self, points: list):
        """Send OpenPose keypoints to the 3D mannequin.

        Args:
            points: list of 18 [x, y] or [x, y, confidence] tuples
                    in the app's 512x512 canvas coordinate space.
        """
        payload = {"points": points}
        json_str = json.dumps(payload)
        self._call_js(f"window.__threejs_bridge.setPose({json.dumps(json_str)});")

    def set_status(self, msg: str):
        """Set the status bar text in the 3D viewer."""
        escaped = json.dumps(msg)
        self._call_js(f"window.__threejs_bridge.setStatus({escaped});")

    def screenshot(self) -> Optional[bytes]:
        """Capture the current 3D view as a PNG image.

        Returns:
            PNG bytes, or None if capture fails.
        """
        pixmap = self.grab()
        if pixmap and not pixmap.isNull():
            import io
            buf = io.BytesIO()
            pixmap.save(buf, "PNG")
            return buf.getvalue()
        return None

    # ------------------------------------------------------------------
    #  Prop Generation
    # ------------------------------------------------------------------

    def _on_prop_requested(self):
        """Internal handler when JS requests a prop generation."""
        if self._on_generate_prop_callback:
            self._on_generate_prop_callback()
        else:
            self.generate_prop_from_file()

    def generate_prop_from_file(self, image_path: Optional[str] = None):
        """Open a file dialog, analyze image, generate and load a 3D prop.

        Args:
            image_path: Optional path; if None, opens a file dialog.
        """
        if image_path is None:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self._parent_window or self,
                "Select Reference Image for 3D Prop",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
            )
            if not path:
                return
            image_path = path

        self.set_status(f"Analyzing {os.path.basename(image_path)}...")

        # Ask for prop name
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self._parent_window or self,
            "Prop Name",
            "Name for the 3D prop:",
            text=os.path.splitext(os.path.basename(image_path))[0]
        )
        if not ok or not name.strip():
            name = "GeneratedProp"
        name = name.strip().replace(" ", "_")

        # Generate the code
        self.set_status(f"Generating 3D model for {name}...")
        js_code = generate_prop_code(image_path, name)
        if js_code is None:
            self.set_status(f"Failed to generate prop from {os.path.basename(image_path)}")
            return

        # Send to JS
        escaped = json.dumps(js_code)
        self._call_js(f"window.__threejs_bridge.addPropFromCode({escaped});")
        self.set_status(f"Prop '{name}' loaded!")

    def load_model_code(self, code: str):
        """Load arbitrary Three.js factory JS code into the scene.

        Args:
            code: JavaScript code string with a factory function that returns a Group.
        """
        escaped = json.dumps(code)
        self._call_js(f"window.__threejs_bridge.loadModelCode({escaped});")

    def clear_props(self):
        """Remove all generated props from the scene."""
        self._call_js("window.__threejs_bridge.clearProps();")
