"""
mannequin_renderer.py - 3D-style mannequin figure renderer

Renders skeleton joint positions as a smooth, shaded 3D mannequin figure
similar to artist's reference models (e.g., Clip Studio Paint, Design Doll).
Uses QPainter with gradient fills and QPainterPath for smooth body contours.

Joint Index Reference:
    0: Nose       1: Neck       2: R.Shoulder  3: R.Elbow
    4: R.Wrist    5: L.Shoulder 6: L.Elbow     7: L.Wrist
    8: R.Hip      9: R.Knee    10: R.Ankle    11: L.Hip
   12: L.Knee    13: L.Ankle   14: R.Eye      15: L.Eye
   16: R.Ear     17: L.Ear
"""
import math
from typing import List, Tuple, Optional

from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath,
    QLinearGradient, QRadialGradient, QPolygonF, QFont
)
from PySide6.QtCore import Qt, QPointF, QRectF


# ============================================================
#  Color Palette
# ============================================================

class Colors:
    """Color scheme for the mannequin rendering."""
    # Body
    BODY_BASE      = QColor(188, 188, 188)
    BODY_LIGHT     = QColor(218, 216, 214)
    BODY_SHADOW    = QColor(148, 148, 150)
    BODY_DEEP      = QColor(125, 125, 128)
    OUTLINE        = QColor(130, 130, 135, 140)

    # Joints
    JOINT_BASE     = QColor(172, 172, 175)
    JOINT_LIGHT    = QColor(208, 208, 210)
    JOINT_SHADOW   = QColor(138, 138, 142)

    # Head
    HEAD_BASE      = QColor(192, 190, 187)
    HEAD_LIGHT     = QColor(222, 220, 217)
    HEAD_SHADOW    = QColor(155, 153, 150)

    # Articulation guide lines
    ARTIC          = QColor(195, 140, 85, 155)
    ARTIC_STRONG   = QColor(200, 145, 90, 200)


# ============================================================
#  Proportion Constants (ratios of body_height)
# ============================================================

# Limb segment widths: (start_ratio, end_ratio)
SEGMENT_WIDTHS = {
    "neck":            (0.044, 0.040),
    "r_upper_arm":     (0.050, 0.040),
    "r_forearm":       (0.040, 0.032),
    "l_upper_arm":     (0.050, 0.040),
    "l_forearm":       (0.040, 0.032),
    "r_upper_leg":     (0.068, 0.052),
    "r_lower_leg":     (0.052, 0.038),
    "l_upper_leg":     (0.068, 0.052),
    "l_lower_leg":     (0.052, 0.038),
}

HEAD_RADIUS_RATIO   = 0.068
HAND_RADIUS_RATIO   = 0.028
FOOT_WIDTH_RATIO    = 0.040
FOOT_LENGTH_RATIO   = 0.068
JOINT_RADIUS_RATIO  = 0.020
TORSO_EXPAND_RATIO  = 0.018


# ============================================================
#  Vector Utilities
# ============================================================

def _len(dx: float, dy: float) -> float:
    return math.sqrt(dx * dx + dy * dy)

def _norm(dx: float, dy: float) -> Tuple[float, float]:
    l = _len(dx, dy)
    return (dx / l, dy / l) if l > 0.001 else (0.0, 0.0)

def _perp(dx: float, dy: float) -> Tuple[float, float]:
    """90° counter-clockwise perpendicular."""
    return (-dy, dx)

def _valid(points, idx: int) -> bool:
    """Check if joint index is valid (not at origin)."""
    return idx < len(points) and not (points[idx][0] == 0 and points[idx][1] == 0)


# ============================================================
#  Body Height Calculation
# ============================================================

def _body_height(points) -> float:
    """Estimate body height from valid joint positions."""
    valid_pts = [(x, y) for x, y in points if x != 0 or y != 0]
    if len(valid_pts) < 2:
        return 300.0
    min_y = min(p[1] for p in valid_pts)
    max_y = max(p[1] for p in valid_pts)
    return max(max_y - min_y, 80.0)


# ============================================================
#  Low-Level Drawing Primitives
# ============================================================

def _draw_capsule(painter: QPainter, p1, p2, w1: float, w2: float,
                  light: QColor, shadow: QColor, outline: QColor,
                  draw_artic: bool = True):
    """
    Draw a tapered capsule (limb segment) between two points with 3D gradient.
    p1, p2: (x, y) tuples
    w1, w2: widths at p1 and p2
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    seg_len = _len(dx, dy)
    if seg_len < 1.0:
        return

    ux, uy = _norm(dx, dy)
    nx, ny = _perp(ux, uy)

    # Build capsule path with rounded end caps
    # Top-left, bottom-left corners at p1; bottom-right, top-right at p2
    tl = QPointF(p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2)
    bl = QPointF(p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2)
    br = QPointF(p2[0] - nx * w2 / 2, p2[1] - ny * w2 / 2)
    tr = QPointF(p2[0] + nx * w2 / 2, p2[1] + ny * w2 / 2)

    # Control points for rounded caps
    cap1 = QPointF(p1[0] - ux * w1 * 0.35, p1[1] - uy * w1 * 0.35)
    cap2 = QPointF(p2[0] + ux * w2 * 0.35, p2[1] + uy * w2 * 0.35)

    path = QPainterPath()
    path.moveTo(tl)
    path.quadTo(cap1, bl)
    path.lineTo(br)
    path.quadTo(cap2, tr)
    path.closeSubpath()

    # Gradient perpendicular to segment axis
    max_w = max(w1, w2)
    mid_x = (p1[0] + p2[0]) / 2
    mid_y = (p1[1] + p2[1]) / 2

    grad = QLinearGradient(
        mid_x + nx * max_w * 0.6, mid_y + ny * max_w * 0.6,
        mid_x - nx * max_w * 0.6, mid_y - ny * max_w * 0.6,
    )
    grad.setColorAt(0.00, light)
    grad.setColorAt(0.40, light.darker(105))
    grad.setColorAt(0.60, shadow.lighter(108))
    grad.setColorAt(1.00, shadow)

    painter.setPen(QPen(outline, max(0.8, max_w * 0.04)))
    painter.setBrush(QBrush(grad))
    painter.drawPath(path)

    # Articulation cross-line at midpoint
    if draw_artic:
        mw = (w1 + w2) / 2
        art_pen = QPen(Colors.ARTIC, max(0.8, mw * 0.07))
        painter.setPen(art_pen)
        painter.drawLine(
            QPointF(mid_x + nx * mw * 0.42, mid_y + ny * mw * 0.42),
            QPointF(mid_x - nx * mw * 0.42, mid_y - ny * mw * 0.42),
        )


def _draw_sphere(painter: QPainter, cx: float, cy: float, radius: float,
                 base: QColor, light: QColor, shadow: QColor,
                 outline: QColor, draw_artic_ring: bool = False):
    """Draw a sphere (joint ball) with radial gradient."""
    grad = QRadialGradient(
        cx - radius * 0.28, cy - radius * 0.28, radius * 1.25
    )
    grad.setColorAt(0.00, light)
    grad.setColorAt(0.45, base)
    grad.setColorAt(0.80, shadow)
    grad.setColorAt(1.00, shadow.darker(115))

    painter.setPen(QPen(outline, max(0.6, radius * 0.06)))
    painter.setBrush(QBrush(grad))
    painter.drawEllipse(QPointF(cx, cy), radius, radius)

    if draw_artic_ring:
        art_pen = QPen(Colors.ARTIC, max(0.6, radius * 0.08))
        painter.setPen(art_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius * 0.72, radius * 0.72)


# ============================================================
#  Body Part Renderers
# ============================================================

def _draw_torso(painter: QPainter, points, bh: float):
    """Draw the torso as a gradient-filled smooth polygon."""
    if not all(_valid(points, i) for i in [2, 5, 8, 11]):
        return

    rs = points[2]   # R shoulder
    ls = points[5]   # L shoulder
    rh = points[8]   # R hip
    lh = points[11]  # L hip

    ex = bh * TORSO_EXPAND_RATIO  # body volume expansion

    # Build smooth torso outline with bezier curves
    path = QPainterPath()

    # Across top: right shoulder -> left shoulder (collarbone)
    path.moveTo(rs[0] - ex, rs[1])
    path.lineTo(ls[0] + ex, ls[1])

    # Left side: shoulder -> waist -> hip (curves inward at waist)
    l_mid_x = (ls[0] + lh[0]) / 2 + ex * 1.8
    l_mid_y = (ls[1] + lh[1]) / 2
    path.quadTo(l_mid_x, l_mid_y, lh[0] + ex * 0.8, lh[1])

    # Across bottom: left hip -> right hip (pelvis)
    path.lineTo(rh[0] - ex * 0.8, rh[1])

    # Right side: hip -> waist -> shoulder
    r_mid_x = (rs[0] + rh[0]) / 2 - ex * 1.8
    r_mid_y = (rs[1] + rh[1]) / 2
    path.quadTo(r_mid_x, r_mid_y, rs[0] - ex, rs[1])

    path.closeSubpath()

    # Gradient left-to-right for 3D feel
    cx = (rs[0] + ls[0]) / 2
    torso_w = abs(ls[0] - rs[0]) + ex * 4

    grad = QLinearGradient(cx - torso_w * 0.55, 0, cx + torso_w * 0.55, 0)
    grad.setColorAt(0.00, Colors.BODY_LIGHT)
    grad.setColorAt(0.30, QColor(208, 208, 208))
    grad.setColorAt(0.50, Colors.BODY_BASE)
    grad.setColorAt(0.75, Colors.BODY_SHADOW)
    grad.setColorAt(1.00, Colors.BODY_DEEP)

    painter.setPen(QPen(Colors.OUTLINE, max(0.8, bh * 0.003)))
    painter.setBrush(QBrush(grad))
    painter.drawPath(path)

    # Articulation lines on torso
    ct_x = (rs[0] + ls[0]) / 2
    ct_y = (rs[1] + ls[1]) / 2
    cb_x = (rh[0] + lh[0]) / 2
    cb_y = (rh[1] + lh[1]) / 2

    art_pen = QPen(Colors.ARTIC, max(0.8, bh * 0.003))
    painter.setPen(art_pen)

    # Center vertical line
    painter.drawLine(QPointF(ct_x, ct_y), QPointF(cb_x, cb_y))

    # Chest horizontal
    chest_t = 0.35
    chest_y = ct_y + (cb_y - ct_y) * chest_t
    chest_lx = ls[0] + (lh[0] - ls[0]) * chest_t + ex * 1.2
    chest_rx = rs[0] + (rh[0] - rs[0]) * chest_t - ex * 1.2
    painter.drawLine(QPointF(chest_rx, chest_y), QPointF(chest_lx, chest_y))

    # Waist horizontal
    waist_t = 0.70
    waist_y = ct_y + (cb_y - ct_y) * waist_t
    waist_lx = ls[0] + (lh[0] - ls[0]) * waist_t + ex * 0.8
    waist_rx = rs[0] + (rh[0] - rs[0]) * waist_t - ex * 0.8
    painter.drawLine(QPointF(waist_rx, waist_y), QPointF(waist_lx, waist_y))


def _draw_head(painter: QPainter, points, bh: float):
    """Draw the head as a gradient sphere with a subtle jaw contour."""
    if not _valid(points, 0) or not _valid(points, 1):
        return

    nose = points[0]
    neck = points[1]
    dx = nose[0] - neck[0]
    dy = nose[1] - neck[1]
    ux, uy = _norm(dx, dy)

    head_r = bh * HEAD_RADIUS_RATIO

    # Center the head above the nose
    hx = nose[0] + ux * head_r * 0.3
    hy = nose[1] + uy * head_r * 0.3

    # Radial gradient for 3D sphere
    grad = QRadialGradient(hx - head_r * 0.22, hy - head_r * 0.28, head_r * 1.3)
    grad.setColorAt(0.00, Colors.HEAD_LIGHT)
    grad.setColorAt(0.35, Colors.HEAD_BASE)
    grad.setColorAt(0.75, Colors.HEAD_SHADOW)
    grad.setColorAt(1.00, Colors.HEAD_SHADOW.darker(115))

    painter.setPen(QPen(Colors.OUTLINE, max(0.8, bh * 0.003)))
    painter.setBrush(QBrush(grad))
    painter.drawEllipse(QPointF(hx, hy), head_r, head_r * 1.06)

    # Subtle jaw / chin line
    jaw_y = hy + head_r * 0.45
    jaw_w = head_r * 0.55
    art_pen = QPen(Colors.ARTIC, max(0.6, bh * 0.002))
    painter.setPen(art_pen)
    painter.drawLine(
        QPointF(hx - jaw_w, jaw_y),
        QPointF(hx + jaw_w, jaw_y),
    )

    # Eye-level horizontal line
    eye_y = hy - head_r * 0.10
    painter.drawLine(
        QPointF(hx - head_r * 0.65, eye_y),
        QPointF(hx + head_r * 0.65, eye_y),
    )

    # Center vertical line on face
    painter.drawLine(
        QPointF(hx, hy - head_r * 0.85),
        QPointF(hx, hy + head_r * 0.75),
    )


def _draw_hand(painter: QPainter, wrist, elbow, bh: float):
    """Draw a simplified mitten-like hand."""
    dx = wrist[0] - elbow[0]
    dy = wrist[1] - elbow[1]
    ux, uy = _norm(dx, dy)

    hand_r = bh * HAND_RADIUS_RATIO
    hx = wrist[0] + ux * hand_r * 0.8
    hy = wrist[1] + uy * hand_r * 0.8

    # Perpendicular for gradient direction
    nx, ny = _perp(ux, uy)

    # Slightly elongated ellipse in the hand direction
    painter.save()
    painter.translate(hx, hy)
    angle = math.degrees(math.atan2(dy, dx))
    painter.rotate(angle)

    grad = QLinearGradient(-hand_r, -hand_r, hand_r, hand_r)
    grad.setColorAt(0.0, Colors.BODY_LIGHT)
    grad.setColorAt(0.5, Colors.BODY_BASE)
    grad.setColorAt(1.0, Colors.BODY_SHADOW)

    painter.setPen(QPen(Colors.OUTLINE, max(0.5, bh * 0.002)))
    painter.setBrush(QBrush(grad))
    painter.drawEllipse(QPointF(0, 0), hand_r * 1.3, hand_r * 0.9)

    painter.restore()


def _draw_foot(painter: QPainter, ankle, knee, bh: float):
    """Draw a simplified foot shape extending from the ankle."""
    dx = ankle[0] - knee[0]
    dy = ankle[1] - knee[1]
    ux, uy = _norm(dx, dy)

    fw = bh * FOOT_WIDTH_RATIO
    fl = bh * FOOT_LENGTH_RATIO

    # Foot extends from ankle in leg direction, then angles forward
    fx = ankle[0] + ux * fl * 0.25
    fy = ankle[1] + uy * fl * 0.25

    painter.save()
    painter.translate(fx, fy)

    # Angle the foot: combine leg direction with a forward bias
    leg_angle = math.degrees(math.atan2(dy, dx))
    # Tilt foot more horizontally (toward 90° which is straight down -> forward)
    foot_angle = leg_angle * 0.4 + 90 * 0.6  # blend toward horizontal
    painter.rotate(foot_angle)

    grad = QLinearGradient(-fl / 2, -fw / 2, fl / 2, fw / 2)
    grad.setColorAt(0.0, Colors.BODY_LIGHT)
    grad.setColorAt(0.5, Colors.BODY_BASE)
    grad.setColorAt(1.0, Colors.BODY_SHADOW)

    painter.setPen(QPen(Colors.OUTLINE, max(0.5, bh * 0.002)))
    painter.setBrush(QBrush(grad))

    # Shoe-like rounded rectangle
    foot_rect = QRectF(-fl / 2, -fw / 2, fl, fw)
    painter.drawRoundedRect(foot_rect, fw * 0.4, fw * 0.4)

    # Articulation toe line
    art_pen = QPen(Colors.ARTIC, max(0.5, bh * 0.002))
    painter.setPen(art_pen)
    painter.drawLine(QPointF(fl * 0.15, -fw * 0.35), QPointF(fl * 0.15, fw * 0.35))

    painter.restore()


# ============================================================
#  Limb Drawing Helper
# ============================================================

def _draw_limb(painter: QPainter, points, ja: int, jb: int,
               wr_a: float, wr_b: float, bh: float):
    """Draw a limb segment if both joints are valid."""
    if not _valid(points, ja) or not _valid(points, jb):
        return
    w1 = bh * wr_a
    w2 = bh * wr_b
    _draw_capsule(
        painter, points[ja], points[jb], w1, w2,
        Colors.BODY_LIGHT, Colors.BODY_SHADOW, Colors.OUTLINE
    )


def _draw_joint(painter: QPainter, points, idx: int, bh: float,
                scale: float = 1.0, artic: bool = True):
    """Draw a joint sphere if valid."""
    if not _valid(points, idx):
        return
    r = bh * JOINT_RADIUS_RATIO * scale
    _draw_sphere(
        painter, points[idx][0], points[idx][1], r,
        Colors.JOINT_BASE, Colors.JOINT_LIGHT, Colors.JOINT_SHADOW,
        Colors.OUTLINE, draw_artic_ring=artic
    )


# ============================================================
#  Main Mannequin Renderer
# ============================================================

def draw_mannequin(painter: QPainter, points, scale_factor: float = 1.0):
    """
    Draw a complete 3D-style mannequin figure from skeleton joint positions.

    Args:
        painter: Active QPainter instance (already begun)
        points: List of 18 joint positions [(x, y), ...]
        scale_factor: Scale multiplier for the rendering
    """
    bh = _body_height(points)

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # ========== Drawing Order (back to front) ==========

    # --- 1. Legs (behind torso) ---
    # Left leg (drawn first = further back)
    _draw_limb(painter, points, 11, 12, 0.068, 0.052, bh)  # L upper leg
    _draw_limb(painter, points, 12, 13, 0.052, 0.038, bh)  # L lower leg

    # Right leg
    _draw_limb(painter, points, 8, 9, 0.068, 0.052, bh)    # R upper leg
    _draw_limb(painter, points, 9, 10, 0.052, 0.038, bh)   # R lower leg

    # Feet
    if _valid(points, 13) and _valid(points, 12):
        _draw_foot(painter, points[13], points[12], bh)
    if _valid(points, 10) and _valid(points, 9):
        _draw_foot(painter, points[10], points[9], bh)

    # Ankle joints
    _draw_joint(painter, points, 10, bh, 1.1, True)
    _draw_joint(painter, points, 13, bh, 1.1, True)

    # Knee joints
    _draw_joint(painter, points, 9, bh, 1.3, True)
    _draw_joint(painter, points, 12, bh, 1.3, True)

    # --- 2. Torso ---
    _draw_torso(painter, points, bh)

    # Hip joints
    _draw_joint(painter, points, 8, bh, 1.4, True)
    _draw_joint(painter, points, 11, bh, 1.4, True)

    # Shoulder joints
    _draw_joint(painter, points, 2, bh, 1.4, True)
    _draw_joint(painter, points, 5, bh, 1.4, True)

    # --- 3. Arms (in front of torso) ---
    # Left arm (drawn first = further back)
    _draw_limb(painter, points, 5, 6, 0.050, 0.040, bh)    # L upper arm
    _draw_limb(painter, points, 6, 7, 0.040, 0.032, bh)    # L forearm

    # Right arm
    _draw_limb(painter, points, 2, 3, 0.050, 0.040, bh)    # R upper arm
    _draw_limb(painter, points, 3, 4, 0.040, 0.032, bh)    # R forearm

    # Elbow joints
    _draw_joint(painter, points, 6, bh, 1.2, True)
    _draw_joint(painter, points, 3, bh, 1.2, True)

    # Wrist joints
    _draw_joint(painter, points, 7, bh, 1.0, True)
    _draw_joint(painter, points, 4, bh, 1.0, True)

    # Hands
    if _valid(points, 7) and _valid(points, 6):
        _draw_hand(painter, points[7], points[6], bh)
    if _valid(points, 4) and _valid(points, 3):
        _draw_hand(painter, points[4], points[3], bh)

    # --- 4. Neck ---
    if _valid(points, 0) and _valid(points, 1):
        neck_w1 = bh * 0.044
        neck_w2 = bh * 0.040
        _draw_capsule(
            painter, points[1], points[0], neck_w1, neck_w2,
            Colors.BODY_LIGHT, Colors.BODY_SHADOW, Colors.OUTLINE,
            draw_artic=True
        )

    # Neck joint
    _draw_joint(painter, points, 1, bh, 1.0, False)

    # --- 5. Head (on top) ---
    _draw_head(painter, points, bh)

    painter.restore()
