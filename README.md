# Human Pose Editor - 雙人/單人專業人體姿勢編輯器 (3D Mannequin & OpenPose)

[繁體中文](#繁體中文) | [English](#english)

---

# 繁體中文

這是一個精美、現代化且採用深色科技風介面 (Dark/Neon Palette) 的人體姿勢編輯器。它支援單人與雙人姿勢調整，並能將姿勢無失真地渲染導出成 OpenPose 標準圖片（非常適合用於 Stable Diffusion ControlNet 繪圖導引）或 3D 藝術家木人素體參考圖。

專案全面採用**高度模組化設計**，以「純函數 (Pure Functions)」為最小幾何與邏輯計算單元，保證程式碼易讀、易擴充且性能卓越。

---

## ✨ 核心特色與亮點

1. **極速環境管理**：使用 Rust 撰寫的極速套件工具 `uv`，一鍵建立環境並安裝所有依賴（PySide6 與 Pillow）。
2. **預設 3D 藝術家木人素體 (3D Mannequin)**：啟動時預設以立體感十足的 3D 藝術家木人素體呈現，並能完美進行節點拖曳調整。
3. **多語系支援 (i18n)**：介面內建**繁體中文**與**英文 (English)**，點擊右上角按鈕即可動態、即時且無縫地雙向切換，完全不影響目前的姿勢調整。
4. **專業高階輔助功能**：
   * **自訂背景描圖 (Background Tracing)**：可隨時載入外部參考圖片至畫布背景，並調整透明度 (Opacity) 進行完美的骨架關節對齊。
   * **角色鎖定與隱藏**：可單獨鎖定或隱藏角色。鎖定後可防止編輯另一個人時誤觸。
   * **骨架水平鏡像 (Mirror)**：一鍵水平翻轉骨架，並自動處理人體左右側關節的解剖學對調，確保 OpenPose 色彩正確。
   * **體型與身高微調**：提供獨立的「身高比例」與「手腳長度」微調滑桿，採用階層式幾何計算，可拉出二次元長腿、Q版比例等。
   * **畫布尺寸與構圖線**：支援快速切換 AI 繪圖常用比例（1:1, 2:3, 3:2）與畫幅，並支援**三分法網格**與**黃金分割線**，助您精確構圖。
5. **高品質無損導出**：
   * 支援導出**純黑背景（ControlNet 標準）**、**純白背景**與**透明背景 (PNG)**。
   * 導出時會自動根據解析度大小**等比例調整骨架線條與關節點的粗細**，確保輸出結果永遠清晰細緻。
   * 匯出時會自動產生搭配的 Gemini 旁路提示詞檔 (txt)。

---

## 🖱️ 滑鼠與鍵盤直覺操作

* **單點拖曳**：用滑鼠左鍵可拖曳任意彩色關節點進行局部位移。
* **整體位移**：選中主軀幹（**頸部關節，紅色外圈環繞**）並拖曳，可平移整個人的骨架。
* **旋轉與縮放**：滑鼠懸停在**頸部關節**上方，**滾動滑鼠滾輪**可旋轉整個人；**按住 `Ctrl` 鍵同時滾動滾輪**可等比例縮放整個人。

---

## 🚀 快速開始指南

本專案支援使用 `uv` 或是傳統的 `pip` 進行管理。

### 方式 A：使用 `uv` 管理與執行（推薦，極速乾淨）

如果您已安裝 `uv`，請在專案根目錄開啟終端機（PowerShell / CMD）並執行：

1. **建立虛擬環境與安裝依賴**：
   ```bash
   uv venv
   uv pip install -r pyproject.toml
   ```
2. **執行編輯器**：
   ```bash
   .venv\Scripts\python main.py
   ```

*(備註：您也可以直接執行 `uv run main.py`，`uv` 會自動為您處理環境！)*

### 方式 B：使用傳統 `pip` 虛擬環境

1. **建立並啟用虛擬環境**：
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **安裝依賴**：
   ```bash
   pip install PySide6 Pillow
   ```
3. **執行編輯器**：
   ```bash
   python main.py
   ```

### ⚡ 一鍵環境安裝與啟動 (One-Click Setup & Launch)

為了提供最直覺、免安裝繁雜指令的極致體驗，專案目錄中提供了兩個批次檔：

1. **`install.bat` (一鍵環境安裝)**：
   * **首次使用時，請直接雙擊 `install.bat`！**
   * 它會自動檢查您的 Python 環境，並優先使用超高速包管理器 `uv`（若無則自動嘗試安裝，或優雅降級使用 Python 內建 `venv` 與 `pip`）建立全新的虛擬環境 `.venv`，並安裝 `PySide6` 與 `Pillow` 等所有依賴套件。
2. **`run.bat` (一鍵啟動)**：
   * **安裝完成後（或後續要使用時），直接雙擊 `run.bat` 即可！**
   * 它使用 Windows 的 `pythonw.exe` 執行，這會**自動隱藏 CMD 黑色背景終端機視窗**，讓應用程式如同原生桌面軟體般精美、乾淨。

---

## 📁 檔案模組說明

本專案高度注重工程品質，將邏輯完全拆分為以下模組：

* 📄 **[main.py](file:///D:/human-pose-editor/main.py)**：主程式進入點，負責建構視窗佈局、綁定訊號與槽函數、載入 QSS 深色霓虹樣式表。
* 📄 **[pose_canvas.py](file:///D:/human-pose-editor/pose_canvas.py)**：繼承自 `QWidget` 的互動式畫布，僅負責滑鼠事件監聽與畫布/背景/網格渲染，將幾何數學計算委託給 `pose_math.py`。
* 📄 **[pose_math.py](file:///D:/human-pose-editor/pose_math.py)**：純函數數學幾何運算模組。負責關節旋轉、縮放、平移、解剖學水平鏡像、以及身高與手腳長度的階層式幾何比例微調。
* 📄 **[mannequin_renderer.py](file:///D:/human-pose-editor/mannequin_renderer.py)**：3D 藝術家木人素體渲染引擎。使用 `QPainterPath` 繪製順滑的肌肉線條，搭配 `QLinearGradient` 與 `QRadialGradient` 展現出逼真的 3D 浮雕立體感。
* 📄 **[pose_presets.py](file:///D:/human-pose-editor/pose_presets.py)**：存放 OpenPose 18點骨架連接拓樸圖、關節色彩定義，以及內建豐富的單人與雙人預設姿勢。
* 📄 **[pose_io.py](file:///D:/human-pose-editor/pose_io.py)**：檔案輸入與輸出模組。利用 PySide6 的 headless `QImage` 進行高反鋸齒的無損渲染，並將結果儲存為 PNG/JPG，亦負責產生 Gemini 旁路提示詞描述檔。
* 📄 **[i18n.py](file:///D:/human-pose-editor/i18n.py)**：多語系語系檔模組，儲存所有中英文翻譯。

---

## 🤖 AI 代理與開發者指南 (For Agents & Developers)

當 AI 代理或開發者在此專案中工作時，請遵循以下核心技術架構：

### 1. 座標系統與比例尺 (Coordinate System & Scale)
* **虛擬畫布大小**：基準座標系統為 `512 x 512`。所有預設姿勢與骨架關節的初始座標皆定義在此空間內。
* **高解析度適應**：導出與實際顯示時會乘以 `scale_factor = max(width, height) / 512.0`。
* 當您編輯座標或計算幾何位移時，必須保持**虛擬座標系與實體顯示座標的分離**。關節編輯一律以虛擬畫布座標（0 至 512）進行，在 [pose_canvas.py](file:///D:/human-pose-editor/pose_canvas.py) 渲染時再透過 `to_screen_coords` 進行轉換。

### 2. OpenPose 18 關節點定義 (OpenPose 18 Keypoints)
本專案採用 COCO/OpenPose 18點拓樸標準，關節點索引（Index）如下：
```text
0: Nose        1: Neck         2: R.Shoulder   3: R.Elbow     4: R.Wrist
5: L.Shoulder  6: L.Elbow      7: L.Wrist      8: R.Hip       9: R.Knee
10: R.Ankle    11: L.Hip       12: L.Knee      13: L.Ankle    14: R.Eye
15: L.Eye      16: R.Ear       17: L.Ear
```
* **關節遮蔽/未初始化狀態**：如果關節座標為 `(0.0, 0.0)`，代表該關節處於隱藏、未初始化或失效狀態，渲染時應跳過該關節及其關聯的骨骼連線。

### 3. 解剖學與階層幾何 (Anatomy & Hierarchical Geometry)
* **頸部（Index 1）作為絕對錨點**：
  * 在 [pose_math.py](file:///D:/human-pose-editor/pose_math.py) 中，進行**整體旋轉、等比例縮放、水平鏡像、以及體型微調**時，皆以頸部關節為原點進行計算。
* **肢體比例縮放 (Hierarchical Scaling)**：
  * 當使用者拉動「手腳長度」滑桿時，不可採用簡單的整體拉伸，否則會造成關節斷裂。
  * 必須採用**階層式向量縮放**：以 `Shoulder -> Elbow -> Wrist` 和 `Hip -> Knee -> Ankle` 的父子階層順序，依次將子關節相對於父關節的長度向量乘以比例因子，重新計算出新的座標點。

### 4. 3D 木人素體渲染機制 (3D Mannequin Rendering)
* 為了完美模擬實體素體，[mannequin_renderer.py](file:///D:/human-pose-editor/mannequin_renderer.py) 的渲染順序（Z-Sorting）十分嚴格（由後至前）：
  1. **雙腿與雙腳**（左腿 -> 右腿 -> 腳部 -> 踝關節 -> 膝關節）
  2. **主軀幹**（Torso 多邊形 -> 骨盆與肩關節球體）
  3. **雙手與雙臂**（左臂 -> 右臂 -> 肘關節 -> 腕關節 -> 手部）
  4. **頸部**（膠囊體與頸部關節）
  5. **頭部**（頭部球體與五官輔助指南線）
* **肢體（Limbs）膠囊體**：使用 `_draw_capsule`，兩端分別以關節為球心畫出圓角，並沿垂直於肢體軸向的方向填充線性漸層（Linear Gradient）以呈現圓柱立體感。
* **關節（Joints）球體**：使用 `_draw_sphere`，在關節中心繪製圓形，填充偏心的放射漸層（Radial Gradient），模擬高光與陰影，創造 3D 球體質感。

---
---

# English

A beautiful, modern human pose editor styled with a dark sci-fi aesthetic (Dark/Neon Palette). It supports editing poses for single or dual figures and rendering them losslessly as standard OpenPose keypoint images (perfect for Stable Diffusion ControlNet guidance) or 3D artist mannequin reference models.

The project is **highly modularized**, employing pure functions as the core units for geometric calculations to guarantee code readability, scalability, and exceptional performance.

---

## ✨ Key Features & Highlights

1. **Blazing-Fast Environment Management**: Uses `uv` (a fast Python package installer written in Rust) to create a clean virtual environment and install PySide6 and Pillow instantly.
2. **Default 3D Artist Mannequin Style**: Displays a highly dimensional, shaded 3D mannequin by default upon startup. Joints can be edited directly.
3. **Multi-Language Support (i18n)**: Seamlessly switch between **Traditional Chinese (繁體中文)** and **English** dynamically in real time without losing active pose states.
4. **Professional Assistant Features**:
   * **Background Tracing**: Load a reference photo onto the background canvas with adjustable opacity for precise alignment.
   * **Character Lock & Hide**: Separately lock or hide characters. Locking prevents accidental changes when editing multiple characters.
   * **Anatomical Mirroring**: Horizontally flip a character's pose, automatically swapping left/right joint colors to keep OpenPose color coding anatomically correct.
   * **Body Proportions Fine-Tuning**: Fine-tune height and limb lengths via hierarchical geometry sliders (perfect for creating anime long-legs or chibi figures).
   * **Canvas & Composition Guides**: Quickly switch between standard aspect ratios (1:1, 2:3, 3:2) and toggle rule-of-thirds grids or golden ratios.
5. **High-Quality Lossless Export**:
   * Export in **Black Background (ControlNet standard)**, **White Background (sketch reference)**, or **Transparent Background (PNG)**.
   * Brush strokes and joints automatically scale based on the export resolution.
   * Automatically exports a matching Gemini sidecar prompt text file.

---

## 🖱️ Intuitive Interactions

* **Drag-and-Drop Joints**: Left-click and drag any joint to pose locally.
* **Global Translation**: Left-click and drag the **Neck joint (highlighted with a red ring)** to translate the entire skeleton.
* **Rotate & Scale**: Hover your mouse over the **Neck joint** and **scroll the wheel** to rotate; hold `Ctrl` and **scroll the wheel** to scale the character proportionally.

---

## 🚀 Quick Start Guide

This project supports environment setup via either `uv` or standard `pip`.

### Option A: Using `uv` (Recommended - fast & clean)

If you have `uv` installed globally, run the following commands in the project directory:

1. **Create Virtual Environment & Install Dependencies**:
   ```bash
   uv venv
   uv pip install -r pyproject.toml
   ```
2. **Run Editor**:
   ```bash
   .venv\Scripts\python main.py
   ```

*(Note: You can also just run `uv run main.py` and let `uv` handle everything automatically!)*

### Option B: Using Standard Python Virtual Environment (`pip`)

1. **Create & Activate Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install PySide6 Pillow
   ```
3. **Run Editor**:
   ```bash
   python main.py
   ```

### ⚡ One-Click Scripts

For convenience, two batch files are provided:

1. **`install.bat`**: Automatically checks for Python, installs `uv` locally if not present, sets up the virtual environment, and installs dependencies.
2. **`run.bat`**: Launches the application using Windows' headless `pythonw.exe`, hiding the console window for a native desktop experience.

---

## 📁 File Modules & Structure

The codebase maintains strict modular division:

* 📄 **[main.py](file:///D:/human-pose-editor/main.py)**: The main entry point. Constructs GUI layout, binds signals/slots, and loads the Neon Dark stylesheet.
* 📄 **[pose_canvas.py](file:///D:/human-pose-editor/pose_canvas.py)**: QWidget subclass representing the interactive canvas. Handles mouse events, grids, and drawing setups, delegating math calculations to `pose_math.py`.
* 📄 **[pose_math.py](file:///D:/human-pose-editor/pose_math.py)**: Pure mathematical operations. Handles translation, rotation, scaling, mirroring, and hierarchical body ratio modifications.
* 📄 **[mannequin_renderer.py](file:///D:/human-pose-editor/mannequin_renderer.py)**: 3D mannequin rendering engine. Draws muscles using `QPainterPath` and styles them with gradients to create a shaded 3D sculpture look.
* 📄 **[pose_presets.py](file:///D:/human-pose-editor/pose_presets.py)**: Holds standard OpenPose topologies, joint color palettes, and preset definitions.
* 📄 **[pose_io.py](file:///D:/human-pose-editor/pose_io.py)**: Headless canvas drawing and file export. Saves high-quality images and outputs Gemini sidecar prompts.
* 📄 **[i18n.py](file:///D:/human-pose-editor/i18n.py)**: Localization dictionary files.

---

## 🤖 Agent & Developer Guide

When AI agents or developer engines work on this project, adhere to these technical specifications:

### 1. Coordinate System & Scale
* **Virtual Workspace**: All predefined poses and skeletons are designed inside a standard `512 x 512` coordinate system.
* **Resolution Scale**: When rendering to screen or exporting headlessly, coordinates are multiplied by `scale_factor = max(width, height) / 512.0`.
* Keep the **virtual coordinate system decoupled from the display screen pixels**. Modify raw skeleton coordinates on the `(0, 0)` to `(512, 512)` grid. Map to screens in [pose_canvas.py](file:///D:/human-pose-editor/pose_canvas.py) via `to_screen_coords`.

### 2. OpenPose 18 Keypoints Topology
We follow the COCO/OpenPose 18-keypoint format:
```text
0: Nose        1: Neck         2: R.Shoulder   3: R.Elbow     4: R.Wrist
5: L.Shoulder  6: L.Elbow      7: L.Wrist      8: R.Hip       9: R.Knee
10: R.Ankle    11: L.Hip       12: L.Knee      13: L.Ankle    14: R.Eye
15: L.Eye      16: R.Ear       17: L.Ear
```
* **Keypoint Visibility**: A coordinate value of `(0.0, 0.0)` denotes a hidden or uninitialized joint. Do not render bones or capsules leading to or from a hidden joint.

### 3. Hierarchical Proportional Calculations
* **Neck (Index 1) as Root Anchor**:
  * In [pose_math.py](file:///D:/human-pose-editor/pose_math.py), global modifications (such as mirroring, rotation, scaling, or height sliders) use the Neck coordinates as the center anchor.
* **Hierarchical Limb Scaling**:
  * Simple scaling of limb coordinates breaks skeleton integrity.
  * You must compute limb lengths recursively down parent-child relationships: `Shoulder -> Elbow -> Wrist` and `Hip -> Knee -> Ankle`. Recompute positions down the chain relative to the parent joint vector scaled by the limb factor.

### 4. 3D Mannequin Rendering Specs
* In [mannequin_renderer.py](file:///D:/human-pose-editor/mannequin_renderer.py), Z-sorting is strictly enforced back-to-front:
  1. **Legs & Feet** (Left leg -> Right leg -> Feet -> Ankles -> Knees)
  2. **Torso** (Main torso polygon -> Hips -> Shoulders)
  3. **Arms & Hands** (Left arm -> Right arm -> Elbows -> Wrists -> Hands)
  4. **Neck** (Capsule -> Neck joint)
  5. **Head** (Head sphere -> Guidelines)
* **Capsule Drawing**: Call `_draw_capsule` to construct tapered capsules between joints. Use a `QLinearGradient` perpendicular to the limb vector direction to mimic cylindrical shading.
* **Sphere Drawing**: Call `_draw_sphere` with a radial gradient centered offset-up-left to simulate light casting on spheres.
