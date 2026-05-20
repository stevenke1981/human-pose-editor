"""
Input/Output module for exporting skeleton data into images using PySide6.
Handles headless high-resolution rendering with anti-aliasing, proportional scaling,
coordinate boundary/reference markers, and sidecar prompt generation.
"""
import os
from typing import List, Dict, Tuple
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QBrush, QFont, QPixmap
from PySide6.QtCore import Qt, QPointF, QRectF
from pose_presets import POSE_CONNECTIONS, CONNECTION_COLORS, JOINT_COLORS
import i18n


def draw_skeleton_on_painter(
    painter: QPainter,
    points: List[Tuple[float, float]],
    scale_factor: float,
    labels_mode: str = "none",
    lang: str = "zh_TW",
    skeleton_style: str = "classic"
):
    """
    Draws a single skeleton (points + connections or 3D mannequin) on a QPainter.
    Scales joint radius, bone thickness, and text labels by scale_factor.
    """
    # Proportional sizes
    joint_radius = max(3.0, 4.5 * scale_factor)
    bone_width = max(2.5, 4.0 * scale_factor)
    
    if skeleton_style == "mannequin":
        from mannequin_renderer import draw_mannequin
        draw_mannequin(painter, points, scale_factor)
    else:
        # 1. Draw Bones (Connections)
        for idx, (p_idx, c_idx) in enumerate(POSE_CONNECTIONS):
            if p_idx < len(points) and c_idx < len(points):
                p1 = points[p_idx]
                p2 = points[c_idx]
                
                # Avoid drawing joints that are exactly at (0, 0) or uninitialized
                if (p1[0] == 0 and p1[1] == 0) or (p2[0] == 0 and p2[1] == 0):
                    continue
                    
                color = CONNECTION_COLORS[idx]
                q_color = QColor(color[0], color[1], color[2], 255)
                
                pen = QPen(q_color)
                pen.setWidthF(bone_width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                
                painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
                
        # 2. Draw Joints
        for idx, pt in enumerate(points):
            if pt[0] == 0 and pt[1] == 0:
                continue
                
            color = JOINT_COLORS[idx]
            q_color = QColor(color[0], color[1], color[2], 255)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(q_color))
            
            painter.drawEllipse(QPointF(pt[0], pt[1]), joint_radius, joint_radius)

    # 3. Draw Joint Text Labels (Index or Name)
    if labels_mode != "none":
        for idx, pt in enumerate(points):
            if pt[0] == 0 and pt[1] == 0:
                continue
                
            color = JOINT_COLORS[idx]
            q_color = QColor(color[0], color[1], color[2], 255)
            
            painter.save()
            # Set high-quality font scaled to output image size
            font_size = int(max(8, 10 * scale_factor))
            font = QFont("Segoe UI", font_size)
            font.setBold(True)
            painter.setFont(font)
            
            # Determine label text
            if labels_mode == "indices":
                label_text = str(idx)
            else:  # "names"
                label_text = i18n.get_translation(f"joint_{idx}", lang)
                
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(label_text)
            th = fm.height()
            
            tx = pt[0] + joint_radius + 4 * scale_factor
            ty = pt[1] - 2 * scale_factor
            
            # Background capsule
            label_rect = QRectF(tx - 3 * scale_factor, ty - th + 3 * scale_factor, tw + 6 * scale_factor, th)
            painter.fillRect(label_rect, QColor(0, 0, 0, 160))
            
            # Border matching joint color
            border_pen = QPen(q_color, max(1.0, 1.0 * scale_factor))
            painter.setPen(border_pen)
            painter.drawRect(label_rect)
            
            # Text inside
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QPointF(tx, ty), label_text)
            painter.restore()


def export_to_image(
    canvas_size: Tuple[int, int],
    skeletons: List[Dict],
    background_mode: str,
    file_path: str,
    labels_mode: str = "none",
    lang: str = "zh_TW",
    show_scale_axes: bool = True,
    show_pose_name: bool = True,
    bg_image_path: str = "",
    bg_opacity: float = 1.0,
    skeleton_style: str = "classic"
) -> bool:
    """
    Renders skeletons headlessly onto a QImage and exports to file_path.
    
    Args:
        canvas_size: (width, height) e.g., (512, 768)
        skeletons: List of dicts, e.g. [{"points": [...], "visible": True, "locked": False}]
        background_mode: "black", "white", or "transparent"
        file_path: Output image destination path
        labels_mode: "none", "indices", or "names"
        lang: Active interface language for name tags
        
    Returns:
        True if success, False otherwise.
    """
    width, height = canvas_size
    
    # Choose format based on transparency
    if background_mode == "transparent" and file_path.lower().endswith(".png"):
        img_format = QImage.Format.Format_ARGB32
    else:
        img_format = QImage.Format.Format_RGB32

    # Create image canvas
    image = QImage(width, height, img_format)
    
    # Initialize background
    if background_mode == "black":
        image.fill(QColor(0, 0, 0, 255))
    elif background_mode == "white":
        image.fill(QColor(255, 255, 255, 255))
    elif background_mode == "transparent":
        image.fill(QColor(0, 0, 0, 0)) # Fully transparent
    else:
        image.fill(QColor(0, 0, 0, 255)) # Default to black
        
    # Paint skeletons
    painter = QPainter(image)
    # Enable high-quality anti-aliasing
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Draw Background Tracing Image if provided
    if bg_image_path and os.path.exists(bg_image_path):
        bg_pixmap = QPixmap(bg_image_path)
        if not bg_pixmap.isNull():
            painter.save()
            painter.setOpacity(bg_opacity)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(image.rect(), bg_pixmap)
            painter.restore()
    
    # Calculate scale factor relative to 512px base size
    base_dim = 512.0
    scale_factor = max(width, height) / base_dim
    
    # 1. Draw Canvas Reference Points if labels are enabled
    if labels_mode != "none":
        painter.save()
        font = QFont("Consolas", int(max(9, 11 * scale_factor)))
        painter.setFont(font)
        
        # Determine grid color based on background
        grid_color = QColor(0, 229, 255, 90) if background_mode == "black" else QColor(0, 100, 200, 120)
        text_color = QColor(0, 229, 255) if background_mode == "black" else QColor(0, 100, 255)
        text_bg = QColor(0, 0, 0, 170) if background_mode != "white" else QColor(255, 255, 255, 200)
        
        cx = width / 2.0
        cy = height / 2.0
        
        # Draw Center Crosshair
        pen = QPen(grid_color, max(1.0, 1.0 * scale_factor), Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(0.0, cy), QPointF(float(width), cy))
        painter.drawLine(QPointF(cx, 0.0), QPointF(cx, float(height)))
        
        # Draw small reference circles at corners and center
        painter.setPen(QPen(text_color, max(1.0, 1.5 * scale_factor)))
        painter.setBrush(QBrush(QColor(0, 229, 255, 50)))
        corner_r = 4.0 * scale_factor
        painter.drawEllipse(QPointF(0.0, 0.0), corner_r, corner_r)
        painter.drawEllipse(QPointF(float(width), 0.0), corner_r, corner_r)
        painter.drawEllipse(QPointF(0.0, float(height)), corner_r, corner_r)
        painter.drawEllipse(QPointF(float(width), float(height)), corner_r, corner_r)
        painter.drawEllipse(QPointF(cx, cy), corner_r * 1.5, corner_r * 1.5)
        
        # Label Coordinates function
        def draw_label(px, py, text, align):
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            
            if "right" in align:
                offset_x = -tw - 8 * scale_factor
            else:
                offset_x = 8 * scale_factor
                
            if "bottom" in align:
                offset_y = -4 * scale_factor
            else:
                offset_y = th + 2 * scale_factor
                
            tx = px + offset_x
            ty = py + offset_y
            
            # Semi-transparent background
            bg_rect = QRectF(tx - 3 * scale_factor, ty - th + 2 * scale_factor, tw + 6 * scale_factor, th)
            painter.fillRect(bg_rect, text_bg)
            
            painter.setPen(QColor(255, 255, 255) if background_mode == "black" else QColor(0, 0, 0))
            painter.drawText(QPointF(tx, ty), text)
            
        draw_label(0.0, 0.0, "(0, 0)", "left_top")
        draw_label(float(width), 0.0, f"({width}, 0)", "right_top")
        draw_label(0.0, float(height), f"(0, {height})", "left_bottom")
        draw_label(float(width), float(height), f"({width}, {height})", "right_bottom")
        draw_label(cx, cy, f"({width // 2}, {height // 2})", "left_top")
        
        painter.restore()
        
    # 1.5 Draw Scale Bar & XYZ Coordinate Tripod if enabled
    if show_scale_axes:
        painter.save()
        scale = scale_factor
        text_bg = QColor(0, 0, 0, 180) if background_mode != "white" else QColor(255, 255, 255, 210)
        axis_text_color = QColor(255, 255, 255) if background_mode != "white" else QColor(0, 0, 0)
        border_color = QColor(80, 80, 90, 150)
        
        # 100 units in virtual coordinates. Length in screen pixels = 100 * scale
        scale_val_units = 100
        bar_w = scale_val_units * scale
        
        # Position panel rect at bottom-left of the canvas box
        panel_w = bar_w + 30 * scale
        panel_h = 75 * scale
        panel_rect = QRectF(
            10 * scale,
            float(height) - panel_h - 10 * scale,
            panel_w,
            panel_h
        )
        
        # Draw panel background
        painter.setPen(QPen(border_color, 1.0))
        painter.setBrush(QBrush(text_bg))
        painter.drawRoundedRect(panel_rect, 4.0 * scale, 4.0 * scale)
        
        # Draw Map Scale Bar
        scale_line_y = panel_rect.y() + panel_rect.height() - 15 * scale
        scale_left = panel_rect.x() + 15 * scale
        scale_right = scale_left + bar_w
        scale_mid = scale_left + bar_w / 2
        
        # Line pen
        line_color = QColor(0, 229, 255) if background_mode == "black" else QColor(0, 100, 255)
        line_pen = QPen(line_color, max(1.5, 2.0 * scale))
        painter.setPen(line_pen)
        
        # Horizontal bar line
        painter.drawLine(QPointF(scale_left, scale_line_y), QPointF(scale_right, scale_line_y))
        # Ticks (vertical lines at left, middle, right)
        tick_h = 5 * scale
        painter.drawLine(QPointF(scale_left, scale_line_y - tick_h), QPointF(scale_left, scale_line_y + tick_h))
        painter.drawLine(QPointF(scale_mid, scale_line_y - tick_h), QPointF(scale_mid, scale_line_y + tick_h))
        painter.drawLine(QPointF(scale_right, scale_line_y - tick_h), QPointF(scale_right, scale_line_y + tick_h))
        
        # Scale Label
        font_scale = QFont("Consolas", int(max(8, 10 * scale)))
        font_scale.setBold(True)
        painter.setFont(font_scale)
        painter.setPen(axis_text_color)
        
        unit_str = i18n.get_translation("scale_unit", lang)
        scale_text = f"{scale_val_units} {unit_str}"
        fm = painter.fontMetrics()
        tx = scale_left + (bar_w - fm.horizontalAdvance(scale_text)) / 2
        ty = scale_line_y - tick_h - 2 * scale
        painter.drawText(QPointF(tx, ty), scale_text)
        
        # --- XYZ Coordinate Axis Indicator (Tripod) ---
        axes_cx = panel_rect.x() + 45 * scale
        axes_cy = panel_rect.y() + 28 * scale
        axis_len = 16 * scale
        
        # X-axis: pointing right
        x_end_x = axes_cx + axis_len
        x_end_y = axes_cy
        
        # Y-axis: pointing down
        y_end_x = axes_cx
        y_end_y = axes_cy + axis_len
        
        # Z-axis: pointing diagonally up-left
        z_len = axis_len * 0.8
        z_end_x = axes_cx - z_len * 0.707
        z_end_y = axes_cy - z_len * 0.707
        
        # Helper to draw colored arrow with label
        def draw_arrow(ex, ey, color, label, font):
            painter.setPen(QPen(color, max(1.5, 2.0 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(axes_cx, axes_cy), QPointF(ex, ey))
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(ex, ey), 2.0 * scale, 2.0 * scale)
            
            painter.setFont(font)
            painter.setPen(color)
            lx = ex + (4.0 * scale if ex >= axes_cx else -10.0 * scale)
            ly = ey + (4.0 * scale if ey >= axes_cy else -2.0 * scale)
            painter.drawText(QPointF(lx, ly), label)
            
        font_axis = QFont("Consolas", int(max(7, 9 * scale)))
        font_axis.setBold(True)
        
        # Draw Z-axis first
        draw_arrow(z_end_x, z_end_y, QColor(0, 130, 255), "Z", font_axis)
        # Draw X-axis
        draw_arrow(x_end_x, x_end_y, QColor(255, 40, 80), "X", font_axis)
        # Draw Y-axis
        draw_arrow(y_end_x, y_end_y, QColor(0, 220, 100), "Y", font_axis)
        
        # Draw Origin center node
        painter.setPen(QPen(axis_text_color, 1.0))
        painter.setBrush(QBrush(QColor(180, 180, 190)))
        painter.drawEllipse(QPointF(axes_cx, axes_cy), 2.0 * scale, 2.0 * scale)
        
        painter.restore()
        
    # 2. Draw Skeletons
    for idx, sk in enumerate(skeletons):
        if sk.get("visible", True):
            draw_skeleton_on_painter(painter, sk["points"], scale_factor, labels_mode, lang, skeleton_style)
            
            # Draw Floating Pose Name Label above the head
            if show_pose_name:
                painter.save()
                font = QFont("Segoe UI", int(max(10, 11 * scale_factor)))
                font.setBold(True)
                painter.setFont(font)
                
                pose_name = sk.get("pose_name", "")
                pose_disp = i18n.get_pose_display_name(pose_name, lang)
                char_lbl = i18n.get_translation("char_label", lang).format(idx + 1)
                label_text = f" {char_lbl} | {pose_disp} "
                
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(label_text)
                th = fm.height()
                
                points = sk["points"]
                visible_pts = [pt for pt in points if (pt[0] != 0 or pt[1] != 0)]
                if visible_pts:
                    min_y = min(pt[1] for pt in visible_pts)
                    head_pt = points[0] if (points[0][0] != 0 or points[0][1] != 0) else (points[1] if (points[1][0] != 0 or points[1][1] != 0) else visible_pts[0])
                    
                    highest_sy = min_y
                    tx = head_pt[0] - tw / 2.0
                    ty = highest_sy - 15 * scale_factor
                    
                    label_rect = QRectF(tx - 4 * scale_factor, ty - th + 2 * scale_factor, tw + 8 * scale_factor, th + 2 * scale_factor)
                    
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor(18, 19, 22, 220)))
                    painter.drawRoundedRect(label_rect, 4.0 * scale_factor, 4.0 * scale_factor)
                    
                    border_pen = QPen(QColor(100, 100, 110, 150), max(1.0, 1.5 * scale_factor))
                    painter.setPen(border_pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRoundedRect(label_rect, 4.0 * scale_factor, 4.0 * scale_factor)
                    
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(QPointF(tx, ty), label_text)
                    painter.restore()
            
    painter.end()
    
    # Save image
    # Ensure directory exists
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
        
    return image.save(file_path)


def generate_sidecar_prompt(
    canvas_size: Tuple[int, int],
    skeletons: List[Dict],
    file_path: str,
    lang: str = "zh_TW"
) -> str:
    """
    Generates a structured prompt sidecar file (.txt) next to the exported image.
    This file gives Gemini/LLM exact coordinates, landmark definitions, and anatomical part definitions.
    Returns the path to the written text file.
    """
    width, height = canvas_size
    txt_path = os.path.splitext(file_path)[0] + "_prompt.txt"
    
    # 1. Standard body part groups
    groups = {
        "Head": {
            "name_en": "Head & Face", "name_zh": "頭部與五官",
            "indices": [0, 14, 15, 16, 17]
        },
        "Torso": {
            "name_en": "Torso / Spine", "name_zh": "軀幹與脊椎",
            "indices": [1, 8, 11]
        },
        "RightArm": {
            "name_en": "Right Arm", "name_zh": "右手臂",
            "indices": [2, 3, 4]
        },
        "LeftArm": {
            "name_en": "Left Arm", "name_zh": "左手臂",
            "indices": [5, 6, 7]
        },
        "RightLeg": {
            "name_en": "Right Leg", "name_zh": "右腿",
            "indices": [8, 9, 10]
        },
        "LeftLeg": {
            "name_en": "Left Leg", "name_zh": "左腿",
            "indices": [11, 12, 13]
        }
    }
    
    # Joint labels dictionary
    joint_definitions_md = []
    joint_definitions_md.append("| Index | Joint Name (EN) | Joint Name (ZH) | Body Part Group / Anatomical Role |")
    joint_definitions_md.append("|-------|-----------------|-----------------|-----------------------------------|")
    
    for i in range(18):
        name_en = i18n.get_translation(f"joint_{i}", "en_US")
        name_zh = i18n.get_translation(f"joint_{i}", "zh_TW")
        # Find which group it belongs to
        grp_en = "N/A"
        for g_id, g_info in groups.items():
            if i in g_info["indices"]:
                grp_en = g_info["name_en"]
                break
        joint_definitions_md.append(f"| {i:<5} | {name_en:<15} | {name_zh:<15} | {grp_en:<33} |")
        
    joint_mapping_table = "\n".join(joint_definitions_md)
    
    # 2. Extract active character coordinates
    visible_chars = [sk for sk in skeletons if sk.get("visible", True)]
    char_count = len(visible_chars)
    
    char_coords_str = ""
    prompt_coords_str = ""
    
    for c_idx, sk in enumerate(visible_chars):
        pts = sk["points"]
        char_coords_str += f"### CHARACTER #{c_idx + 1}\n"
        char_coords_str += f"- Height Scale: {sk.get('height_scale', 1.0)*100:.1f}%\n"
        char_coords_str += f"- Limb Scale: {sk.get('limb_scale', 1.0)*100:.1f}%\n"
        char_coords_str += f"- Joint Coordinates Table:\n\n"
        char_coords_str += "| Index | Joint Name (EN) | Pixel X | Pixel Y | Normalized X (0.0-1.0) | Normalized Y (0.0-1.0) |\n"
        char_coords_str += "|-------|-----------------|---------|---------|------------------------|------------------------|\n"
        
        prompt_coords_str += f"Character #{c_idx + 1} (Normalized Keypoint Coordinates):\n"
        
        for idx, pt in enumerate(pts):
            if pt[0] == 0 and pt[1] == 0:
                # Joint is hidden/uninitialized
                char_coords_str += f"| {idx:<5} | {i18n.get_translation(f'joint_{idx}', 'en_US'):<15} | {'HIDDEN':<7} | {'HIDDEN':<7} | {'HIDDEN':<22} | {'HIDDEN':<22} |\n"
                continue
                
            px, py = pt
            nx = px / width
            ny = py / height
            name_en = i18n.get_translation(f"joint_{idx}", "en_US")
            char_coords_str += f"| {idx:<5} | {name_en:<15} | {px:<7.1f} | {py:<7.1f} | {nx:<22.4f} | {ny:<22.4f} |\n"
            
            prompt_coords_str += f"  - Joint {idx} ({name_en}): [{nx:.3f}, {ny:.3f}]\n"
            
        char_coords_str += "\n"
        prompt_coords_str += "\n"
        
    # Build text template
    content = f"""================================================================================
HUMAN POSE SKELETON REFERENCE DATA FOR GEMINI / MULTIMODAL LLM
================================================================================

This file contains coordinate references, joint annotations, and body part definitions
for the accompanying pose image. Use this data as a spatial and anatomical reference
for generating, modifying, or analyzing images based on this pose.

--------------------------------------------------------------------------------
1. CANVAS & COORDINATE REFERENCE SYSTEM
--------------------------------------------------------------------------------
- Canvas Width: {width} pixels
- Canvas Height: {height} pixels
- Coordinate Origin: Top-Left corner is (0, 0)
- Axis Directions:
  * X-axis: Horizontal, increases from Left (0) to Right ({width})
  * Y-axis: Vertical, increases from Top (0) to Bottom ({height})
- Bounding Coordinates:
  * Top-Left: (0, 0)
  * Top-Right: ({width}, 0)
  * Bottom-Left: (0, {height})
  * Bottom-Right: ({width}, {height})
  * Center Point: ({width // 2}, {height // 2})

--------------------------------------------------------------------------------
2. OPENPOSE 18-KEYPOINT DEFINITIONS & ANATOMICAL GROUPING
--------------------------------------------------------------------------------
Below is the standard layout of the 18 keypoints. This mapping explains how 
joints are numbered, their standard names, and which body parts they belong to.

{joint_mapping_table}

--------------------------------------------------------------------------------
3. ANATOMICAL LIMB CONNECTIONS (BONES)
--------------------------------------------------------------------------------
Bones are represented by lines connecting the following joints:
- Head & Face: (1-0), (0-14), (14-16), (0-15), (15-17), (16-2), (17-5)
- Torso / Spine: (1-8), (1-11)
- Right Arm: RShoulder(2) -> RElbow(3) -> RWrist(4)
- Left Arm: LShoulder(5) -> LElbow(6) -> LWrist(7)
- Right Leg: RHip(8) -> RKnee(9) -> RAnkle(10)
- Left Leg: LHip(11) -> LKnee(12) -> LAnkle(13)

--------------------------------------------------------------------------------
4. ACTIVE CHARACTER POSE COORDINATES
--------------------------------------------------------------------------------
There are {char_count} character(s) visible on the canvas. Below are their keypoint
coordinates in absolute pixels (X, Y) and normalized values (0.0 to 1.0).

{char_coords_str}
--------------------------------------------------------------------------------
5. SUGGESTED LLM / GEMINI PROMPT
--------------------------------------------------------------------------------
Use the following prompt text directly in Gemini to guide the image generation:

"Generate a high-quality photo based on the accompanying pose skeleton image.
The image contains {char_count} character(s) whose joints are mapped using the OpenPose 18-keypoint format.
Here is the precise spatial data of the characters' keypoints (normalized coordinates where [0,0] is top-left and [1,1] is bottom-right):

{prompt_coords_str.strip()}

Please generate an image where the characters' body positions, limbs, head tilt, and alignment match these coordinates perfectly.
[Describe your characters' appearance, clothing, actions, and the background environment here...]"
================================================================================
"""
    # Write file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return txt_path
