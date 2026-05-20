"""
Preset pose coordinate definitions for single and double person skeletons.
All coordinates are designed for a standard 512x512 canvas coordinates space,
and can be offset or transformed as needed.
Contains a high-fidelity Forward Kinematics (FK) engine to procedural-generate 105 diverse poses.
"""
import math
from typing import List, Tuple, Dict, Any

# Connection definitions (limbs) for OpenPose 18 keypoints format
# Total 19 bones
POSE_CONNECTIONS = [
    (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
    (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
    (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),
    (16, 2), (17, 5)
]

# Color mapping for the 19 limbs (RGB values)
# Perfect OpenPose standard colors
CONNECTION_COLORS = [
    (255, 0, 85), (255, 170, 0), (255, 0, 0), (255, 85, 0), (255, 255, 0), (170, 255, 0),
    (85, 255, 0), (0, 255, 0), (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255),
    (0, 85, 255), (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170), (170, 0, 255)
]

# Keypoint joint colors (RGB values)
JOINT_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0),
    (0, 255, 0), (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)
]

# Localized Display Names for Poses
POSE_DISPLAY_NAMES = {
    # 1. YOGA (20)
    "yoga_tree": {"zh_TW": "瑜珈 - 樹式", "en_US": "Yoga - Tree Pose"},
    "yoga_warrior1": {"zh_TW": "瑜珈 - 戰士一式", "en_US": "Yoga - Warrior I"},
    "yoga_warrior2": {"zh_TW": "瑜珈 - 戰士二式", "en_US": "Yoga - Warrior II"},
    "yoga_warrior3": {"zh_TW": "瑜珈 - 戰士三式", "en_US": "Yoga - Warrior III"},
    "yoga_downward_dog": {"zh_TW": "瑜珈 - 下犬式", "en_US": "Yoga - Downward Dog"},
    "yoga_cobra": {"zh_TW": "瑜珈 - 眼鏡蛇式", "en_US": "Yoga - Cobra Pose"},
    "yoga_triangle": {"zh_TW": "瑜珈 - 三角式", "en_US": "Yoga - Triangle Pose"},
    "yoga_bridge": {"zh_TW": "瑜珈 - 橋式", "en_US": "Yoga - Bridge Pose"},
    "yoga_lotus": {"zh_TW": "瑜珈 - 蓮花坐姿", "en_US": "Yoga - Lotus Pose"},
    "yoga_boat": {"zh_TW": "瑜珈 - 船式", "en_US": "Yoga - Boat Pose"},
    "yoga_half_moon": {"zh_TW": "瑜珈 - 半月式", "en_US": "Yoga - Half Moon Pose"},
    "yoga_crow": {"zh_TW": "瑜珈 - 烏鴉式", "en_US": "Yoga - Crow Pose"},
    "yoga_chair": {"zh_TW": "瑜珈 - 幻椅式", "en_US": "Yoga - Chair Pose"},
    "yoga_camel": {"zh_TW": "瑜珈 - 駱駝式", "en_US": "Yoga - Camel Pose"},
    "yoga_child": {"zh_TW": "瑜珈 - 嬰兒式", "en_US": "Yoga - Child's Pose"},
    "yoga_plank": {"zh_TW": "瑜珈 - 側平板式", "en_US": "Yoga - Side Plank"},
    "yoga_eagle": {"zh_TW": "瑜珈 - 鷹式", "en_US": "Yoga - Eagle Pose"},
    "yoga_dancer": {"zh_TW": "瑜珈 - 舞王式", "en_US": "Yoga - Dancer's Pose"},
    "yoga_shoulder_stand": {"zh_TW": "瑜珈 - 肩立式", "en_US": "Yoga - Shoulder Stand"},
    "yoga_corpse": {"zh_TW": "瑜珈 - 攤屍式 (大休息)", "en_US": "Yoga - Corpse Pose"},

    # 2. TAI CHI (15)
    "taichi_opening": {"zh_TW": "太極 - 起勢", "en_US": "Tai Chi - Opening"},
    "taichi_crane": {"zh_TW": "太極 - 白鶴亮翅", "en_US": "Tai Chi - White Crane Spreads Wings"},
    "taichi_whip": {"zh_TW": "太極 - 單鞭", "en_US": "Tai Chi - Single Whip"},
    "taichi_lute": {"zh_TW": "太極 - 手揮琵琶", "en_US": "Tai Chi - Play the Lute"},
    "taichi_brush_knee": {"zh_TW": "太極 - 摟膝拗步", "en_US": "Tai Chi - Brush Knee"},
    "taichi_bird_tail": {"zh_TW": "太極 - 攬雀尾", "en_US": "Tai Chi - Grasp Bird's Tail"},
    "taichi_clouds": {"zh_TW": "太極 - 雲手", "en_US": "Tai Chi - Wave Hands like Clouds"},
    "taichi_rooster": {"zh_TW": "太極 - 金雞獨立", "en_US": "Tai Chi - Golden Rooster Stands on One Leg"},
    "taichi_repulse_monkey": {"zh_TW": "太極 - 倒捲肱", "en_US": "Tai Chi - Step Back & Repulse Monkey"},
    "taichi_needle": {"zh_TW": "太極 - 海底針", "en_US": "Tai Chi - Needle at Sea Bottom"},
    "taichi_fan": {"zh_TW": "太極 - 閃通背", "en_US": "Tai Chi - Fan Through Back"},
    "taichi_parry_punch": {"zh_TW": "太極 - 搬攔捶", "en_US": "Tai Chi - Deflect, Parry & Punch"},
    "taichi_close": {"zh_TW": "太極 - 如封似閉", "en_US": "Tai Chi - Apparent Close"},
    "taichi_crossing": {"zh_TW": "太極 - 十字手", "en_US": "Tai Chi - Crossing Hands"},
    "taichi_closing": {"zh_TW": "太極 - 收勢", "en_US": "Tai Chi - Closing"},

    # 3. DANCING (15)
    "dance_arabesque": {"zh_TW": "舞蹈 - 芭蕾阿拉貝斯克", "en_US": "Dance - Ballet Arabesque"},
    "dance_pirouette": {"zh_TW": "舞蹈 - 芭蕾旋轉", "en_US": "Dance - Ballet Pirouette"},
    "dance_freeze": {"zh_TW": "舞蹈 - 地板舞倒立定格", "en_US": "Dance - Breakdance Freeze"},
    "dance_salsa": {"zh_TW": "舞蹈 - 騷莎滑步", "en_US": "Dance - Salsa Step"},
    "dance_hiphop": {"zh_TW": "舞蹈 - 嘻哈巨星半蹲", "en_US": "Dance - Hiphop Stance"},
    "dance_waltz": {"zh_TW": "舞蹈 - 華爾滋展臂", "en_US": "Dance - Waltz Frame"},
    "dance_disco": {"zh_TW": "舞蹈 - 迪斯可經典指天", "en_US": "Dance - Disco Point"},
    "dance_flamenco": {"zh_TW": "舞蹈 - 佛朗明哥裙擺", "en_US": "Dance - Flamenco Stance"},
    "dance_contemporary": {"zh_TW": "舞蹈 - 現代舞躍動延展", "en_US": "Dance - Contemporary Reach"},
    "dance_jazz": {"zh_TW": "舞蹈 - 爵士手滑步", "en_US": "Dance - Jazz Frame"},
    "dance_moonwalk": {"zh_TW": "舞蹈 - 太空步定格", "en_US": "Dance - Moonwalk Stance"},
    "dance_rock": {"zh_TW": "舞蹈 - 搖滾歌手激情傾斜", "en_US": "Dance - Rock Pose"},
    "dance_dab": {"zh_TW": "舞蹈 - 點水炫耀 Dab", "en_US": "Dance - Dab Pose"},
    "dance_twist": {"zh_TW": "舞蹈 - 復古扭扭舞姿", "en_US": "Dance - Twist Step"},
    "dance_robot": {"zh_TW": "舞蹈 - 機械機械定格", "en_US": "Dance - Robot Pose"},

    # 4. SPORTS & ATHLETICS (20)
    "sport_sprint_start": {"zh_TW": "運動 - 起跑準備蹲姿", "en_US": "Sport - Sprint Block Start"},
    "sport_sprint": {"zh_TW": "運動 - 百米奔跑衝刺", "en_US": "Sport - Sprinting Run"},
    "sport_long_jump": {"zh_TW": "運動 - 跳遠空中收腹", "en_US": "Sport - Long Jump Flight"},
    "sport_javelin": {"zh_TW": "運動 - 標槍向後拉弓", "en_US": "Sport - Javelin Throw Prep"},
    "sport_basketball": {"zh_TW": "運動 - 籃球起跳投籃", "en_US": "Sport - Basketball Jump Shot"},
    "sport_soccer": {"zh_TW": "運動 - 足球凌空抽射", "en_US": "Sport - Soccer Volley Kick"},
    "sport_tennis": {"zh_TW": "運動 - 網球過頂發球", "en_US": "Sport - Tennis Serve"},
    "sport_swim": {"zh_TW": "運動 - 游泳起跳台預備", "en_US": "Sport - Swimmer Dive Block"},
    "sport_golf": {"zh_TW": "運動 - 高爾夫收桿定格", "en_US": "Sport - Golf Follow-Through"},
    "sport_boxing_jab": {"zh_TW": "運動 - 拳擊前手直拳", "en_US": "Sport - Boxing Jab"},
    "sport_boxing_guard": {"zh_TW": "運動 - 拳擊雙手抱架", "en_US": "Sport - Boxing Guard"},
    "sport_weight": {"zh_TW": "運動 - 舉重槓鈴過頂", "en_US": "Sport - Weightlifting Clean & Jerk"},
    "sport_archery": {"zh_TW": "運動 - 射箭開弓瞄準", "en_US": "Sport - Archery Full Draw"},
    "sport_skate": {"zh_TW": "運動 - 滑板空中抓板", "en_US": "Sport - Skateboarding Air Grab"},
    "sport_baseball_pitch": {"zh_TW": "運動 - 棒球投手抬腿", "en_US": "Sport - Baseball Pitcher Windup"},
    "sport_baseball_bat": {"zh_TW": "運動 - 棒球擊球揮棒", "en_US": "Sport - Baseball Batter Swing"},
    "sport_karate": {"zh_TW": "運動 - 空手道高側踢", "en_US": "Sport - Karate Side Kick"},
    "sport_gymnast": {"zh_TW": "運動 - 體操騰空劈腿", "en_US": "Sport - Gymnast Aerial Split"},
    "sport_volley": {"zh_TW": "運動 - 排球起跳扣殺", "en_US": "Sport - Volleyball Spike"},
    "sport_ice": {"zh_TW": "運動 - 花滑燕式巡航", "en_US": "Sport - Figure Skating Spiral"},

    # 5. DAILY & ACTIONS (20)
    "daily_stand": {"zh_TW": "日常 - 標準站立", "en_US": "Daily - Standard Stand"},
    "daily_wave": {"zh_TW": "日常 - 揮手打招呼", "en_US": "Daily - Friendly Wave"},
    "daily_sit": {"zh_TW": "日常 - 盤腿而坐", "en_US": "Daily - Sitting Crossed Legs"},
    "daily_phone": {"zh_TW": "日常 - 低頭划手機", "en_US": "Daily - Browsing Phone"},
    "daily_bow": {"zh_TW": "日常 - 鞠躬謝幕", "en_US": "Daily - Bowing"},
    "daily_kneel": {"zh_TW": "日常 - 跪姿祈禱", "en_US": "Daily - Kneeling Prayer"},
    "daily_think": {"zh_TW": "日常 - 托腮托腮沉思", "en_US": "Daily - Thinking"},
    "daily_walk": {"zh_TW": "日常 - 邁步散步", "en_US": "Daily - Casual Walk"},
    "daily_run": {"zh_TW": "日常 - 慢跑健身", "en_US": "Daily - Jogging"},
    "daily_umbrella": {"zh_TW": "日常 - 單手撐傘行走", "en_US": "Daily - Holding Umbrella Walk"},
    "daily_salute": {"zh_TW": "日常 - 軍禮敬禮", "en_US": "Daily - Saluting"},
    "daily_shrug": {"zh_TW": "日常 - 雙手攤開聳肩", "en_US": "Daily - Shrugging Shoulder"},
    "daily_point": {"zh_TW": "日常 - 手指前方引路", "en_US": "Daily - Pointing Forward"},
    "daily_camera": {"zh_TW": "日常 - 手持單眼拍照", "en_US": "Daily - Taking Photo"},
    "daily_sleep": {"zh_TW": "日常 - 臥床側躺入睡", "en_US": "Daily - Side Sleeping"},
    "daily_read": {"zh_TW": "日常 - 雙手持書閱讀", "en_US": "Daily - Reading Book"},
    "daily_clap": {"zh_TW": "日常 - 鼓掌喝采", "en_US": "Daily - Clapping Hands"},
    "daily_look_far": {"zh_TW": "日常 - 遮陽極目遠眺", "en_US": "Daily - Looking into Distance"},
    "daily_defend": {"zh_TW": "日常 - 雙臂交叉格擋", "en_US": "Daily - Arm Cross Guard"},
    "daily_victory": {"zh_TW": "日常 - 比雙勝利剪刀手", "en_US": "Daily - Double Victory Pose"},

    # 6. DOUBLE POSES (15)
    "double_shake": {"zh_TW": "雙人 - 握手合影", "en_US": "Double - Classic Handshake"},
    "double_hug": {"zh_TW": "雙人 - 溫暖擁抱", "en_US": "Double - Warm Hug"},
    "double_fight": {"zh_TW": "雙人 - 近身格鬥", "en_US": "Double - Action Combat"},
    "double_walk": {"zh_TW": "雙人 - 並肩散步", "en_US": "Double - Casual Walk Side-by-side"},
    "double_highfive": {"zh_TW": "雙人 - 跳躍擊掌", "en_US": "Double - High Five"},
    "double_proposal": {"zh_TW": "雙人 - 單膝下跪求婚", "en_US": "Double - Kneeling Proposal"},
    "double_tango": {"zh_TW": "雙人 - 激情探戈下腰", "en_US": "Double - Tango Dip"},
    "double_carry": {"zh_TW": "雙人 - 背人嬉戲", "en_US": "Double - Piggyback Carry"},
    "double_backtoback": {"zh_TW": "雙人 - 背靠背坐", "en_US": "Double - Sitting Back-to-Back"},
    "double_whisper": {"zh_TW": "雙人 - 貼耳悄悄話", "en_US": "Double - Whispering Secrets"},
    "double_heart": {"zh_TW": "雙人 - 合力比愛心", "en_US": "Double - Dynamic Love Heart"},
    "double_yoga_tree": {"zh_TW": "雙人瑜珈 - 合作雙人樹式", "en_US": "Partner Yoga - Double Tree"},
    "double_yoga_dog": {"zh_TW": "雙人瑜珈 - 上下疊羅漢犬式", "en_US": "Partner Yoga - Double Stack Dog"},
    "double_yoga_warrior": {"zh_TW": "雙人瑜珈 - 面對面手拉手戰士", "en_US": "Partner Yoga - Face-to-Face Warrior"},
    "double_yoga_acro": {"zh_TW": "雙人瑜珈 - 空中飛鳥支撐", "en_US": "Partner Yoga - Acro Flying Bird"}
}


def _rotate_vector(x: float, y: float, angle_deg: float) -> Tuple[float, float]:
    """Helper to rotate a 2D vector by angle in degrees."""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


def generate_fk_pose(
    tx: float = 256.0, ty: float = 150.0,
    torso_angle: float = 0.0,
    r_shoulder: float = 0.0, r_elbow: float = 0.0,
    l_shoulder: float = 0.0, l_elbow: float = 0.0,
    r_hip: float = 0.0, r_knee: float = 0.0,
    l_hip: float = 0.0, l_knee: float = 0.0,
    head: float = 0.0,
    global_rot: float = 0.0
) -> List[Tuple[float, float]]:
    """
    Procedurally generates an 18-joint human pose using Forward Kinematics (FK).
    All angles are defined in degrees:
      - torso_angle: tilt of spine (0 is down)
      - shoulder angles: relative to torso angle (0 is down)
      - elbow angles: relative to shoulder angle (0 is straight arm)
      - hip angles: relative to torso angle (0 is down)
      - knee angles: relative to hip angle (0 is straight leg)
      - head angle: relative to torso angle (0 is straight up)
      - global_rot: final global rotation of the whole skeleton around the Neck.
    """
    torso_rad = math.radians(torso_angle)
    
    # 1. Neck (Anchor)
    neck = (tx, ty)
    
    # 2. Torso (Neck -> Pelvis)
    pelvis_x = tx + 100.0 * math.sin(torso_rad)
    pelvis_y = ty + 100.0 * math.cos(torso_rad)
    pelvis = (pelvis_x, pelvis_y)
    
    # 3. Shoulders (horizontal relative to torso)
    r_sh_dx, r_sh_dy = _rotate_vector(-30.0, 0.0, torso_angle)
    r_shoulder_pt = (tx + r_sh_dx, ty + r_sh_dy)
    
    l_sh_dx, l_sh_dy = _rotate_vector(30.0, 0.0, torso_angle)
    l_shoulder_pt = (tx + l_sh_dx, ty + l_sh_dy)
    
    # 4. Right Arm (Shoulder -> Elbow -> Wrist)
    r_arm_angle = torso_angle + r_shoulder
    r_elbow_dx = 55.0 * math.sin(math.radians(r_arm_angle))
    r_elbow_dy = 55.0 * math.cos(math.radians(r_arm_angle))
    r_elbow_pt = (r_shoulder_pt[0] + r_elbow_dx, r_shoulder_pt[1] + r_elbow_dy)
    
    r_forearm_angle = r_arm_angle + r_elbow
    r_wrist_dx = 55.0 * math.sin(math.radians(r_forearm_angle))
    r_wrist_dy = 55.0 * math.cos(math.radians(r_forearm_angle))
    r_wrist_pt = (r_elbow_pt[0] + r_wrist_dx, r_elbow_pt[1] + r_wrist_dy)
    
    # 5. Left Arm (Shoulder -> Elbow -> Wrist)
    l_arm_angle = torso_angle + l_shoulder
    l_elbow_dx = 55.0 * math.sin(math.radians(l_arm_angle))
    l_elbow_dy = 55.0 * math.cos(math.radians(l_arm_angle))
    l_elbow_pt = (l_shoulder_pt[0] + l_elbow_dx, l_shoulder_pt[1] + l_elbow_dy)
    
    l_forearm_angle = l_arm_angle + l_elbow
    l_wrist_dx = 55.0 * math.sin(math.radians(l_forearm_angle))
    l_wrist_dy = 55.0 * math.cos(math.radians(l_forearm_angle))
    l_wrist_pt = (l_elbow_pt[0] + l_wrist_dx, l_elbow_pt[1] + l_wrist_dy)
    
    # 6. Hips (Pelvis Center -> RHip/LHip)
    r_hip_dx, r_hip_dy = _rotate_vector(-20.0, 0.0, torso_angle)
    r_hip_pt = (pelvis_x + r_hip_dx, pelvis_y + r_hip_dy)
    
    l_hip_dx, l_hip_dy = _rotate_vector(20.0, 0.0, torso_angle)
    l_hip_pt = (pelvis_x + l_hip_dx, pelvis_y + l_hip_dy)
    
    # 7. Right Leg (Hip -> Knee -> Ankle)
    r_thigh_angle = torso_angle + r_hip
    r_knee_dx = 70.0 * math.sin(math.radians(r_thigh_angle))
    r_knee_dy = 70.0 * math.cos(math.radians(r_thigh_angle))
    r_knee_pt = (r_hip_pt[0] + r_knee_dx, r_hip_pt[1] + r_knee_dy)
    
    r_calf_angle = r_thigh_angle + r_knee
    r_ankle_dx = 70.0 * math.sin(math.radians(r_calf_angle))
    r_ankle_dy = 70.0 * math.cos(math.radians(r_calf_angle))
    r_ankle_pt = (r_knee_pt[0] + r_ankle_dx, r_knee_pt[1] + r_ankle_dy)
    
    # 8. Left Leg (Hip -> Knee -> Ankle)
    l_thigh_angle = torso_angle + l_hip
    l_knee_dx = 70.0 * math.sin(math.radians(l_thigh_angle))
    l_knee_dy = 70.0 * math.cos(math.radians(l_thigh_angle))
    l_knee_pt = (l_hip_pt[0] + l_knee_dx, l_hip_pt[1] + l_knee_dy)
    
    l_calf_angle = l_thigh_angle + l_knee
    l_ankle_dx = 70.0 * math.sin(math.radians(l_calf_angle))
    l_ankle_dy = 70.0 * math.cos(math.radians(l_calf_angle))
    l_ankle_pt = (l_knee_pt[0] + l_ankle_dx, l_knee_pt[1] + l_ankle_dy)
    
    # 9. Head and Facial Features
    head_phi = torso_angle + head
    nose_dx, nose_dy = _rotate_vector(0.0, -30.0, head_phi)
    nose_pt = (tx + nose_dx, ty + nose_dy)
    
    r_eye_dx, r_eye_dy = _rotate_vector(-6.0, -8.0, head_phi)
    r_eye_pt = (nose_pt[0] + r_eye_dx, nose_pt[1] + r_eye_dy)
    
    l_eye_dx, l_eye_dy = _rotate_vector(6.0, -8.0, head_phi)
    l_eye_pt = (nose_pt[0] + l_eye_dx, nose_pt[1] + l_eye_dy)
    
    r_ear_dx, r_ear_dy = _rotate_vector(-8.0, 3.0, head_phi)
    r_ear_pt = (r_eye_pt[0] + r_ear_dx, r_eye_pt[1] + r_ear_dy)
    
    l_ear_dx, l_ear_dy = _rotate_vector(8.0, 3.0, head_phi)
    l_ear_pt = (l_eye_pt[0] + l_ear_dx, l_eye_pt[1] + l_ear_dy)
    
    points = [
        nose_pt,       # 0: Nose
        neck,          # 1: Neck
        r_shoulder_pt, # 2: RShoulder
        r_elbow_pt,    # 3: RElbow
        r_wrist_pt,    # 4: RWrist
        l_shoulder_pt, # 5: LShoulder
        l_elbow_pt,    # 6: LElbow
        l_wrist_pt,    # 7: LWrist
        r_hip_pt,      # 8: RHip
        r_knee_pt,     # 9: RKnee
        r_ankle_pt,    # 10: RAnkle
        l_hip_pt,      # 11: LHip
        l_knee_pt,     # 12: LKnee
        l_ankle_pt,    # 13: LAnkle
        r_eye_pt,      # 14: REye
        l_eye_pt,      # 15: LEye
        r_ear_pt,      # 16: REar
        l_ear_pt       # 17: LEar
    ]
    
    # Apply global rotation around the Neck pivot
    if global_rot != 0.0:
        rot_pts = []
        for x, y in points:
            dx = x - tx
            dy = y - ty
            rx, ry = _rotate_vector(dx, dy, global_rot)
            rot_pts.append((tx + rx, ty + ry))
        return rot_pts
        
    return points


# Procedural Pose Parameter Database (torso, r_sh, r_el, l_sh, l_el, r_hip, r_kn, l_hip, l_kn, head, global_rot)
SINGLE_POSE_PARAMS = {
    # === YOGA POSES (20) ===
    # Tree Pose: Balance on left, right foot nested on thigh, hands high together
    "yoga_tree": (0.0, 160.0, 30.0, -160.0, -30.0, 45.0, 135.0, 0.0, 0.0, 0.0, 0.0),
    # Warrior I: Stretched stance, arms vertically up
    "yoga_warrior1": (10.0, 185.0, 0.0, -185.0, 0.0, 35.0, -75.0, -40.0, 10.0, 0.0, 0.0),
    # Warrior II: Stretched stance, arms extended horizontally
    "yoga_warrior2": (0.0, -90.0, 0.0, 90.0, 0.0, 45.0, -80.0, -45.0, 15.0, 90.0, 0.0),
    # Warrior III: Standing horizontal scale
    "yoga_warrior3": (-90.0, -180.0, 0.0, -180.0, 0.0, 90.0, 0.0, -90.0, 0.0, 10.0, 0.0),
    # Downward Dog: Inverted V
    "yoga_downward_dog": (35.0, -150.0, 0.0, -150.0, 0.0, 100.0, 0.0, 100.0, 0.0, -10.0, -120.0),
    # Cobra Pose: Torso curved up, hips on ground
    "yoga_cobra": (-60.0, 40.0, 70.0, 40.0, 70.0, 90.0, 0.0, 90.0, 0.0, -30.0, 90.0),
    # Triangle Pose: Sideways bend, arms vertical, feet spread
    "yoga_triangle": (0.0, 180.0, 0.0, 0.0, 0.0, 30.0, 0.0, -30.0, 0.0, 90.0, 90.0),
    # Bridge Pose: Arch shape, hips raised high
    "yoga_bridge": (0.0, -20.0, 20.0, -20.0, 20.0, 80.0, -100.0, 80.0, -100.0, 0.0, 180.0),
    # Lotus Pose: Floor crossed legs meditation
    "yoga_lotus": (0.0, 30.0, 110.0, -30.0, -110.0, 75.0, 130.0, -75.0, -130.0, 0.0, 0.0),
    # Boat Pose: V-sit balance on floor
    "yoga_boat": (35.0, -85.0, 0.0, 85.0, 0.0, -45.0, -10.0, -45.0, -10.0, -10.0, 30.0),
    # Half Moon: Balance sideways on right hand & leg, left arm & leg horizontal
    "yoga_half_moon": (-90.0, -90.0, 0.0, 90.0, 0.0, 0.0, 0.0, -90.0, 0.0, 90.0, 90.0),
    # Crow Pose: Arm balance crouching high
    "yoga_crow": (45.0, -35.0, 110.0, -35.0, 110.0, 95.0, 125.0, 95.0, 125.0, -20.0, -75.0),
    # Chair Pose: Squatting standing posture, arms high
    "yoga_chair": (30.0, 150.0, 10.0, -150.0, -10.0, 50.0, -90.0, 50.0, -90.0, 0.0, 0.0),
    # Camel Pose: Standing kneel, arching backward to touch heels
    "yoga_camel": (-45.0, 45.0, 10.0, -45.0, -10.0, 10.0, -90.0, 10.0, -90.0, -40.0, 0.0),
    # Child's Pose: Crouching over knees, face on ground, arms extended forward
    "yoga_child": (90.0, 180.0, 0.0, 180.0, 0.0, 135.0, -135.0, 135.0, -135.0, 10.0, -80.0),
    # Side Plank: Pushup sideways on right hand, body straight line
    "yoga_plank": (90.0, 90.0, 0.0, -90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -90.0),
    # Eagle Pose: Double wrapped limbs standing
    "yoga_eagle": (15.0, 45.0, 90.0, -45.0, -90.0, 40.0, 100.0, 15.0, 30.0, 0.0, 0.0),
    # Dancer's Pose: Balance on one leg, grabbing back foot raised high
    "yoga_dancer": (35.0, -80.0, 0.0, 135.0, 90.0, 10.0, 20.0, -120.0, 120.0, 20.0, 0.0),
    # Shoulder Stand: Straight vertical upside down, supported on shoulders
    "yoga_shoulder_stand": (0.0, 45.0, 90.0, -45.0, -90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 180.0),
    # Corpse Pose: Flat lying on back, arms relaxed at sides
    "yoga_corpse": (0.0, 10.0, 0.0, -10.0, 0.0, 5.0, 0.0, -5.0, 0.0, 0.0, 90.0),

    # === TAI CHI POSES (15) ===
    "taichi_opening": (5.0, -70.0, 20.0, 70.0, -20.0, 15.0, 15.0, 15.0, 15.0, 0.0, 0.0),
    "taichi_crane": (0.0, -120.0, -30.0, 55.0, 30.0, 15.0, 20.0, -45.0, 60.0, 0.0, 0.0),
    "taichi_whip": (5.0, -100.0, -10.0, 80.0, -30.0, 35.0, -45.0, -35.0, 45.0, 90.0, 0.0),
    "taichi_lute": (10.0, -45.0, 40.0, 30.0, -45.0, 20.0, 40.0, -30.0, 15.0, 45.0, 0.0),
    "taichi_brush_knee": (15.0, -80.0, 30.0, 45.0, -30.0, 30.0, -60.0, -30.0, 20.0, 45.0, 0.0),
    "taichi_bird_tail": (10.0, -65.0, 55.0, 70.0, -45.0, 35.0, -50.0, -25.0, 20.0, 30.0, 0.0),
    "taichi_clouds": (5.0, -45.0, 60.0, 45.0, -60.0, 20.0, 15.0, 20.0, 15.0, 45.0, 0.0),
    "taichi_rooster": (0.0, -135.0, -45.0, 45.0, 90.0, 0.0, 0.0, -90.0, 110.0, 0.0, 0.0),
    "taichi_repulse_monkey": (-10.0, 80.0, -20.0, -80.0, 30.0, -30.0, 30.0, 40.0, -20.0, -30.0, 0.0),
    "taichi_needle": (45.0, 35.0, 45.0, -65.0, -30.0, 45.0, 30.0, -15.0, 90.0, -20.0, 0.0),
    "taichi_fan": (10.0, -120.0, 15.0, 120.0, -15.0, 35.0, -45.0, -25.0, 30.0, 60.0, 0.0),
    "taichi_parry_punch": (15.0, -45.0, 90.0, 80.0, -30.0, 45.0, -60.0, -35.0, 15.0, 45.0, 0.0),
    "taichi_close": (5.0, -65.0, 45.0, 65.0, -45.0, 25.0, -20.0, 25.0, -20.0, 0.0, 0.0),
    "taichi_crossing": (0.0, -30.0, 75.0, 30.0, -75.0, 15.0, 15.0, 15.0, 15.0, 0.0, 0.0),
    "taichi_closing": (0.0, 15.0, 5.0, -15.0, -5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),

    # === DANCING POSES (15) ===
    "dance_arabesque": (-30.0, -90.0, 10.0, 90.0, -10.0, -80.0, 10.0, 45.0, 0.0, 20.0, 0.0),
    "dance_pirouette": (0.0, 110.0, 90.0, -110.0, -90.0, 45.0, 120.0, 0.0, 0.0, -30.0, 0.0),
    "dance_freeze": (45.0, 110.0, 90.0, -60.0, 90.0, 60.0, 90.0, -45.0, 45.0, 0.0, 150.0),
    "dance_salsa": (10.0, -45.0, 45.0, 80.0, -30.0, 35.0, -45.0, -25.0, 10.0, 45.0, 0.0),
    "dance_hiphop": (30.0, -45.0, 90.0, 45.0, -90.0, 60.0, -90.0, 40.0, -80.0, -10.0, 0.0),
    "dance_waltz": (5.0, -100.0, 30.0, 100.0, -30.0, 20.0, -10.0, -20.0, 10.0, -30.0, 0.0),
    "dance_disco": (5.0, -155.0, -10.0, 45.0, 90.0, 30.0, -20.0, -35.0, 10.0, -45.0, 0.0),
    "dance_flamenco": (-15.0, -160.0, -80.0, 75.0, 45.0, 15.0, 30.0, -25.0, 0.0, -20.0, 0.0),
    "dance_contemporary": (-45.0, -180.0, 0.0, 90.0, 90.0, -110.0, 20.0, 45.0, 15.0, -30.0, 0.0),
    "dance_jazz": (15.0, -80.0, 95.0, 80.0, -95.0, 40.0, -60.0, -10.0, 20.0, 15.0, 0.0),
    "dance_moonwalk": (15.0, 15.0, 20.0, -15.0, -20.0, 40.0, -40.0, -20.0, 90.0, 0.0, 0.0),
    "dance_rock": (-25.0, -145.0, 30.0, -45.0, 90.0, 15.0, 20.0, -30.0, 45.0, -45.0, 0.0),
    "dance_dab": (45.0, 145.0, 10.0, 135.0, 0.0, 25.0, -10.0, -25.0, 10.0, -90.0, 0.0),
    "dance_twist": (10.0, 35.0, 60.0, -35.0, -60.0, 45.0, -90.0, -45.0, 90.0, 0.0, 0.0),
    "dance_robot": (0.0, -90.0, 90.0, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 45.0, 0.0),

    # === SPORTS & ATHLETICS (20) ===
    "sport_sprint_start": (75.0, -45.0, 90.0, 45.0, -90.0, 90.0, -90.0, 65.0, -75.0, -45.0, 0.0),
    "sport_sprint": (35.0, -80.0, 90.0, 80.0, -90.0, -45.0, 90.0, 65.0, -45.0, 15.0, 0.0),
    "sport_long_jump": (45.0, -165.0, -20.0, 165.0, 20.0, -90.0, -90.0, -90.0, -90.0, 20.0, 0.0),
    "sport_javelin": (-30.0, 135.0, -10.0, -135.0, -90.0, -35.0, 10.0, 45.0, -60.0, -30.0, 0.0),
    "sport_basketball": (15.0, 165.0, 45.0, -165.0, -45.0, 45.0, -70.0, 30.0, -40.0, -30.0, 0.0),
    "sport_soccer": (20.0, -45.0, 30.0, 45.0, -30.0, -90.0, 95.0, 45.0, -45.0, 15.0, 0.0),
    "sport_tennis": (-25.0, 175.0, 15.0, -110.0, -30.0, 35.0, -45.0, -35.0, 15.0, -45.0, 0.0),
    "sport_swim": (65.0, -170.0, 0.0, 170.0, 0.0, 45.0, -45.0, 45.0, -45.0, -60.0, 0.0),
    "sport_golf": (-15.0, 80.0, 95.0, -120.0, -25.0, 45.0, -20.0, -10.0, 90.0, 90.0, 0.0),
    "sport_boxing_jab": (20.0, 15.0, 90.0, 110.0, 5.0, 45.0, -45.0, -25.0, 10.0, 30.0, 0.0),
    "sport_boxing_guard": (15.0, 110.0, 90.0, -110.0, -90.0, 30.0, -30.0, -20.0, 20.0, 0.0, 0.0),
    "sport_weight": (0.0, 180.0, 0.0, -180.0, 0.0, 45.0, -45.0, 45.0, -45.0, 0.0, 0.0),
    "sport_archery": (0.0, 90.0, 0.0, -90.0, 90.0, 20.0, -10.0, -20.0, 10.0, -90.0, 0.0),
    "sport_skate": (35.0, -135.0, 45.0, 120.0, 30.0, -65.0, 45.0, 45.0, -45.0, 20.0, 0.0),
    "sport_baseball_pitch": (-10.0, 110.0, 45.0, -45.0, -90.0, 0.0, 0.0, -110.0, 110.0, -45.0, 0.0),
    "sport_baseball_bat": (25.0, -45.0, 95.0, 45.0, -95.0, 45.0, -30.0, -45.0, 15.0, 90.0, 0.0),
    "sport_karate": (0.0, 80.0, 45.0, -80.0, -45.0, 0.0, 0.0, -90.0, 10.0, 90.0, 0.0),
    "sport_gymnast": (0.0, -165.0, 0.0, 165.0, 0.0, -90.0, 0.0, 90.0, 0.0, 0.0, 0.0),
    "sport_volley": (10.0, 175.0, 10.0, 120.0, 60.0, 35.0, -95.0, -15.0, -20.0, -30.0, 0.0),
    "sport_ice": (-45.0, -90.0, 10.0, 90.0, -10.0, -90.0, 10.0, 45.0, 10.0, -20.0, 0.0),

    # === DAILY & ACTIONS (20) ===
    "daily_stand": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    "daily_wave": (0.0, 0.0, 0.0, 135.0, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    "daily_sit": (0.0, 30.0, 110.0, -30.0, -110.0, 75.0, 130.0, -75.0, -130.0, 0.0, 0.0),
    "daily_phone": (25.0, 45.0, 90.0, -45.0, -90.0, 10.0, -10.0, -10.0, 10.0, 35.0, 0.0),
    "daily_bow": (45.0, 15.0, 15.0, -15.0, -15.0, 15.0, -10.0, 15.0, -10.0, 45.0, 0.0),
    "daily_kneel": (0.0, 25.0, 90.0, -25.0, -90.0, 45.0, -95.0, 45.0, -95.0, 20.0, 0.0),
    "daily_think": (20.0, 25.0, 90.0, -45.0, -110.0, 45.0, -45.0, 45.0, -45.0, 15.0, 0.0),
    "daily_walk": (5.0, -20.0, 20.0, 20.0, -20.0, 25.0, -10.0, -20.0, 30.0, 0.0, 0.0),
    "daily_run": (25.0, -60.0, 90.0, 60.0, -90.0, -30.0, 90.0, 50.0, -40.0, 10.0, 0.0),
    "daily_umbrella": (5.0, -15.0, 10.0, 160.0, 20.0, 15.0, -5.0, -15.0, 10.0, 0.0, 0.0),
    "daily_salute": (0.0, 0.0, 0.0, 110.0, -135.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    "daily_shrug": (0.0, -45.0, 90.0, 45.0, -90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    "daily_point": (5.0, -20.0, 10.0, 90.0, 0.0, 15.0, -5.0, -15.0, 10.0, 90.0, 0.0),
    "daily_camera": (15.0, 80.0, 95.0, -80.0, -95.0, 10.0, -10.0, -10.0, 10.0, 0.0, 0.0),
    "daily_sleep": (0.0, 15.0, 15.0, -15.0, -15.0, 10.0, -20.0, -10.0, 20.0, 0.0, 90.0),
    "daily_read": (20.0, 45.0, 95.0, -45.0, -95.0, 45.0, -45.0, 45.0, -45.0, 30.0, 0.0),
    "daily_clap": (10.0, 45.0, 95.0, -45.0, -95.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    "daily_look_far": (5.0, -20.0, 10.0, 135.0, -135.0, 10.0, -10.0, -10.0, 10.0, -45.0, 0.0),
    "daily_defend": (15.0, 45.0, 135.0, -45.0, -135.0, 20.0, -20.0, -20.0, 20.0, 0.0, 0.0),
    "daily_victory": (0.0, 115.0, 45.0, -115.0, -45.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
}

# Mapping of categories to lists of pose keys
POSE_CATEGORIES = {
    "yoga": [
        "yoga_tree", "yoga_warrior1", "yoga_warrior2", "yoga_warrior3", "yoga_downward_dog",
        "yoga_cobra", "yoga_triangle", "yoga_bridge", "yoga_lotus", "yoga_boat",
        "yoga_half_moon", "yoga_crow", "yoga_chair", "yoga_camel", "yoga_child",
        "yoga_plank", "yoga_eagle", "yoga_dancer", "yoga_shoulder_stand", "yoga_corpse"
    ],
    "taichi": [
        "taichi_opening", "taichi_crane", "taichi_whip", "taichi_lute", "taichi_brush_knee",
        "taichi_bird_tail", "taichi_clouds", "taichi_rooster", "taichi_repulse_monkey", "taichi_needle",
        "taichi_fan", "taichi_parry_punch", "taichi_close", "taichi_crossing", "taichi_closing"
    ],
    "dancing": [
        "dance_arabesque", "dance_pirouette", "dance_freeze", "dance_salsa", "dance_hiphop",
        "dance_waltz", "dance_disco", "dance_flamenco", "dance_contemporary", "dance_jazz",
        "dance_moonwalk", "dance_rock", "dance_dab", "dance_twist", "dance_robot"
    ],
    "sports": [
        "sport_sprint_start", "sport_sprint", "sport_long_jump", "sport_javelin", "sport_basketball",
        "sport_soccer", "sport_tennis", "sport_swim", "sport_golf", "sport_boxing_jab",
        "sport_boxing_guard", "sport_weight", "sport_archery", "sport_skate", "sport_baseball_pitch",
        "sport_baseball_bat", "sport_karate", "sport_gymnast", "sport_volley", "sport_ice"
    ],
    "daily": [
        "daily_stand", "daily_wave", "daily_sit", "daily_phone", "daily_bow",
        "daily_kneel", "daily_think", "daily_walk", "daily_run", "daily_umbrella",
        "daily_salute", "daily_shrug", "daily_point", "daily_camera", "daily_sleep",
        "daily_read", "daily_clap", "daily_look_far", "daily_defend", "daily_victory"
    ],
    "double": [
        "double_shake", "double_hug", "double_fight", "double_walk", "double_highfive",
        "double_proposal", "double_tango", "double_carry", "double_backtoback", "double_whisper",
        "double_heart", "double_yoga_tree", "double_yoga_dog", "double_yoga_warrior", "double_yoga_acro"
    ]
}

# Localized Display Names for Category selectors
CATEGORY_DISPLAY_NAMES = {
    "yoga": {"zh_TW": "🧘 瑜珈姿勢 (Yoga)", "en_US": "🧘 Yoga Poses"},
    "taichi": {"zh_TW": "☯️ 太極拳法 (Tai Chi)", "en_US": "☯️ Tai Chi Poses"},
    "dancing": {"zh_TW": "💃 舞蹈動作 (Dancing)", "en_US": "💃 Dance Poses"},
    "sports": {"zh_TW": "🏃 運動競技 (Sports)", "en_US": "🏃 Sports & Athletics"},
    "daily": {"zh_TW": "🧍 日常姿勢 (Daily)", "en_US": "🧍 Daily & Actions"},
    "double": {"zh_TW": "👥 雙人互動 (Double)", "en_US": "👥 Double Poses"}
}


def get_preset_pose(name: str, dx: float = 0.0, dy: float = 0.0) -> List[Tuple[float, float]]:
    """
    Returns a single-person pose coordinate list by offset (dx, dy).
    If it's defined in SINGLE_POSE_PARAMS, generates dynamically.
    Falls back to a standard standing pose if not found.
    """
    if name in SINGLE_POSE_PARAMS:
        params = SINGLE_POSE_PARAMS[name]
        # Generates with standard center (256, 150)
        pts = generate_fk_pose(
            tx=256.0, ty=150.0,
            torso_angle=params[0],
            r_shoulder=params[1], r_elbow=params[2],
            l_shoulder=params[3], l_elbow=params[4],
            r_hip=params[5], r_knee=params[6],
            l_hip=params[7], l_knee=params[8],
            head=params[9], global_rot=params[10]
        )
        return [(x + dx, y + dy) for x, y in pts]
        
    # Legacy fallbacks
    if name == "single_stand":
        return get_preset_pose("daily_stand", dx, dy)
    elif name == "single_walk":
        return get_preset_pose("daily_walk", dx, dy)
    elif name == "single_run":
        return get_preset_pose("daily_run", dx, dy)
    elif name == "single_wave":
        return get_preset_pose("daily_wave", dx, dy)
    elif name == "single_sit":
        return get_preset_pose("daily_sit", dx, dy)
        
    return get_preset_pose("daily_stand", dx, dy)


def get_double_preset_pose(name: str) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Returns a tuple of two skeletons for a double person preset.
    Skeletons are procedurally generated or loaded to fit beautifully on the canvas.
    """
    # 1. Double Handshake
    if name == "double_shake":
        p1 = generate_fk_pose(tx=180.0, ty=150.0, torso_angle=5.0, r_shoulder=45.0, r_elbow=30.0, l_shoulder=-15.0, l_elbow=-20.0, r_hip=5.0, r_knee=0.0, l_hip=-5.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=332.0, ty=150.0, torso_angle=-5.0, r_shoulder=-15.0, r_elbow=-20.0, l_shoulder=45.0, l_elbow=30.0, r_hip=5.0, r_knee=0.0, l_hip=-5.0, l_knee=0.0)
        # Symmetrize handshake heights
        p1[4] = (245.0, 200.0)
        p2[7] = (260.0, 200.0)
        return p1, p2
        
    # 2. Warm Hug
    elif name == "double_hug":
        p1 = generate_fk_pose(tx=230.0, ty=150.0, torso_angle=10.0, r_shoulder=55.0, r_elbow=45.0, l_shoulder=45.0, l_elbow=45.0, r_hip=5.0, r_knee=0.0, l_hip=5.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=282.0, ty=150.0, torso_angle=-10.0, r_shoulder=-45.0, r_elbow=-45.0, l_shoulder=-55.0, l_elbow=-45.0, r_hip=-5.0, r_knee=0.0, l_hip=-5.0, l_knee=0.0)
        return p1, p2
        
    # 3. Action Combat
    elif name == "double_fight":
        p1 = generate_fk_pose(tx=170.0, ty=150.0, torso_angle=20.0, r_shoulder=10.0, r_elbow=90.0, l_shoulder=-90.0, l_elbow=-10.0, r_hip=45.0, r_knee=-45.0, l_hip=15.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=342.0, ty=150.0, torso_angle=-20.0, r_shoulder=90.0, r_elbow=10.0, l_shoulder=-10.0, l_elbow=-90.0, r_hip=-15.0, r_knee=0.0, l_hip=-45.0, l_knee=45.0)
        return p1, p2
        
    # 4.並肩漫步 (Walk side-by-side)
    elif name == "double_walk":
        p1 = get_preset_pose("daily_walk", -70.0, 0.0)
        p2 = get_preset_pose("daily_walk", 70.0, 10.0)
        return p1, p2

    # 5. Double High Five
    elif name == "double_highfive":
        p1 = generate_fk_pose(tx=190.0, ty=120.0, torso_angle=10.0, r_shoulder=-150.0, r_elbow=0.0, l_shoulder=30.0, l_elbow=30.0, r_hip=45.0, r_knee=-45.0, l_hip=15.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=322.0, ty=120.0, torso_angle=-10.0, r_shoulder=-30.0, r_elbow=-30.0, l_shoulder=-150.0, l_elbow=0.0, r_hip=-15.0, r_knee=0.0, l_hip=-45.0, l_knee=45.0)
        # Connect high five hands
        p1[4] = (250.0, 60.0)
        p2[7] = (262.0, 60.0)
        return p1, p2

    # 6. Kneeling Proposal (單膝下跪求婚)
    elif name == "double_proposal":
        p1 = generate_fk_pose(tx=180.0, ty=190.0, torso_angle=10.0, r_shoulder=-60.0, r_elbow=45.0, l_shoulder=-60.0, l_elbow=45.0, r_hip=45.0, r_knee=-45.0, l_hip=90.0, l_knee=-110.0)
        p2 = generate_fk_pose(tx=310.0, ty=140.0, torso_angle=0.0, r_shoulder=45.0, r_elbow=90.0, l_shoulder=-30.0, l_elbow=-30.0, r_hip=5.0, r_knee=5.0, l_hip=-5.0, l_knee=5.0)
        return p1, p2

    # 7. Tango Dip (探戈下腰)
    elif name == "double_tango":
        p1 = generate_fk_pose(tx=200.0, ty=140.0, torso_angle=15.0, r_shoulder=45.0, r_elbow=45.0, l_shoulder=-45.0, l_elbow=-45.0, r_hip=30.0, r_knee=-30.0, l_hip=-15.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=300.0, ty=170.0, torso_angle=-60.0, r_shoulder=-120.0, r_elbow=-20.0, l_shoulder=30.0, l_elbow=90.0, r_hip=-45.0, r_knee=45.0, l_hip=45.0, l_knee=0.0)
        return p1, p2

    # 8. Piggyback Carry (背人)
    elif name == "double_carry":
        # P1 carrying P2
        p1 = generate_fk_pose(tx=256.0, ty=170.0, torso_angle=20.0, r_shoulder=45.0, r_elbow=90.0, l_shoulder=-45.0, l_elbow=-90.0, r_hip=45.0, r_knee=-45.0, l_hip=45.0, l_knee=-45.0)
        p2 = generate_fk_pose(tx=250.0, ty=110.0, torso_angle=15.0, r_shoulder=-30.0, r_elbow=90.0, l_shoulder=30.0, l_elbow=-90.0, r_hip=-45.0, r_knee=90.0, l_hip=-45.0, l_knee=90.0)
        return p1, p2

    # 9. Sitting Back-to-Back
    elif name == "double_backtoback":
        p1 = generate_fk_pose(tx=210.0, ty=200.0, torso_angle=-5.0, r_shoulder=15.0, r_elbow=30.0, l_shoulder=-15.0, l_elbow=-30.0, r_hip=90.0, r_knee=-90.0, l_hip=90.0, l_knee=-90.0)
        p2 = generate_fk_pose(tx=302.0, ty=200.0, torso_angle=5.0, r_shoulder=15.0, r_elbow=30.0, l_shoulder=-15.0, l_elbow=-30.0, r_hip=-90.0, r_knee=90.0, l_hip=-90.0, l_knee=90.0)
        return p1, p2

    # 10. Whispering Secrets
    elif name == "double_whisper":
        p1 = generate_fk_pose(tx=210.0, ty=140.0, torso_angle=15.0, r_shoulder=45.0, r_elbow=90.0, l_shoulder=-15.0, l_elbow=-30.0, r_hip=10.0, r_knee=10.0, l_hip=-10.0, l_knee=10.0)
        p2 = generate_fk_pose(tx=290.0, ty=140.0, torso_angle=-10.0, r_shoulder=15.0, r_elbow=30.0, l_shoulder=-45.0, l_elbow=-90.0, r_hip=10.0, r_knee=10.0, l_hip=-10.0, l_knee=10.0, head=30.0)
        return p1, p2

    # 11. Double Heart (合力比心)
    elif name == "double_heart":
        p1 = generate_fk_pose(tx=200.0, ty=140.0, torso_angle=10.0, r_shoulder=-90.0, r_elbow=90.0, l_shoulder=45.0, l_elbow=45.0, r_hip=10.0, r_knee=0.0, l_hip=-10.0, l_knee=0.0)
        p2 = generate_fk_pose(tx=312.0, ty=140.0, torso_angle=-10.0, r_shoulder=-45.0, r_elbow=-45.0, l_shoulder=90.0, l_elbow=-90.0, r_hip=10.0, r_knee=0.0, l_hip=-10.0, l_knee=0.0)
        # Meet hands over head and in front to make a heart shape
        p1[4] = (256.0, 70.0)
        p2[7] = (256.0, 70.0)
        p1[7] = (245.0, 180.0)
        p2[4] = (267.0, 180.0)
        return p1, p2

    # 12. Partner Yoga Tree
    elif name == "double_yoga_tree":
        # P1 stands on left, raises left arm, holds P2's hand with right arm
        p1 = generate_fk_pose(tx=190.0, ty=150.0, torso_angle=0.0, r_shoulder=-45.0, r_elbow=30.0, l_shoulder=160.0, l_elbow=10.0, r_hip=45.0, r_knee=135.0, l_hip=0.0, l_knee=0.0)
        # P2 stands on right, raises right arm, holds P1's hand with left arm
        p2 = generate_fk_pose(tx=322.0, ty=150.0, torso_angle=0.0, r_shoulder=-160.0, r_elbow=-10.0, l_shoulder=45.0, l_elbow=-30.0, r_hip=0.0, r_knee=0.0, l_hip=-45.0, l_knee=-135.0)
        # Connect hands in middle
        p1[4] = (256.0, 200.0)
        p2[7] = (256.0, 200.0)
        return p1, p2

    # 13. Partner Yoga Stack Dog (上下疊羅漢犬式)
    elif name == "double_yoga_dog":
        p1 = generate_fk_pose(tx=170.0, ty=180.0, torso_angle=45.0, r_shoulder=-120.0, r_elbow=0.0, l_shoulder=-120.0, l_elbow=0.0, r_hip=90.0, r_knee=0.0, l_hip=90.0, l_knee=0.0, global_rot=-30.0)
        p2 = generate_fk_pose(tx=250.0, ty=110.0, torso_angle=45.0, r_shoulder=-120.0, r_elbow=0.0, l_shoulder=-120.0, l_elbow=0.0, r_hip=90.0, r_knee=0.0, l_hip=90.0, l_knee=0.0, global_rot=-40.0)
        return p1, p2

    # 14. Partner Yoga Warrior
    elif name == "double_yoga_warrior":
        # Facing each other, holding hands, lunging backward
        p1 = generate_fk_pose(tx=190.0, ty=150.0, torso_angle=10.0, r_shoulder=-90.0, r_elbow=0.0, l_shoulder=-90.0, l_elbow=0.0, r_hip=35.0, r_knee=-80.0, l_hip=-45.0, l_knee=15.0)
        p2 = generate_fk_pose(tx=322.0, ty=150.0, torso_angle=-10.0, r_shoulder=90.0, r_elbow=0.0, l_shoulder=90.0, l_elbow=0.0, r_hip=45.0, r_knee=-15.0, l_hip=-35.0, l_knee=80.0)
        # Connect hands in middle
        p1[4] = (256.0, 160.0)
        p2[7] = (256.0, 160.0)
        return p1, p2

    # 15. Partner Yoga Acro (空中支撐)
    elif name == "double_yoga_acro":
        # P1 lies on ground, uses feet to support P2 who is flying horizontally in the air
        p1 = generate_fk_pose(tx=256.0, ty=280.0, torso_angle=0.0, r_shoulder=45.0, r_elbow=30.0, l_shoulder=-45.0, l_elbow=-30.0, r_hip=-90.0, r_knee=0.0, l_hip=-90.0, l_knee=0.0, global_rot=90.0)
        p2 = generate_fk_pose(tx=256.0, ty=130.0, torso_angle=-90.0, r_shoulder=-180.0, r_elbow=0.0, l_shoulder=-180.0, l_elbow=0.0, r_hip=90.0, r_knee=0.0, l_hip=90.0, l_knee=0.0)
        # Support contact
        p2[1] = (256.0, 120.0)
        return p1, p2

    # Fallback default handshake
    return get_double_preset_pose("double_shake")
