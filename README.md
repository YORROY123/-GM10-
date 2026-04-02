# ❄️ 商錄冷庫 GM10 數位雙生系統

## 部署步驟（Streamlit Cloud）

### 方法一：Streamlit Community Cloud（免費）

1. 建立 GitHub repo，上傳以下兩個檔案：
   - `cold_storage_digital_twin.py`
   - `requirements.txt`

2. 至 [share.streamlit.io](https://share.streamlit.io) 登入

3. New app → 選擇你的 repo → Main file: `cold_storage_digital_twin.py`

4. Deploy！

### 方法二：本機執行

```bash
pip install -r requirements.txt
streamlit run cold_storage_digital_twin.py
```

---

## 使用方式

1. 開啟 App 後，在左側 Sidebar 上傳 `GM10_YYYY-MM-DD.csv`
2. 使用時間滑桿選取分析區間
3. 調整重採樣頻率（原始5秒 / 1分鐘 / 5分鐘）
4. 在警戒值設定庫內溫度上下限

---

## 功能說明

| 功能 | 說明 |
|------|------|
| 冷庫平面圖 | 8個庫內感測器即時溫度氣泡（色階代表溫度） |
| KPI 儀表板 | 平均溫/均勻度σ/壓縮機溫/濕度 |
| 時間序列 | CH1-CH8 + 平均溫度曲線 |
| 庫外環境 | CH101-CH106 溫度+濕度趨勢 |
| 統計分析 | 均勻度/溫差/直方圖/各CH平均 |
| 時間熱圖 | 時間×通道 溫度 Heatmap |
| 警報診斷 | 超限/均勻性/濕度異常自動偵測 |
| 資料匯出 | 下載篩選後 CSV |

---

## 感測器配置（依 PPTX 文件）

### GM10 Module 1（庫內）
| 位置 | 左 | 右 |
|------|----|----|
| 前排 | CH2 | CH1 |
| 中前 | CH4 | CH3 |
| 中後 | CH6 | CH5 |
| 後排 | CH8 | CH7 |

### GM10 Module 2（庫外）
- CH101：一號壓縮機溫度
- CH102：左T / CH103：前T / CH104：上T
- CH105：前H（溫溼度計）/ CH106：前T（溫溼度計）

---

**ITRI 綠能所 智慧控制設備研究室 ｜ GB+44015-2026**
