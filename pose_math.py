"""
Modular geometric and mathematical functions for human pose skeletons.
All functions are pure and operate on coordinate lists/arrays.
"""
import math
from typing import List, Tuple, Dict

# COCO OpenPose 18 Keypoints Index mapping for anatomical mirroring
# Index: 0:Nose, 1:Neck, 2:RShoulder, 3:RElbow, 4:RWrist, 5:LShoulder, 6:LElbow, 7:LWrist,
#        8:RHip, 9:RKnee, 10:RAnkle, 11:LHip, 12:LKnee, 13:LAnkle, 14:REye, 15:LEye, 16:REar, 17:LEar
MIRROR_SWAP_MAP = {
    2: 5,   # RShoulder <-> LShoulder
    3: 6,   # RElbow <-> LElbow
    4: 7,   # RWrist <-> LWrist
    8: 11,  # RHip <-> LHip
    9: 12,  # RKnee <-> LKnee
    10: 13, # RAnkle <-> LAnkle
    14: 15, # REye <-> LEye
    16: 17  # REar <-> LEar
}


def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates the Euclidean distance between two 2D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def translate_points(points: List[Tuple[float, float]], dx: float, dy: float) -> List[Tuple[float, float]]:
    """Translates a list of 2D points by dx and dy."""
    return [(x + dx, y + dy) for x, y in points]


def rotate_point(point: Tuple[float, float], center: Tuple[float, float], angle_rad: float) -> Tuple[float, float]:
    """Rotates a single 2D point around a center by an angle in radians."""
    x, y = point
    cx, cy = center
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Translate to origin
    nx = x - cx
    ny = y - cy
    
    # Rotate
    rx = nx * cos_a - ny * sin_a
    ry = nx * sin_a + ny * cos_a
    
    # Translate back
    return (rx + cx, ry + cy)


def rotate_pose(points: List[Tuple[float, float]], angle_deg: float, center: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Rotates a whole skeleton (list of points) around a center by an angle in degrees."""
    angle_rad = math.radians(angle_deg)
    return [rotate_point(pt, center, angle_rad) for pt in points]


def scale_points(points: List[Tuple[float, float]], scale_factor: float, center: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Scales a list of 2D points relative to a center by a factor."""
    cx, cy = center
    return [(cx + (x - cx) * scale_factor, cy + (y - cy) * scale_factor) for x, y in points]


def mirror_pose(points: List[Tuple[float, float]], center_x: float) -> List[Tuple[float, float]]:
    """
    Mirrors a skeleton horizontally around a vertical line at center_x.
    Performs horizontal mirror followed by anatomical left/right swaps.
    """
    # 1. Flip X coordinates
    flipped = [(2 * center_x - x, y) for x, y in points]
    
    # 2. Perform anatomical left/right swaps to preserve OpenPose correctness
    mirrored = list(flipped)
    for left_idx, right_idx in MIRROR_SWAP_MAP.items():
        # Swap values
        mirrored[left_idx] = flipped[right_idx]
        mirrored[right_idx] = flipped[left_idx]
        
    return mirrored


def adjust_proportions(
    points: List[Tuple[float, float]],
    height_factor: float,
    limb_factor: float
) -> List[Tuple[float, float]]:
    """
    Adjusts the skeleton height and limb proportions hierarchically relative to the Neck (index 1).
    This keeps the pose anatomical and avoids joint disconnection.
    """
    if not points or len(points) < 18:
        return points

    # Use Neck (index 1) as the absolute anchor
    neck = points[1]
    nx, ny = neck
    
    # Make a copy to write to
    adjusted = list(points)
    
    # 1. Apply Height Scale relative to Neck Y coordinate
    # (Mainly scales the vertical distance of torso and legs relative to neck)
    for i in range(len(points)):
        if i == 1:  # Skip neck anchor
            continue
        px, py = points[i]
        # Torso and lower body get scaled vertically
        dy = py - ny
        dx = px - nx
        
        # Apply scaling relative to neck
        # For eyes/ears/nose, let's keep them proportional but not stretched too much
        if i in [0, 14, 15, 16, 17]:
            adjusted[i] = (nx + dx, ny + dy * (1.0 + (height_factor - 1.0) * 0.5))
        else:
            adjusted[i] = (nx + dx, ny + dy * height_factor)
            
    # 2. Adjust limbs (Arms and Legs) hierarchically from their parent anchors
    # We reconstruct the skeleton arms and legs using vectors and apply limb_factor
    
    # Helper to scale segment: parent -> child -> grandchild
    def scale_limb(parent_idx: int, mid_idx: int, end_idx: int, factor: float):
        p = adjusted[parent_idx]
        m = adjusted[mid_idx]
        e = adjusted[end_idx]
        
        # parent -> mid
        v_mid = (m[0] - p[0], m[1] - p[1])
        m_new = (p[0] + v_mid[0] * factor, p[1] + v_mid[1] * factor)
        adjusted[mid_idx] = m_new
        
        # mid -> end
        v_end = (e[0] - m[0], e[1] - m[1])
        e_new = (m_new[0] + v_end[0] * factor, m_new[1] + v_end[1] * factor)
        adjusted[end_idx] = e_new

    # Scale Right Arm: Shoulder (2) -> Elbow (3) -> Wrist (4)
    scale_limb(2, 3, 4, limb_factor)
    # Scale Left Arm: Shoulder (5) -> Elbow (6) -> Wrist (7)
    scale_limb(5, 6, 7, limb_factor)
    
    # Scale Right Leg: Hip (8) -> Knee (9) -> Ankle (10)
    scale_limb(8, 9, 10, limb_factor)
    # Scale Left Leg: Hip (11) -> Knee (12) -> Ankle (13)
    scale_limb(11, 12, 13, limb_factor)
    
    # Head and facial features are kept close to nose
    nose = adjusted[0]
    for eye_idx in [14, 15]:
        v = (adjusted[eye_idx][0] - nose[0], adjusted[eye_idx][1] - nose[1])
        adjusted[eye_idx] = (nose[0] + v[0], nose[1] + v[1])
        
    for ear_idx, eye_idx in [(16, 14), (17, 15)]:
        eye = adjusted[eye_idx]
        v = (adjusted[ear_idx][0] - eye[0], adjusted[ear_idx][1] - eye[1])
        adjusted[ear_idx] = (eye[0] + v[0], eye[1] + v[1])

    return adjusted


def find_closest_keypoint(
    skeletons: List[Dict],
    mouse_x: float,
    mouse_y: float,
    threshold: float = 15.0
) -> Tuple[int, int]:
    """
    Finds the closest keypoint among all visible and unlocked skeletons.
    Returns:
        (skeleton_index, keypoint_index) or (-1, -1) if none within threshold.
    """
    closest_dist = float('inf')
    found_sk_idx = -1
    found_kp_idx = -1
    
    for sk_idx, sk in enumerate(skeletons):
        if sk.get("locked", False) or not sk.get("visible", True):
            continue
        
        points = sk.get("points", [])
        for kp_idx, (x, y) in enumerate(points):
            dist = calculate_distance((x, y), (mouse_x, mouse_y))
            if dist < threshold and dist < closest_dist:
                closest_dist = dist
                found_sk_idx = sk_idx
                found_kp_idx = kp_idx
                
    return found_sk_idx, found_kp_idx


def find_closest_torso(
    skeletons: List[Dict],
    mouse_x: float,
    mouse_y: float,
    threshold: float = 20.0
) -> int:
    """
    Finds the closest person to translate based on click proximity to the main torso (Neck, index 1).
    Returns skeleton_index, or -1 if none within threshold.
    """
    closest_dist = float('inf')
    found_sk_idx = -1
    
    for sk_idx, sk in enumerate(skeletons):
        if sk.get("locked", False) or not sk.get("visible", True):
            continue
            
        points = sk.get("points", [])
        if len(points) > 1:
            neck = points[1]
            dist = calculate_distance(neck, (mouse_x, mouse_y))
            if dist < threshold and dist < closest_dist:
                closest_dist = dist
                found_sk_idx = sk_idx
                
    return found_sk_idx
