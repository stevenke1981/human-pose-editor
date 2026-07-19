"""
threejs_viewer.py — QWebEngineView wrapper for embedded Three.js 3D viewer.

Provides a PySide6 widget with an embedded Three.js scene, QWebChannel bridge,
and a Python API for loading models, setting poses, generating props, and more.

NOTE: The viewer is served via a local HTTP server (not file://) so that
Three.js ES modules (importmap) work correctly in Qt WebEngine / Chromium.
"""
import os
import json
import threading
import http.server
import socket
from typing import Optional, Callable

from PySide6.QtCore import QObject, Slot, Signal, QUrl, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from prop_generator import generate_prop_code, generate_json_spec


# ======================================================================
#  Local HTTP Server (singleton) — serves threejs/viewer.html with
#  correct MIME types so ES modules + importmap work in QWebEngineView.
# ======================================================================

_local_server = None
_local_server_port = None
_local_server_thread = None


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that suppresses console log output."""
    def log_message(self, fmt, *args):
        pass


def _start_local_server():
    """Start a daemon-threaded HTTP server at a random port, serving the
    project root directory so that ``threejs/viewer.html`` is reachable.
    Safe to call multiple times — only starts once."""
    global _local_server, _local_server_port, _local_server_thread
    if _local_server is not None:
        return

    # Find a free TCP port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        _local_server_port = s.getsockname()[1]

    # Serve from the project root directory (where threejs/ lives)
    project_root = os.path.dirname(os.path.abspath(__file__))

    server = http.server.HTTPServer(
        ('127.0.0.1', _local_server_port),
        lambda *a, **kw: _QuietHandler(*a, directory=project_root, **kw),
    )
    server.timeout = 0.5  # allow clean shutdown

    _local_server = server

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _local_server_thread = thread


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

    @Slot()
    def on_sculpt_pipeline_requested(self):
        """Called by JS when the user clicks 'Sculpt Pipeline' in the 3D toolbar."""
        if self._viewer:
            self._viewer.run_sculpt_pipeline()


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

        # Ensure the local HTTP server is running (for ES module support)
        _start_local_server()

        # Locate the HTML template — use relative path for HTTP server
        if html_path is None:
            html_path = "threejs/viewer.html"
        # Strip absolute prefix if caller passed a full path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if html_path.startswith(project_root):
            html_path = os.path.relpath(html_path, project_root)

        self._html_path = html_path
        self._ready = False

        # Load via HTTP (not file://) so ES modules + importmap work
        viewer_url = f"http://127.0.0.1:{_local_server_port}/{html_path.replace(os.sep, '/')}"
        self.load(QUrl(viewer_url))
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
        if ok:
            print(f"[ThreeJSViewer] Loaded: {self.url().toString()}")
        else:
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

    # ------------------------------------------------------------------
    #  Sculpt Pipeline (full integration)
    # ------------------------------------------------------------------

    def run_sculpt_pipeline(self, image_path: Optional[str] = None):
        """Run the full Three.js Object Sculptor pipeline from image to scene.

        Args:
            image_path: Optional path; if None, opens a file dialog.
        """
        if image_path is None:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self._parent_window or self,
                "Select Reference Image for Sculpt Pipeline",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
            )
            if not path:
                return
            image_path = path

        from PySide6.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(
            self._parent_window or self,
            "Sculpt Pipeline — Object Name",
            "Name of the object to generate:",
            text=os.path.splitext(os.path.basename(image_path))[0]
        )
        if not ok or not name.strip():
            name = "SculptedObject"

        # Complexity selection
        complexities = ["moderate", "simple", "complex", "ultra"]
        complexity, ok = QInputDialog.getItem(
            self._parent_window or self,
            "Sculpt Pipeline — Complexity",
            "Complexity tier:",
            complexities, 0, False
        )
        if not ok:
            complexity = "moderate"

        self.set_status(f"🔧 Sculpt pipeline: probing image...")

        # Import and run pipeline
        from sculpt_pipeline import run_pipeline

        # Run in a way that doesn't block UI — but since QWebEngineView
        # is async anyway, we just run synchronously with status updates
        try:
            result = run_pipeline(
                image_path=image_path,
                target_name=name,
                complexity=complexity,
            )

            if not result.success:
                self.set_status(f"❌ Pipeline failed: {result.error}")
                QMessageBox.critical(
                    self._parent_window or self,
                    "Sculpt Pipeline Error",
                    f"Pipeline failed:\n{result.error}"
                )
                return

            if result.js_code:
                self.set_status(f"✅ Pipeline complete! Loading {name} into scene...")
                escaped = json.dumps(result.js_code)
                self._call_js(f"window.__threejs_bridge.addPropFromCode({escaped});")
                self.set_status(f"✅ {name} loaded from sculpt pipeline")

                # Show summary
                probe = result.probe_result or {}
                val = result.validation or {}
                summary = (
                    f"✅ Sculpt Pipeline Complete\n\n"
                    f"Object: {name}\n"
                    f"Image: {os.path.basename(image_path)}\n"
                    f"Probe: {probe.get('width', '?')}x{probe.get('height', '?')}\n"
                    f"Validation: {len(val.get('errors', []))} errors, "
                    f"{len(val.get('warnings', []))} warnings\n"
                    f"Spec: {os.path.basename(result.spec_path or '')}\n"
                    f"Generated: {os.path.basename(result.ts_path or '')}"
                )
                QMessageBox.information(
                    self._parent_window or self,
                    "Sculpt Pipeline Complete",
                    summary
                )
            else:
                self.set_status("⚠️ Pipeline completed but no JS code generated")

        except Exception as e:
            self.set_status(f"❌ Pipeline error: {e}")
            QMessageBox.critical(
                self._parent_window or self,
                "Sculpt Pipeline Error",
                f"Unexpected error:\n{e}"
            )
