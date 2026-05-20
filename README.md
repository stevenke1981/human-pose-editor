# Human Pose Editor - 雙人/單人專業人體姿勢編輯器

這是一個精美、現代化且採用深色科技風介面 (Dark/Neon Palette) 的人體姿勢編輯器。它支援單人與雙人姿勢調整，並能將姿勢無失真地渲染導出成 OpenPose 標準圖片（非常適合用於 Stable Diffusion ControlNet 繪圖導引）或一般美術參考圖。

專案全面採用**高度模組化設計**，以「純函數 (Pure Functions)」為最小幾何與邏輯計算單元，保證程式碼易讀、易擴充且性能卓越。

---

## ✨ 核心特色與亮點

1. **極速環境管理**：使用 Rust 撰寫的極速套件工具 `uv`，一鍵建立環境並安裝所有依賴（PySide6 與 Pillow）。
2. **多語系支援 (i18n)**：介面內建**繁體中文**與**英文 (English)**，點擊右上角按鈕即可動態、即時且無縫地雙向切換，完全不影響目前的姿勢調整。
3. **滑鼠直覺操作**：
   * **單點拖曳**：用滑鼠左鍵可拖曳任意彩色關節點進行局部位移。
   * **整體位移**：選中主軀幹（**頸部關節，紅色外圈環繞**）並拖曳，可平移整個人的骨架。
   * **旋轉與縮放**：滑鼠懸停在**頸部關節**上方，**滾動滑鼠滾輪**可旋轉整個人；**按住 `Ctrl` 鍵同時滾動滾輪**可等比例縮放整個人。
4. **內建豐富預設姿勢 (Presets)**：
   * **單人預設**：標準站立、邁步前行、奔跑衝刺、揮手致意、跳躍騰空、盤腿而坐。
   * **雙人預設**：握手合影、溫暖擁抱、近身搏擊、並肩漫步。自動補齊第二個角色，一鍵排出互動大片！
5. **專業高階輔助功能**：
   * **自訂背景描圖 (Background Tracing)**：可隨時載入外部參考圖片至畫布背景，並調整透明度 (Opacity) 進行完美的骨架關節對齊。
   * **角色鎖定與隱藏**：可單獨鎖定或隱藏角色。鎖定後可防止編輯另一個人時誤觸。
   * **骨架水平鏡像 (Mirror)**：一鍵水平翻轉骨架，並自動處理人體左右側關節的解剖學對調，確保 OpenPose 色彩正確。
   * **體型與身高微調**：提供獨立的「身高比例」與「手腳長度」微調滑桿，採用階層式幾何計算，可拉出二次元長腿、Q版比例等。
   * **畫布尺寸與構圖線**：支援快速切換 AI 繪圖常用比例（1:1, 2:3, 3:2）與畫幅，並支援**三分法網格**與**黃金分割線**，助您精確構圖。
6. **高品質無損導出**：
   * 支援導出**純黑背景（ControlNet 標準）**、**純白背景**與**透明背景 (PNG)**。
   * 導出時會自動根據解析度大小**等比例調整骨架線條與關節點的粗細**，確保輸出結果永遠清晰細緻。

---

## 🚀 快速開始指南

本專案支援使用 `uv` 或是傳統的 `pip` 進行管理。

### 方式 A：使用 `uv` 管理與執行（推薦，極速乾淨）

如果您已安裝 `uv`，請在專案根目錄（`c:/Users/steven/Documents/Playground`）開啟終端機（PowerShell / CMD）並執行：

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

---

## ⚡ 一鍵環境安裝與啟動 (One-Click Setup & Launch)

為了提供最直覺、免安裝繁雜指令的極致體驗，專案目錄中提供了兩個批次檔：

1. **`install.bat` (一鍵環境安裝)**：
   * **首次使用時，請直接雙擊 `install.bat`！**
   * 它會自動檢查您的 Python 環境，並優先使用超高速包管理器 `uv`（若無則自動嘗試安裝，或優雅降級使用 Python 內建 `venv` 與 `pip`）建立全新的虛擬環境 `.venv`，並安裝 `PySide6` 與 `Pillow` 等所有依賴套件。
   * 您完全不需要打開 PowerShell 敲打任何安裝指令，全程自動化處理。

2. **`run.bat` (一鍵啟動)**：
   * **安裝完成後（或後續要使用時），直接雙擊 `run.bat` 即可！**
   * 它使用 Windows 的 `pythonw.exe` 執行，這會**自動隱藏 CMD 黑色背景終端機視窗**，讓應用程式如同原生桌面軟體般精美、乾淨。
   * 如果尚未安裝依賴，它也會貼心地引導您執行 `install.bat`。

---

## 📁 檔案模組說明

本專案高度注重工程品質，將邏輯完全拆分為以下模組：

* 📄 **[main.py](file:///c:/Users/steven/Documents/Playground/main.py)**：主程式進入點，負責建構視窗佈局、綁定訊號與槽函數、載入 QSS 深色霓虹樣式表。
* 📄 **[pose_canvas.py](file:///c:/Users/steven/Documents/Playground/pose_canvas.py)**：繼承自 `QWidget` 的互動式畫布，僅負責滑鼠事件監聽與畫布/背景/網格渲染，將數學計算委託給 `pose_math.py`。
* 📄 **[pose_math.py](file:///c:/Users/steven/Documents/Playground/pose_math.py)**：純函數數學幾何運算模組。負責關節旋轉、縮放、平移、解剖學水平鏡像、以及關節鄰近選取等純算法。
* 📄 **[pose_presets.py](file:///c:/Users/steven/Documents/Playground/pose_presets.py)**：存放 OpenPose 18點骨架連接拓樸圖、關節色彩定義、以及單人與雙人預設姿勢的標準坐標陣列。
* 📄 **[pose_io.py](file:///c:/Users/steven/Documents/Playground/pose_io.py)**：檔案輸入與輸出模組。利用 PySide6 的 headless `QImage` 進行高反鋸齒的無損渲染，並將結果儲存為 PNG/JPG。
* 📄 **[i18n.py](file:///c:/Users/steven/Documents/Playground/i18n.py)**：多語系語系檔模組，儲存所有中英文鍵值對翻譯與提供 `get_translation` 字典查找函數。
