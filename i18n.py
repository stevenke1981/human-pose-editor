"""
Multi-language translation module (i18n) for the Human Pose Editor.
Provides translations for Traditional Chinese (zh_TW) and English (en_US).
"""

# Translation dictionary containing all UI strings
TRANSLATIONS = {
    "zh_TW": {
        "title": "人體姿勢編輯器 - 雙人/單人專業版",
        "switch_lang": "English",
        "lang_name": "繁體中文",
        # Sidebar sections
        "char_manager": "角色管理",
        "presets_panel": "預設姿勢庫",
        "canvas_settings": "畫布與背景設定",
        "composition_assist": "構圖輔助工具",
        "export_panel": "匯出設定",
        # Buttons & Labels
        "add_char": "＋ 新增角色",
        "del_char": "－ 刪除角色",
        "reset_pose": "↺ 重設姿勢",
        "mirror_pose": "⇄ 左右鏡像",
        "lock": "鎖定",
        "unlock": "解鎖",
        "visible": "顯示",
        "hidden": "隱藏",
        "height_scale": "身高比例: ",
        "limb_scale": "手腳長度: ",
        "bg_image": "參考背景圖: ",
        "load_bg": "📂 載入背景圖",
        "clear_bg": "❌ 清除背景",
        "bg_opacity": "背景透明度: ",
        "resolution": "畫布尺寸: ",
        "grid_type": "構圖線: ",
        "grid_none": "無輔助線",
        "grid_thirds": "三分法網格",
        "grid_golden": "黃金分割線",
        "export_btn": "💾 匯出姿勢圖片",
        "canvas_color": "背景底色: ",
        "bg_black": "純黑 (ControlNet 標準)",
        "bg_white": "純白 (手繪參考)",
        "bg_transparent": "透明背景 (PNG)",
        # Presets names
        "preset_single_stand": "單人 - 標準站立",
        "preset_single_walk": "單人 - 邁步前行",
        "preset_single_run": "單人 - 奔跑衝刺",
        "preset_single_wave": "單人 - 揮手致意",
        "preset_single_jump": "單人 - 跳躍騰空",
        "preset_single_sit": "單人 - 盤腿而坐",
        "preset_double_shake": "雙人 - 握手合影",
        "preset_double_hug": "雙人 - 溫暖擁抱",
        "preset_double_fight": "雙人 - 近身搏擊",
        "preset_double_walk": "雙人 - 並肩漫步",
        # Dialogs / Prompts
        "export_success": "匯出成功",
        "export_success_msg": "圖片已成功儲存至:\n{}",
        "export_error": "匯出失敗",
        "export_error_msg": "無法儲存圖片，錯誤訊息:\n{}",
        "load_bg_title": "選擇參考背景圖",
        "save_image_title": "儲存姿勢圖片",
        "image_files": "圖片檔案 (*.png *.jpg *.jpeg *.bmp)",
        "all_files": "所有檔案 (*.*)",
        "status_ready": "就緒。拖曳節點以調整姿勢。選取主軀幹（頸部連線）可平移或以滑輪旋轉/縮放人物。",
        "status_locked": "此角色已鎖定，無法修改。",
        "status_hidden": "此角色已隱藏。",
        "limit_reached": "已達角色上限（最多支援 2 人）",
        "char_label": "角色 {}",
        "no_char_selected": "請先選擇一個角色進行調整",
        # Joint labels
        "labels_type": "節點標記: ",
        "labels_none": "無標記",
        "labels_indices": "數字編號 (0-17)",
        "labels_names": "部位名稱 (Nose...)",
        "show_scale_axes": "顯示比例尺與空間方向",
        "show_pose_name": "顯示姿勢名稱",
        "export_bg": "匯出時包含背景參考圖",
        "skeleton_style": "骨架/人體樣式: ",
        "style_classic": "傳統彩色線條 (ControlNet)",
        "style_mannequin": "3D 藝術家素體 (繪畫參考)",
        "pose_custom": "自訂姿勢",
        "export_success_sidecar_msg": "圖片與 Gemini 旁路提示詞已成功儲存至:\n{}\n及\n{}",
        # Joint names (zh_TW)
        "joint_0": "鼻",
        "joint_1": "頸部",
        "joint_2": "右肩",
        "joint_3": "右肘",
        "joint_4": "右腕",
        "joint_5": "左肩",
        "joint_6": "左肘",
        "joint_7": "左腕",
        "joint_8": "右臀",
        "joint_9": "右膝",
        "joint_10": "右踝",
        "joint_11": "左臀",
        "joint_12": "左膝",
        "joint_13": "左踝",
        "joint_14": "右眼",
        "joint_15": "左眼",
        "joint_16": "右耳",
        "joint_17": "左耳",
        "scale_unit": "像素",
    },
    "en_US": {
        "title": "Human Pose Editor - Professional Single/Double Edition",
        "switch_lang": "繁體中文",
        "lang_name": "English",
        # Sidebar sections
        "char_manager": "Characters",
        "presets_panel": "Pose Presets",
        "canvas_settings": "Canvas & Background",
        "composition_assist": "Composition Tools",
        "export_panel": "Export settings",
        # Buttons & Labels
        "add_char": "＋ Add Character",
        "del_char": "－ Delete Character",
        "reset_pose": "↺ Reset Pose",
        "mirror_pose": "⇄ Mirror Pose",
        "lock": "Lock",
        "unlock": "Unlock",
        "visible": "Show",
        "hidden": "Hide",
        "height_scale": "Height Scale: ",
        "limb_scale": "Limb Length: ",
        "bg_image": "Ref Background: ",
        "load_bg": "📂 Load Background",
        "clear_bg": "❌ Clear Background",
        "bg_opacity": "Background Opacity: ",
        "resolution": "Canvas Size: ",
        "grid_type": "Composition: ",
        "grid_none": "No Guidelines",
        "grid_thirds": "Rule of Thirds",
        "grid_golden": "Golden Ratio",
        "export_btn": "💾 Export Pose Image",
        "canvas_color": "Canvas Base: ",
        "bg_black": "Pure Black (ControlNet Std)",
        "bg_white": "Pure White (Drawing Ref)",
        "bg_transparent": "Transparent (PNG)",
        # Presets names
        "preset_single_stand": "Single - Standard Stand",
        "preset_single_walk": "Single - Walking",
        "preset_single_run": "Single - Running",
        "preset_single_wave": "Single - Friendly Wave",
        "preset_single_jump": "Single - Mid-air Jump",
        "preset_single_sit": "Single - Crossed Legs",
        "preset_double_shake": "Double - Handshake",
        "preset_double_hug": "Double - Warm Hug",
        "preset_double_fight": "Double - Action Combat",
        "preset_double_walk": "Double - Walking Side-by-side",
        # Dialogs / Prompts
        "export_success": "Export Successful",
        "export_success_msg": "Image saved successfully to:\n{}",
        "export_error": "Export Failed",
        "export_error_msg": "Could not save image. Error:\n{}",
        "load_bg_title": "Select Background Reference Image",
        "save_image_title": "Save Pose Image",
        "image_files": "Image Files (*.png *.jpg *.jpeg *.bmp)",
        "all_files": "All Files (*.*)",
        "status_ready": "Ready. Drag joints to adjust pose. Drag main torso (neck connection) to translate, or use mouse wheel to rotate/scale.",
        "status_locked": "This character is locked and cannot be edited.",
        "status_hidden": "This character is hidden.",
        "limit_reached": "Maximum character limit reached (Max 2 characters)",
        "char_label": "Character {}",
        "no_char_selected": "Please select a character to adjust first",
        # Joint labels
        "labels_type": "Joint Labels: ",
        "labels_none": "No Labels",
        "labels_indices": "Index Numbers (0-17)",
        "labels_names": "Joint Names (Nose...)",
        "show_scale_axes": "Show Scale & XYZ Axes",
        "show_pose_name": "Show Pose Name",
        "export_bg": "Include reference background on export",
        "skeleton_style": "Mannequin Style: ",
        "style_classic": "Classic Color Line (ControlNet)",
        "style_mannequin": "3D Artist Mannequin (Drawing Ref)",
        "pose_custom": "Custom Pose",
        "export_success_sidecar_msg": "Image and Gemini sidecar prompt saved successfully to:\n{}\nand\n{}",
        # Joint names (en_US)
        "joint_0": "Nose",
        "joint_1": "Neck",
        "joint_2": "RShoulder",
        "joint_3": "RElbow",
        "joint_4": "RWrist",
        "joint_5": "LShoulder",
        "joint_6": "LElbow",
        "joint_7": "LWrist",
        "joint_8": "RHip",
        "joint_9": "RKnee",
        "joint_10": "RAnkle",
        "joint_11": "LHip",
        "joint_12": "LKnee",
        "joint_13": "LAnkle",
        "joint_14": "REye",
        "joint_15": "LEye",
        "joint_16": "REar",
        "joint_17": "LEar",
        "scale_unit": "px",
    }
}


def get_translation(key: str, lang: str = "zh_TW") -> str:
    """
    Returns the translated string for the given key and language.
    Defaults to zh_TW if the key or language is not found.
    """
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["zh_TW"])
    return lang_dict.get(key, f"[{key}]")


def get_pose_display_name(pose_name: str, lang: str = "zh_TW") -> str:
    """
    Returns the translated, human-friendly display name of a given pose key.
    Handles legacy presets, custom poses, and modified indicators automatically.
    """
    if not pose_name or pose_name == "custom":
        return get_translation("pose_custom", lang)
    
    # Check if it is a modified pose
    is_modified = False
    base_name = pose_name
    if pose_name.endswith("_modified"):
        is_modified = True
        base_name = pose_name[:-9]
    
    # Try finding in basic presets
    preset_key = f"preset_{base_name}"
    translated = get_translation(preset_key, lang)
    if not translated.startswith("[preset_"):
        disp = translated
    else:
        # Try pose_presets.POSE_DISPLAY_NAMES
        import pose_presets
        names = pose_presets.POSE_DISPLAY_NAMES.get(base_name, {})
        disp = names.get(lang, base_name)
        
    if is_modified:
        suffix = " (已修改)" if lang == "zh_TW" else " (Modified)"
        return f"{disp}{suffix}"
    return disp

