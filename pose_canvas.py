"""
Interactive QWidget-based canvas for rendering and editing skeletons.
Handles mouse events, drag-and-drop transformations, reference background loading, and composition grid lines.
"""
from typing import List, Dict, Tuple, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QImage, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
import os

from pose_presets import POSE_CONNECTIONS, CONNECTION_COLORS, JOINT_COLORS
import pose_math
import i18n


class PoseCanvas(QWidget):
    # Signals
    char_selected = Signal(int)  # Emitted when a character is selected (clicked)
    pose_changed = Signal()      # Emitted when a pose is modified by dragging

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # State Variables
        self.canvas_width = 512
        self.canvas_height = 512
        self.skeletons: List[Dict] = []
        self.selected_char_idx = -1
        
        # Background Tracing Image State
        self.bg_image_path: str = ""
        self.bg_opacity: float = 0.5
        self.bg_pixmap: Optional[QPixmap] = None
        self.canvas_bg_color = "black"  # "black", "white", "transparent"

        # Composition Grid
        self.grid_type = "none"  # "none", "thirds", "golden"

        # Labels & Reference Coordinates
        self.labels_mode = "none"  # "none", "indices", "names"
        self.lang = "zh_TW"

        # Dragging State
        self.dragged_sk_idx = -1
        self.dragged_kp_idx = -1
        self.dragged_whole_char = False
        self.last_canvas_mouse_pos = (0.0, 0.0)

        # Coordinate Transform Cache (to map screen <-> virtual canvas)
        self.scale_factor = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def set_skeletons(self, skeletons: List[Dict]):
        self.skeletons = skeletons
        self.update()

    def set_canvas_size(self, width: int, height: int):
        self.canvas_width = width
        self.canvas_height = height
        self.update()

    def set_canvas_bg_color(self, bg_color: str):
        self.canvas_bg_color = bg_color
        self.update()

    def set_grid_type(self, grid_type: str):
        self.grid_type = grid_type
        self.update()

    def set_labels_mode(self, mode: str):
        self.labels_mode = mode
        self.update()

    def set_language(self, lang: str):
        self.lang = lang
        self.update()

    def set_background_image(self, image_path: str):
        self.bg_image_path = image_path
        if image_path and os.path.exists(image_path):
            self.bg_pixmap = QPixmap(image_path)
        else:
            self.bg_pixmap = None
        self.update()

    def set_background_opacity(self, opacity: float):
        self.bg_opacity = opacity
        self.update()

    def update_transforms(self):
        """Calculates scale and offset to fit virtual canvas centered inside QWidget."""
        ww, wh = self.width(), self.height()
        cw, ch = self.canvas_width, self.canvas_height
        
        # Calculate scale to fit inside widget with 5% margin
        margin = 0.95
        scale_x = (ww * margin) / cw
        scale_y = (wh * margin) / ch
        self.scale_factor = min(scale_x, scale_y)
        
        # Centers the virtual canvas
        self.offset_x = (ww - cw * self.scale_factor) / 2
        self.offset_y = (wh - ch * self.scale_factor) / 2

    def to_canvas_coords(self, sx: float, sy: float) -> Tuple[float, float]:
        """Converts screen coordinates to virtual canvas coordinates."""
        vx = (sx - self.offset_x) / self.scale_factor
        vy = (sy - self.offset_y) / self.scale_factor
        return vx, vy

    def to_screen_coords(self, vx: float, vy: float) -> Tuple[float, float]:
        """Converts virtual canvas coordinates to screen coordinates."""
        sx = self.offset_x + vx * self.scale_factor
        sy = self.offset_y + vy * self.scale_factor
        return sx, sy

    def paintEvent(self, event):
        self.update_transforms()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # 1. Fill Widget background with professional dark workspace color
        painter.fillRect(self.rect(), QColor(25, 26, 30))
        
        # Bounding box of virtual canvas
        canvas_rect = QRectF(
            self.offset_x,
            self.offset_y,
            self.canvas_width * self.scale_factor,
            self.canvas_height * self.scale_factor
        )
        
        # 2. Draw Virtual Canvas Base
        if self.canvas_bg_color == "black":
            painter.fillRect(canvas_rect, QColor(0, 0, 0))
        elif self.canvas_bg_color == "white":
            painter.fillRect(canvas_rect, QColor(255, 255, 255))
        elif self.canvas_bg_color == "transparent":
            # Draw checkers grid for transparent canvas representation
            self.draw_checkerboard(painter, canvas_rect)
            
        # Draw clean border around the virtual canvas
        border_pen = QPen(QColor(100, 100, 110, 150))
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        painter.drawRect(canvas_rect)

        # 3. Draw Background Tracing Image
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            painter.save()
            painter.setOpacity(self.bg_opacity)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(canvas_rect.toRect(), self.bg_pixmap)
            painter.restore()

        # 4. Draw Composition Grid Lines
        self.draw_composition_grid(painter, canvas_rect)

        # 4.5 Draw Canvas Reference Points (corners, center crosshairs)
        self.draw_canvas_reference_points(painter, canvas_rect)

        # 5. Draw Skeletons
        for idx, sk in enumerate(self.skeletons):
            if not sk.get("visible", True):
                continue
                
            is_selected = (idx == self.selected_char_idx)
            self.draw_skeleton(painter, sk["points"], is_selected, sk.get("locked", False))

        painter.end()

    def draw_checkerboard(self, painter: QPainter, rect: QRectF):
        """Draws a Photoshop-like checkerboard pattern for transparent canvases."""
        painter.fillRect(rect, QColor(240, 240, 240))
        cell_size = 12.0
        grid_color = QColor(200, 200, 200)
        
        painter.save()
        painter.setClipRect(rect)
        
        x = rect.left()
        while x < rect.right():
            y = rect.top()
            row_idx = int((x - rect.left()) / cell_size) % 2
            while y < rect.bottom():
                col_idx = int((y - rect.top()) / cell_size) % 2
                if (row_idx + col_idx) % 2 == 1:
                    painter.fillRect(QRectF(x, y, cell_size, cell_size), grid_color)
                y += cell_size
            x += cell_size
            
        painter.restore()

    def draw_composition_grid(self, painter: QPainter, rect: QRectF):
        """Renders composition guidelines inside the virtual canvas box."""
        if self.grid_type == "none":
            return
            
        pen = QPen(QColor(0, 180, 255, 120), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        rx, ry, rw, rh = rect.x(), rect.y(), rect.width(), rect.height()
        
        if self.grid_type == "thirds":
            # Vertical
            painter.drawLine(QPointF(rx + rw / 3, ry), QPointF(rx + rw / 3, ry + rh))
            painter.drawLine(QPointF(rx + rw * 2 / 3, ry), QPointF(rx + rw * 2 / 3, ry + rh))
            # Horizontal
            painter.drawLine(QPointF(rx, ry + rh / 3), QPointF(rx + rw, ry + rh / 3))
            painter.drawLine(QPointF(rx, ry + rh * 2 / 3), QPointF(rx + rw, ry + rh * 2 / 3))
            
        elif self.grid_type == "golden":
            # Golden ratio is approx 0.618
            gr = 0.61803398875
            # Vertical
            painter.drawLine(QPointF(rx + rw * (1 - gr), ry), QPointF(rx + rw * (1 - gr), ry + rh))
            painter.drawLine(QPointF(rx + rw * gr, ry), QPointF(rx + rw * gr, ry + rh))
            # Horizontal
            painter.drawLine(QPointF(rx, ry + rh * (1 - gr)), QPointF(rx + rw, ry + rh * (1 - gr)))
            painter.drawLine(QPointF(rx, ry + rh * gr), QPointF(rx + rw, ry + rh * gr))

    def draw_canvas_reference_points(self, painter: QPainter, rect: QRectF):
        """Draws pixel coordinates at the 4 corners of the canvas and center point."""
        if self.labels_mode == "none":
            return
            
        painter.save()
        font = QFont("Consolas", int(max(9, 11 * self.scale_factor)))
        painter.setFont(font)
        
        # Grid/crosshair color - subtle cyan with transparency
        grid_color = QColor(0, 229, 255, 90) if self.canvas_bg_color == "black" else QColor(0, 100, 200, 120)
        text_color = QColor(0, 229, 255) if self.canvas_bg_color == "black" else QColor(0, 100, 255)
        text_bg = QColor(0, 0, 0, 170) if self.canvas_bg_color != "white" else QColor(255, 255, 255, 200)
        
        # 1. Draw Center Crosshair
        cx = rect.x() + rect.width() / 2
        cy = rect.y() + rect.height() / 2
        pen = QPen(grid_color, 1.0, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(rect.x(), cy), QPointF(rect.x() + rect.width(), cy))
        painter.drawLine(QPointF(cx, rect.y()), QPointF(cx, rect.y() + rect.height()))
        
        # 2. Draw small reference circles at corners and center
        painter.setPen(QPen(text_color, 1.5))
        painter.setBrush(QBrush(QColor(0, 229, 255, 50)))
        corner_r = 4.0
        painter.drawEllipse(QPointF(rect.x(), rect.y()), corner_r, corner_r)
        painter.drawEllipse(QPointF(rect.x() + rect.width(), rect.y()), corner_r, corner_r)
        painter.drawEllipse(QPointF(rect.x(), rect.y() + rect.height()), corner_r, corner_r)
        painter.drawEllipse(QPointF(rect.x() + rect.width(), rect.y() + rect.height()), corner_r, corner_r)
        painter.drawEllipse(QPointF(cx, cy), corner_r * 1.5, corner_r * 1.5)
        
        # 3. Label Coordinates
        def draw_label(px, py, text, align):
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            
            # offsets based on alignment
            if "right" in align:
                offset_x = -tw - 8
            else:
                offset_x = 8
                
            if "bottom" in align:
                offset_y = -4
            else:
                offset_y = th + 2
                
            tx = px + offset_x
            ty = py + offset_y
            
            # Draw semi-transparent background rect for readability
            bg_rect = QRectF(tx - 3, ty - th + 2, tw + 6, th)
            painter.fillRect(bg_rect, text_bg)
            
            painter.setPen(QColor(255, 255, 255) if self.canvas_bg_color == "black" else QColor(0, 0, 0))
            painter.drawText(QPointF(tx, ty), text)

        # Draw 4 corners
        draw_label(rect.x(), rect.y(), "(0, 0)", "left_top")
        draw_label(rect.x() + rect.width(), rect.y(), f"({self.canvas_width}, 0)", "right_top")
        draw_label(rect.x(), rect.y() + rect.height(), f"(0, {self.canvas_height})", "left_bottom")
        draw_label(rect.x() + rect.width(), rect.y() + rect.height(), f"({self.canvas_width}, {self.canvas_height})", "right_bottom")
        
        # Center coordinate label
        draw_label(cx, cy, f"({self.canvas_width//2}, {self.canvas_height//2})", "left_top")
        
        painter.restore()

    def draw_skeleton(
        self,
        painter: QPainter,
        points: List[Tuple[float, float]],
        is_selected: bool,
        is_locked: bool
    ):
        """Renders a single skeleton's joints and connections onto screen coordinates."""
        # Calculate dynamic size based on current zoom
        joint_radius = max(3.5, 4.5 * self.scale_factor)
        bone_width = max(2.5, 4.0 * self.scale_factor)
        
        # Selected skeleton gets a subtle glow or hover effect on joints
        select_halo_radius = joint_radius + 4
        
        # 1. Draw Bones
        for idx, (p_idx, c_idx) in enumerate(POSE_CONNECTIONS):
            if p_idx < len(points) and c_idx < len(points):
                pt1 = points[p_idx]
                pt2 = points[c_idx]
                
                # Skip uninitialized / hidden joints
                if (pt1[0] == 0 and pt1[1] == 0) or (pt2[0] == 0 and pt2[1] == 0):
                    continue
                    
                sx1, sy1 = self.to_screen_coords(pt1[0], pt1[1])
                sx2, sy2 = self.to_screen_coords(pt2[0], pt2[1])
                
                rgb = CONNECTION_COLORS[idx]
                color = QColor(rgb[0], rgb[1], rgb[2], 255)
                
                pen = QPen(color)
                pen.setWidthF(bone_width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                
                painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

        # 2. Draw Selected Character Torso Glow (Dotted line around spine/shoulders)
        if is_selected and len(points) > 5:
            # Highlight neck (index 1) with an active neon glow ring
            nx, ny = self.to_screen_coords(points[1][0], points[1][1])
            glow_pen = QPen(QColor(0, 255, 255, 200), 2.0, Qt.PenStyle.DotLine)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(nx, ny), joint_radius * 2.5, joint_radius * 2.5)

        # 3. Draw Joints
        for idx, pt in enumerate(points):
            if pt[0] == 0 and pt[1] == 0:
                continue
                
            sx, sy = self.to_screen_coords(pt[0], pt[1])
            rgb = JOINT_COLORS[idx]
            color = QColor(rgb[0], rgb[1], rgb[2], 255)
            
            # Joint Highlight if character is selected
            if is_selected:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(rgb[0], rgb[1], rgb[2], 50)))
                painter.drawEllipse(QPointF(sx, sy), select_halo_radius, select_halo_radius)
                
            # Draw standard solid joint
            painter.setPen(Qt.PenStyle.NoPen)
            if is_locked:
                # Dim joints if locked
                painter.setBrush(QBrush(QColor(128, 128, 128)))
            else:
                painter.setBrush(QBrush(color))
                
            painter.drawEllipse(QPointF(sx, sy), joint_radius, joint_radius)

            # 4. Draw Joint Text Labels (Index or Name)
            if self.labels_mode != "none":
                painter.save()
                font = QFont("Segoe UI", int(max(9, 10 * self.scale_factor)))
                font.setBold(True)
                painter.setFont(font)
                
                # Determine label content
                if self.labels_mode == "indices":
                    label_text = str(idx)
                else: # "names"
                    label_text = i18n.get_translation(f"joint_{idx}", self.lang)
                
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label_text)
                th = fm.height()
                
                # Offset label to right-top of the joint dot
                tx = sx + joint_radius + 4
                ty = sy - 2
                
                # Render background capsule/rect behind text for high legibility
                label_rect = QRectF(tx - 3, ty - th + 3, tw + 6, th)
                # Dark background for readability
                painter.fillRect(label_rect, QColor(0, 0, 0, 160))
                # Border matching joint color
                border_pen = QPen(color, 1.0)
                painter.setPen(border_pen)
                painter.drawRect(label_rect)
                
                # Draw text inside
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QPointF(tx, ty), label_text)
                painter.restore()

    # --- Mouse & Interaction Events ---
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
            
        self.update_transforms()
        sx, sy = event.position().x(), event.position().y()
        vx, vy = self.to_canvas_coords(sx, sy)
        
        # 1. Search for clicking a joint (scales tolerance with zoom)
        tolerance = 15.0 / self.scale_factor
        sk_idx, kp_idx = pose_math.find_closest_keypoint(self.skeletons, vx, vy, tolerance)
        
        if sk_idx != -1:
            # Hit! Change active character
            self.selected_char_idx = sk_idx
            self.char_selected.emit(sk_idx)
            
            # Decide if moving whole character or single joint
            # Direct dragging on Neck (index 1) moves the entire skeleton
            if kp_idx == 1:
                self.dragged_sk_idx = sk_idx
                self.dragged_whole_char = True
            else:
                self.dragged_sk_idx = sk_idx
                self.dragged_kp_idx = kp_idx
                self.dragged_whole_char = False
                
            self.last_canvas_mouse_pos = (vx, vy)
            self.update()
            return

        # 2. If no joint clicked, look if we clicked near any neck to select that person
        torso_tolerance = 25.0 / self.scale_factor
        sk_idx = pose_math.find_closest_torso(self.skeletons, vx, vy, torso_tolerance)
        if sk_idx != -1:
            self.selected_char_idx = sk_idx
            self.char_selected.emit(sk_idx)
            self.update()
            
    def mouseMoveEvent(self, event):
        if self.dragged_sk_idx == -1:
            return
            
        self.update_transforms()
        sx, sy = event.position().x(), event.position().y()
        vx, vy = self.to_canvas_coords(sx, sy)
        
        # Reference active skeleton
        sk = self.skeletons[self.dragged_sk_idx]
        if sk.get("locked", False):
            self.dragged_sk_idx = -1
            return
            
        points = list(sk["points"])
        
        if self.dragged_whole_char:
            # Calculate canvas-space translation delta
            lx, ly = self.last_canvas_mouse_pos
            dx = vx - lx
            dy = vy - ly
            
            sk["points"] = pose_math.translate_points(points, dx, dy)
            self.last_canvas_mouse_pos = (vx, vy)
            
        elif self.dragged_kp_idx != -1:
            # Drag single joint
            kp_idx = self.dragged_kp_idx
            
            # Apply coordinate constrain so joints stay inside canvas box (optional, we allow slight bounds overflow)
            cx = max(0.0, min(float(self.canvas_width), vx))
            cy = max(0.0, min(float(self.canvas_height), vy))
            
            points[kp_idx] = (cx, cy)
            sk["points"] = points
            
        self.pose_changed.emit()
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragged_sk_idx = -1
        self.dragged_kp_idx = -1
        self.dragged_whole_char = False
        
    def wheelEvent(self, event):
        """Allows rotating active skeleton using mouse wheel when hovering near its torso."""
        if self.selected_char_idx == -1:
            return
            
        sk = self.skeletons[self.selected_char_idx]
        if sk.get("locked", False):
            return
            
        self.update_transforms()
        sx, sy = event.position().x(), event.position().y()
        vx, vy = self.to_canvas_coords(sx, sy)
        
        points = sk["points"]
        neck = points[1]
        
        # Check if hovering near active person's Neck to perform rotation/scaling
        dist = pose_math.calculate_distance((vx, vy), neck)
        if dist < 60.0 / self.scale_factor:
            angle_delta = event.angleDelta().y() / 120.0  # Usually +1.0 or -1.0
            
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl + Wheel: Scale character
                scale_factor = 1.0 + (angle_delta * 0.05)
                sk["points"] = pose_math.scale_points(points, scale_factor, neck)
            else:
                # Normal Wheel: Rotate character around Neck
                rot_deg = angle_delta * 5.0  # 5 degrees per click
                sk["points"] = pose_math.rotate_pose(points, rot_deg, neck)
                
            self.pose_changed.emit()
            self.update()
            event.accept()
