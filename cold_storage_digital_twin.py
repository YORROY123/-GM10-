"""
商錄冷庫 GM10 數位雙生系統
Digital Twin for GM10 Cold Storage - Streamlit App
ITRI 智慧控制設備研究室
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="商錄冷庫 GM10 數位雙生系統",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Light theme base */
    .stApp { background-color: #f5f7fa; color: #1a2a45; }
    .main .block-container { padding: 1rem 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #eaf2fb 100%);
        border: 1px solid #b3d1ec;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,100,200,0.10);
    }
    .kpi-label { font-size: 0.75rem; color: #2a6496; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
    .kpi-value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .kpi-unit  { font-size: 0.85rem; color: #2a6496; }
    .kpi-delta { font-size: 0.78rem; margin-top: 4px; }

    /* Section headers */
    .section-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1565c0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 12px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 2px solid #90caf9;
    }

    /* Status badge */
    .badge-ok   { background:#e8f5e9; color:#2e7d32; border:1px solid #4caf50; border-radius:6px; padding:2px 10px; font-size:0.78rem; }
    .badge-warn { background:#fff8e1; color:#f57f17; border:1px solid #ffb300; border-radius:6px; padding:2px 10px; font-size:0.78rem; }
    .badge-err  { background:#ffebee; color:#c62828; border:1px solid #f44336; border-radius:6px; padding:2px 10px; font-size:0.78rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #e8f0fb; border-right: 1px solid #b3d1ec; }
    section[data-testid="stSidebar"] .stMarkdown h2 { color: #1565c0; }

    /* Plotly chart backgrounds */
    .js-plotly-plot { border-radius: 10px; border: 1px solid #d0e4f7; }

    /* Alert box */
    .alert-box {
        background: #ffebee;
        border-left: 4px solid #f44336;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #c62828;
    }
    .warn-box {
        background: #fff8e1;
        border-left: 4px solid #ffb300;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #f57f17;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sensor Layout Definition
# ─────────────────────────────────────────────
# 3D positions: x=左右(0=左,1=右), y=前後(0=前,1=後), z=上下(0=下,1=上)
# Based on PPTX diagram: 8 corners of the cold storage box
INSIDE_SENSORS = {
    # x:0=左,1=右 | y:0=前,1=後 | z:0=下,1=上
    # 使用者確認:
    # CH1=後右上, CH2=前右上, CH3=前左上, CH4=後左上
    # CH5=後右下, CH6=前右下, CH7=前左下, CH8=後左下
    'CH1': {'label': 'CH1 後右上', 'col_key': 'CH1(測試通道_01)', 'pos': (1, 1, 1)},
    'CH2': {'label': 'CH2 前右上', 'col_key': 'CH2(測試通道_02)', 'pos': (1, 0, 1)},
    'CH3': {'label': 'CH3 前左上', 'col_key': 'CH3(通道 3)',      'pos': (0, 0, 1)},
    'CH4': {'label': 'CH4 後左上', 'col_key': 'CH4(通道 4)',      'pos': (0, 1, 1)},
    'CH5': {'label': 'CH5 後右下', 'col_key': 'CH5(通道 5)',      'pos': (1, 1, 0)},
    'CH6': {'label': 'CH6 前右下', 'col_key': 'CH6(通道 6)',      'pos': (1, 0, 0)},
    'CH7': {'label': 'CH7 前左下', 'col_key': 'CH7(通道 7)',      'pos': (0, 0, 0)},
    'CH8': {'label': 'CH8 後左下', 'col_key': 'CH8(通道 8)',      'pos': (0, 1, 0)},
}

OUTSIDE_SENSORS = {
    'CH104': {'label': 'CH104\n上T',   'col_key': 'CH104(通道 104)', 'unit': '°C'},
    'CH101': {'label': 'CH101\n壓縮機', 'col_key': 'CH101(一號壓縮機)', 'unit': '°C'},
    'CH102': {'label': 'CH102\n左T',   'col_key': 'CH102(通道 102)', 'unit': '°C'},
    'CH103': {'label': 'CH103\n前T',   'col_key': 'CH103(通道 103)', 'unit': '°C'},
    'CH106': {'label': 'CH106\n前T(溫溼)',  'col_key': 'CH106(關鍵數據 (CH106))', 'unit': '°C'},
    'CH105': {'label': 'CH105\n前H(溫溼)',  'col_key': 'CH105(通道 105)', 'unit': '%RH'},
}

# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, parse_dates=['時間'])
    else:
        # Try default path
        default = "GM10_2026-03-30.csv"
        if os.path.exists(default):
            df = pd.read_csv(default, parse_dates=['時間'])
        else:
            return None
    df = df.sort_values('時間').reset_index(drop=True)
    # Compute derived columns
    inside_cols = [s['col_key'] for s in INSIDE_SENSORS.values()]
    df['avg_inside_T'] = df[inside_cols].mean(axis=1)
    df['max_inside_T'] = df[inside_cols].max(axis=1)
    df['min_inside_T'] = df[inside_cols].min(axis=1)
    df['uniformity']   = df[inside_cols].std(axis=1)   # lower = more uniform
    return df

# ─────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────
def temp_color(val, vmin=-25, vmax=-10):
    """Map temperature to a blue-cyan-white scale."""
    ratio = (val - vmin) / (vmax - vmin)
    ratio = max(0, min(1, ratio))
    # cold (blue) → warm (cyan/white)
    r = int(30 + 200 * ratio)
    g = int(80 + 160 * ratio)
    b = int(200 + 55 * ratio)
    return f'rgb({r},{g},{b})'

def badge_html(status):
    cls = {'ok': 'badge-ok', 'warn': 'badge-warn', 'err': 'badge-err'}.get(status, 'badge-ok')
    label = {'ok': '✅ 正常', 'warn': '⚠️ 注意', 'err': '🚨 異常'}.get(status, '正常')
    return f'<span class="{cls}">{label}</span>'

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ❄️ GM10 數位雙生")
    st.markdown("**商錄冷庫監控系統**")
    st.markdown("---")

    uploaded = st.file_uploader("📂 上傳 CSV 資料", type=["csv"],
                                help="格式：GM10_YYYY-MM-DD.csv")
    st.markdown("---")
    st.markdown("### ⚙️ 顯示設定")
    resample_opt = st.selectbox("資料重採樣", ["原始(5秒)", "30秒", "1分鐘", "5分鐘", "15分鐘"],
                                index=2)
    show_raw = st.checkbox("顯示原始通道曲線", value=True)
    show_stats = st.checkbox("顯示統計分析", value=True)

    st.markdown("---")
    st.markdown("### 🌡️ 溫度警戒值")
    alarm_high = st.slider("庫內上限 (°C)", -30, -5, -10, 1)
    alarm_low  = st.slider("庫內下限 (°C)", -40, -20, -30, 1)

    st.markdown("---")
    st.markdown("### ℹ️ 系統資訊")
    st.markdown("""
    - **專案**: GB+44015-2026
    - **單位**: 綠能所 智慧控制設備研究室
    - **模組**: GM10 Module 1&2
    """)

# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────
df_raw = load_data(uploaded)

if df_raw is None:
    st.title("❄️ 商錄冷庫 GM10 數位雙生系統")
    st.warning("請在左側上傳 GM10 CSV 資料檔案")
    st.info("資料格式：GM10_YYYY-MM-DD.csv（GM10 記錄器輸出）")
    st.stop()

# Resample
resample_map = {"原始(5秒)": None, "30秒": "30s", "1分鐘": "1min",
                "5分鐘": "5min", "15分鐘": "15min"}
rs = resample_map[resample_opt]
if rs:
    df = df_raw.set_index('時間').resample(rs).mean().reset_index()
else:
    df = df_raw.copy()

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("# ❄️ 商錄冷庫 GM10 數位雙生系統")
    st.markdown("**GB+44015-2026 ｜ 綠能所 智慧控制設備研究室**")
with col_date:
    date_str = df['時間'].iloc[-1].strftime('%Y-%m-%d')
    t_start  = df['時間'].iloc[0].strftime('%H:%M:%S')
    t_end    = df['時間'].iloc[-1].strftime('%H:%M:%S')
    st.markdown(f"""
    <div class='kpi-card' style='text-align:left; margin-top:10px;'>
        <div class='kpi-label'>資料日期</div>
        <div style='font-size:1.1rem; font-weight:600; color:#4fc3f7;'>{date_str}</div>
        <div style='font-size:0.8rem; color:#7ab3d4;'>{t_start} → {t_end}</div>
        <div style='font-size:0.78rem; color:#7ab3d4; margin-top:4px;'>共 {len(df_raw)} 筆（5秒間隔）</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# Time Range Slider
# ─────────────────────────────────────────────
t_min = df['時間'].min().to_pydatetime()
t_max = df['時間'].max().to_pydatetime()

col_sl1, col_sl2 = st.columns([4, 1])
with col_sl1:
    time_range = st.slider(
        "⏱️ 時間範圍",
        min_value=t_min, max_value=t_max,
        value=(t_min, t_max),
        format="HH:mm:ss",
        label_visibility="collapsed"
    )
with col_sl2:
    st.markdown(f"""
    <div style='padding-top:8px; font-size:0.82rem; color:#7ab3d4;'>
    {time_range[0].strftime('%H:%M')} → {time_range[1].strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

dff = df[(df['時間'] >= time_range[0]) & (df['時間'] <= time_range[1])]
if len(dff) == 0:
    st.error("選取時間範圍內無資料")
    st.stop()

latest = dff.iloc[-1]
inside_cols = [s['col_key'] for s in INSIDE_SENSORS.values()]

# ─────────────────────────────────────────────
# KPI Cards Row
# ─────────────────────────────────────────────
st.markdown("<div class='section-title'>📊 即時關鍵指標</div>", unsafe_allow_html=True)

inside_vals = [latest[s['col_key']] for s in INSIDE_SENSORS.values()]
avg_T   = np.mean(inside_vals)
max_T   = np.max(inside_vals)
min_T   = np.min(inside_vals)
unif    = np.std(inside_vals)
comp_T  = latest['CH101(一號壓縮機)']
humid   = latest['CH105(通道 105)']
amb_T   = latest['CH106(關鍵數據 (CH106))']

# Alarm logic
if avg_T > alarm_high:
    alarm_status = 'err'
elif avg_T > alarm_high - 2:
    alarm_status = 'warn'
elif avg_T < alarm_low:
    alarm_status = 'warn'
else:
    alarm_status = 'ok'

kpi_cols = st.columns(7)
kpis = [
    ("庫內平均溫度", f"{avg_T:.1f}", "°C", f"{'🔴' if alarm_status=='err' else '🟡' if alarm_status=='warn' else '🟢'} {badge_html(alarm_status)}"),
    ("庫內最高溫度", f"{max_T:.1f}", "°C", f"min: {min_T:.1f}°C"),
    ("溫度均勻度",   f"±{unif:.2f}", "°C", "σ 標準差"),
    ("壓縮機溫度",   f"{comp_T:.1f}", "°C", "CH101"),
    ("環境溫度(前)", f"{amb_T:.1f}", "°C", "CH106 溫溼度計"),
    ("環境濕度(前)", f"{humid:.1f}", "%RH", "CH105 溫溼度計"),
    ("資料點數",     f"{len(dff):,}", "筆", f"Δt={resample_opt}"),
]

for col, (label, val, unit, delta) in zip(kpi_cols, kpis):
    col.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value' style='color:#{"f44336" if "🔴" in delta else "ffb300" if "🟡" in delta else "4fc3f7"};'>{val}</div>
        <div class='kpi-unit'>{unit}</div>
        <div class='kpi-delta'>{delta}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Layout: Floor Plan + Time Series
# ─────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

# ── LEFT: Module 1 (庫內) + Module 2 (庫外) ──
with col_left:
    st.markdown("""
    <div style='background:linear-gradient(90deg,#0d2040,#0a1a30);
         border:1px solid #1e5f9f; border-radius:8px; padding:8px 14px; margin-bottom:8px;
         font-size:0.82rem; color:#7ab3d4; text-align:center;'>
        🔬 <b style='color:#4fc3f7'>GM10 儀器</b> &nbsp;|&nbsp;
        <span style='color:#42a5f5'>Module 1 庫內</span> (CH1-CH8) &nbsp;+&nbsp;
        <span style='color:#ffa726'>Module 2 庫外</span> (CH101-CH106)
    </div>
    """, unsafe_allow_html=True)

    mod_tab1, mod_tab2 = st.tabs(["❄️ Module 1 庫內 3D", "🌡️ Module 2 庫外"])

    with mod_tab1:
        st.markdown("<div class='section-title'>Module 1 — 庫內 8點溫度分布（2×4 量測點）</div>",
                    unsafe_allow_html=True)
        fig_floor = go.Figure()

        # Box edges: connect the 8 corners
        # Corners: (x, y, z)  x=左右, y=前後, z=上下
        corners = {
            'A': (0,0,1), 'B': (1,0,1),  # front-top: left, right
            'C': (0,0,0), 'D': (1,0,0),  # front-bot: left, right
            'E': (0,1,1), 'F': (1,1,1),  # back-top:  left, right
            'G': (0,1,0), 'H': (1,1,0),  # back-bot:  left, right
        }
    # Edges list (pairs of corners)
        edges = [
            # front face
            ('A','B'), ('A','C'), ('B','D'), ('C','D'),
            # back face
            ('E','F'), ('E','G'), ('F','H'), ('G','H'),
            # connecting edges (solid for visible, dashed for hidden)
            ('A','E'), ('B','F'),  # top edges
            ('C','G'), ('D','H'),  # bottom edges
        ]
        # Hidden edges (dashed): C-G, D-H → typically back-bottom hidden in perspective
        hidden_edges = {('C','G'), ('D','H'), ('E','G'), ('G','H')}

        def add_edge(p1, p2, dashed=False):
            x0,y0,z0 = corners[p1]
            x1,y1,z1 = corners[p2]
            fig_floor.add_trace(go.Scatter3d(
                x=[x0,x1,None], y=[y0,y1,None], z=[z0,z1,None],
                mode='lines',
                line=dict(
                    color='rgba(30,80,160,0.7)' if not dashed else 'rgba(30,80,160,0.3)',
                    width=3 if not dashed else 2,
                    dash='dash' if dashed else 'solid'
                ),
                showlegend=False, hoverinfo='skip'
            ))

        for p1, p2 in edges:
            add_edge(p1, p2, dashed=(p1,p2) in hidden_edges or (p2,p1) in hidden_edges)

        # Sensor nodes
        vals = [latest[s['col_key']] for s in INSIDE_SENSORS.values()]
        vmin_t, vmax_t = min(vals) - 1, max(vals) + 1

        xs, ys, zs, colors_3d, sizes_3d, texts, hovers = [], [], [], [], [], [], []
        for name, s in INSIDE_SENSORS.items():
            x, y, z = s['pos']
            val = latest[s['col_key']]
            ratio = (val - vmin_t) / max(vmax_t - vmin_t, 0.1)
            # Blue (cold) → Cyan (warmer)
            r = int(20 + 180 * ratio)
            g = int(100 + 120 * ratio)
            b = int(220 + 30 * ratio)
            xs.append(x); ys.append(y); zs.append(z)
            colors_3d.append(f'rgb({r},{g},{b})')
            sizes_3d.append(22)
            texts.append(f"{val:.1f}°C")
            hovers.append(f"<b>{name}</b><br>{s['label']}<br>溫度: {val:.2f}°C")

        fig_floor.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers+text',
            marker=dict(
                size=sizes_3d, opacity=0.95,
                line=dict(color='white', width=1.5),
                colorscale=[[0,'rgb(20,60,200)'],[0.5,'rgb(50,160,220)'],[1,'rgb(150,220,255)']],
                cmin=vmin_t, cmax=vmax_t,
                colorbar=dict(
                    title=dict(text="°C", font=dict(color='#1565c0', size=11)),
                    tickfont=dict(color='#1a2a45', size=9),
                    thickness=10, len=0.5, x=1.0,
                    bgcolor='rgba(245,247,250,0)',
                ),
                showscale=True,
                color=vals,
            ),
            text=texts,
            textposition='top center',
            textfont=dict(size=10, color='white', family='Arial Black'),
            hovertext=hovers,
            hoverinfo='text',
            showlegend=False,
            name='感測器',
        ))

        # Sensor name labels (offset slightly)
        ch_names = list(INSIDE_SENSORS.keys())
        label_offsets = {'CH1':(0.12,0,0.08), 'CH2':(-0.12,0,0.08),
                         'CH3':(-0.12,0,-0.08), 'CH4':(0.12,0,-0.08),
                         'CH5':(0.12,0,0.08), 'CH6':(-0.12,0,0.08),
                         'CH7':(-0.12,0,-0.08), 'CH8':(0.12,0,-0.08)}
        lx,ly,lz,ltxt = [],[],[],[]
        for name, s in INSIDE_SENSORS.items():
            ox,oy,oz = label_offsets.get(name,(0,0,0.1))
            x,y,z = s['pos']
            lx.append(x+ox); ly.append(y+oy); lz.append(z+oz)
            ltxt.append(name)
        fig_floor.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz, mode='text',
            text=ltxt,
            textfont=dict(size=9, color='#1565c0'),
            showlegend=False, hoverinfo='skip'
        ))

        # Face labels (前面/後面)
        fig_floor.add_trace(go.Scatter3d(
            x=[0.5, 0.5], y=[-0.15, 1.15], z=[0.5, 0.5],
            mode='text',
            text=['前面', '後面'],
            textfont=dict(size=12, color='#f0b030'),
            showlegend=False, hoverinfo='skip'
        ))

        # Alarm warning text in 3D
        alarm_text = ''
        if avg_T > alarm_high:
            alarm_text = f'⚠️ 超限 {avg_T:.1f}°C'

        fig_floor.update_layout(
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='',
                           showspikes=False),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='',
                           showspikes=False),
                zaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='',
                           showspikes=False),
                bgcolor='rgba(245,247,250,1)',
                camera=dict(
                    eye=dict(x=-1.6, y=-1.8, z=1.2),   # 仿 PPTX 視角
                    up=dict(x=0, y=0, z=1),
                ),
                aspectmode='cube',
            ),
            paper_bgcolor='#f5f7fa',
            height=420,
            margin=dict(l=0, r=60, t=10, b=0),
        )

        st.plotly_chart(fig_floor, use_container_width=True, config={'displayModeBar': False})

        # Legend for Module 1 layout
        st.markdown("""
        <div style='font-size:0.75rem; color:#5a8aaa; text-align:center; margin-top:-10px;'>
        🖱️ 可拖曳旋轉 3D 視角 &nbsp;｜&nbsp;
        左欄=左(L) &nbsp; 右欄=右(R) &nbsp; 上列=前面 &nbsp; 下列=後面
        </div>
        <table style='width:100%; font-size:0.78rem; color:#7ab3d4;
               border-collapse:collapse; margin-top:6px; text-align:center;'>
          <tr style='background:#0d2040;'>
            <td style='border:1px solid #1e3a5f; padding:3px;'>CH2 前左上</td>
            <td style='border:1px solid #1e3a5f; padding:3px;'>CH1 前右上</td>
          </tr>
          <tr><td style='border:1px solid #1e3a5f; padding:3px;'>CH4 前左下</td>
              <td style='border:1px solid #1e3a5f; padding:3px;'>CH3 前右下</td></tr>
          <tr><td style='border:1px solid #1e3a5f; padding:3px;'>CH6 後左上</td>
              <td style='border:1px solid #1e3a5f; padding:3px;'>CH5 後右上</td></tr>
          <tr style='background:#0d2040;'>
            <td style='border:1px solid #1e3a5f; padding:3px;'>CH8 後左下</td>
            <td style='border:1px solid #1e3a5f; padding:3px;'>CH7 後右下</td>
          </tr>
        </table>
        """, unsafe_allow_html=True)

        if avg_T > alarm_high:
            st.markdown(f"<div class='alert-box'>🚨 庫內平均溫度超限：{avg_T:.1f}°C > {alarm_high}°C</div>",
                        unsafe_allow_html=True)

    # ── Module 2 Tab ──
    with mod_tab2:
        st.markdown("<div class='section-title'>Module 2 — 庫外感測器（冷庫機體外壁）</div>",
                    unsafe_allow_html=True)

        # Module 2 outside sensor layout (對照 PPTX Module2 圖):
        # CH104[上T]  → 頂部中央
        # CH101[右T]  → 右牆面中央（壓縮機）
        # CH102[左T]  → 左牆面，前下方（PPTX顯示在左前下角）
        # CH103[前T]  → 前牆面中上
        # CH106[前T溫溼] → 前牆面左中
        # CH105[前H溼]   → 前牆面左下（與CH106同側）

        out2_sensors = [
            {'name':'CH104', 'label':'CH104\n上T',
             'col':'CH104(通道 104)',         'unit':'°C',
             'pos':(0.5, 0.5, 1.42), 'color':'#ffa726'},
            {'name':'CH101', 'label':'CH101\n右T(壓縮機)',
             'col':'CH101(一號壓縮機)', 'unit':'°C',
             'pos':(-0.42, 0.8, 0.15), 'color':'#ef5350'},
            {'name':'CH102', 'label':'CH102\n左T',
             'col':'CH102(通道 102)', 'unit':'°C',
             'pos':(1.42, 0.3, 0.55), 'color':'#42a5f5'},
            {'name':'CH103', 'label':'CH103\n前T',
             'col':'CH103(通道 103)', 'unit':'°C',
             'pos':(0.55, -0.42, 0.65), 'color':'#66bb6a'},
            {'name':'CH106', 'label':'CH106\n前T(溫溼度計)',
             'col':'CH106(關鍵數據 (CH106))', 'unit':'°C',
             'pos':(0.2, -0.42, 0.38), 'color':'#ab47bc'},
            {'name':'CH105', 'label':'CH105\n前H(溫溼度計)',
             'col':'CH105(通道 105)', 'unit':'%RH',
             'pos':(0.2, -0.42, 0.18), 'color':'#26c6da'},
        ]

        fig_out3d = go.Figure()

        # Draw the cold storage box (semi-transparent)
        corners2 = {
            'A':(0,0,1),'B':(1,0,1),'C':(0,0,0),'D':(1,0,0),
            'E':(0,1,1),'F':(1,1,1),'G':(0,1,0),'H':(1,1,0),
        }
        edges2 = [('A','B'),('A','C'),('B','D'),('C','D'),
                  ('E','F'),('F','H'),('B','F'),('D','H'),
                  ('A','E'),('E','G'),('G','H'),('C','G')]
        for p1,p2 in edges2:
            x0,y0,z0 = corners2[p1]; x1,y1,z1 = corners2[p2]
            fig_out3d.add_trace(go.Scatter3d(
                x=[x0,x1,None], y=[y0,y1,None], z=[z0,z1,None],
                mode='lines',
                line=dict(color='rgba(30,80,160,0.5)', width=2),
                showlegend=False, hoverinfo='skip'
            ))
        # Semi-transparent box fill (front face hint)
        fig_out3d.add_trace(go.Mesh3d(
            x=[0,1,1,0], y=[0,0,0,0], z=[0,0,1,1],
            color='rgba(30,80,160,0.08)', opacity=0.08,
            showlegend=False, hoverinfo='skip'
        ))

        # Outside sensor nodes
        for s in out2_sensors:
            val = latest[s['col']]
            sz  = 18 if s['unit'] == '°C' else 20
            x,y,z = s['pos']
            label_short = s['name']
            val_str = f"{val:.1f}{s['unit']}"
            fig_out3d.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers+text',
                marker=dict(size=sz, color=s['color'], opacity=0.92,
                            symbol='circle',
                            line=dict(color='white', width=1.5)),
                text=[val_str],
                textposition='top center',
                textfont=dict(size=10, color='white', family='Arial Black'),
                name=s['name'],
                hovertemplate=f"<b>{s['name']}</b><br>{s['label'].replace(chr(10),' ')}<br>{val:.2f} {s['unit']}<extra></extra>",
                showlegend=True,
            ))
            # Line from sensor to box surface (connector)
            # Find nearest box face point
            bx = max(0, min(1, x)); by = max(0, min(1, y)); bz = max(0, min(1, z))
            fig_out3d.add_trace(go.Scatter3d(
                x=[x, bx, None], y=[y, by, None], z=[z, bz, None],
                mode='lines',
                line=dict(color=s['color'], width=1.5, dash='dot'),
                showlegend=False, hoverinfo='skip'
            ))

        # Labels
        fig_out3d.add_trace(go.Scatter3d(
            x=[0.5, 0.5], y=[-0.15, 1.15], z=[0.5, 0.5],
            mode='text', text=['前面', '後面'],
            textfont=dict(size=11, color='#f0b030'),
            showlegend=False, hoverinfo='skip'
        ))

        fig_out3d.update_layout(
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='', showspikes=False,
                           range=[-0.6, 1.6]),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='', showspikes=False,
                           range=[-0.6, 1.6]),
                zaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                           backgroundcolor='rgba(245,247,250,0)', title='', showspikes=False,
                           range=[-0.2, 1.6]),
                bgcolor='rgba(245,247,250,1)',
                camera=dict(eye=dict(x=-1.8, y=-1.8, z=1.2), up=dict(x=0,y=0,z=1)),
                aspectmode='cube',
            ),
            legend=dict(orientation="h", y=-0.05, font=dict(size=9, color='#1565c0'),
                        bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor='#f5f7fa',
            height=380,
            margin=dict(l=0, r=10, t=5, b=0),
        )
        st.plotly_chart(fig_out3d, use_container_width=True, config={'displayModeBar': False})

        # Module 2 value cards
        cols_m2 = st.columns(2)
        for i, s in enumerate(out2_sensors):
            val = latest[s['col']]
            cols_m2[i % 2].markdown(f"""
            <div class='kpi-card' style='margin-bottom:4px; padding:8px 10px;'>
                <div class='kpi-label' style='color:{s["color"]};'>{s['name']}</div>
                <div style='font-size:1.3rem; font-weight:700; color:{s["color"]};'>{val:.1f}</div>
                <div class='kpi-unit'>{s['unit']}</div>
            </div>
            """, unsafe_allow_html=True)

# ── RIGHT: Time Series Chart ──
with col_right:
    st.markdown("<div class='section-title'>📈 時間序列曲線</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔵 庫內溫度 (CH1-CH8)", "🟠 庫外環境", "📊 統計趨勢"])

    # ── Tab 1: Inside temperatures ──
    with tab1:
        # ── 疊圖 / 不疊圖 切換 ──
        overlay_mode = st.radio(
            "顯示模式",
            ["📊 疊圖（所有通道同一張）", "📋 不疊圖（各通道分開）"],
            horizontal=True, label_visibility="collapsed"
        )
        overlay = "疊圖" in overlay_mode

        colors_inside = ['#ef5350','#ffa726','#ffee58','#66bb6a',
                         '#42a5f5','#ab47bc','#26c6da','#ff7043']
        ch_list = list(INSIDE_SENSORS.items())

        if overlay:
            # ── 疊圖模式 ──
            fig_inside = go.Figure()
            for i, (name, s) in enumerate(ch_list):
                fig_inside.add_trace(go.Scatter(
                    x=dff['時間'], y=dff[s['col_key']],
                    name=f"{name} {s['label'].split(' ')[1]}",
                    line=dict(width=1.8, color=colors_inside[i]),
                    opacity=0.9,
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}°C<extra></extra>"
                ))
            # Average line
            fig_inside.add_trace(go.Scatter(
                x=dff['時間'], y=dff['avg_inside_T'],
                name='平均', line=dict(width=2.5, color='white', dash='dash'),
                hovertemplate="平均: %{y:.2f}°C<extra></extra>"
            ))
            fig_inside.add_hrect(y0=alarm_high, y1=alarm_high+5,
                                 fillcolor="rgba(244,67,54,0.08)", line_width=0)
            fig_inside.add_hline(y=alarm_high, line=dict(color="#f44336", dash="dot", width=1.5),
                                 annotation_text=f"上限 {alarm_high}°C",
                                 annotation_font_color="#f44336")
            fig_inside.add_hline(y=alarm_low, line=dict(color="#ff9800", dash="dot", width=1.5),
                                 annotation_text=f"下限 {alarm_low}°C",
                                 annotation_font_color="#ff9800")
            fig_inside.update_layout(
                plot_bgcolor='#ffffff', paper_bgcolor='#f5f7fa',
                height=400, margin=dict(l=10, r=10, t=15, b=10),
                legend=dict(orientation="h", y=-0.18, font=dict(size=10, color='#1565c0'),
                            bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor='#d0e4f7', tickfont=dict(color='#1a2a45')),
                yaxis=dict(gridcolor='#d0e4f7', tickfont=dict(color='#1a2a45'),
                           title=dict(text="溫度 (°C)", font=dict(color='#1565c0'))),
                hovermode='x unified',
            )
            st.plotly_chart(fig_inside, use_container_width=True)

        else:
            # ── 不疊圖模式：2×4 subplots ──
            fig_sub = make_subplots(
                rows=4, cols=2,
                shared_xaxes=True,
                vertical_spacing=0.04,
                horizontal_spacing=0.06,
                subplot_titles=[f"{n} {s['label'].split(' ')[1]}"
                                for n, s in ch_list],
            )
            for i, (name, s) in enumerate(ch_list):
                row = i // 2 + 1
                col = i % 2 + 1
                fig_sub.add_trace(go.Scatter(
                    x=dff['時間'], y=dff[s['col_key']],
                    name=name,
                    line=dict(width=1.5, color=colors_inside[i]),
                    fill='tozeroy',
                    fillcolor=colors_inside[i].replace(')', ',0.08)').replace('rgb', 'rgba'),
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}°C<extra></extra>",
                    showlegend=False,
                ), row=row, col=col)
                # Alarm line per subplot
                fig_sub.add_hline(y=alarm_high, row=row, col=col,
                                  line=dict(color="#f44336", dash="dot", width=1))

            fig_sub.update_layout(
                plot_bgcolor='#ffffff', paper_bgcolor='#f5f7fa',
                height=700, margin=dict(l=10, r=10, t=30, b=10),
                hovermode='x unified',
            )
            for ann in fig_sub.layout.annotations:
                ann.font.color = "#7ab3d4"
                ann.font.size = 10
            for ax in [f'xaxis{i}' if i > 1 else 'xaxis' for i in range(1, 9)] + \
                       [f'yaxis{i}' if i > 1 else 'yaxis' for i in range(1, 9)]:
                fig_sub.update_layout(**{ax: dict(
                    gridcolor='#d0e4f7', tickfont=dict(color='#1a2a45', size=8),
                    title_font=dict(color='#1565c0')
                )})
            st.plotly_chart(fig_sub, use_container_width=True)

    # ── Tab 2: Outside environment ──
    with tab2:
        fig_out = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.6, 0.4],
                                subplot_titles=["庫外溫度 (°C)", "濕度 (%RH)"],
                                vertical_spacing=0.08)
        # Temperature channels
        out_temp_sensors = ['CH101(一號壓縮機)', 'CH102(通道 102)',
                            'CH103(通道 103)', 'CH104(通道 104)', 'CH106(關鍵數據 (CH106))']
        out_temp_labels  = ['CH101 壓縮機', 'CH102 左T', 'CH103 前T', 'CH104 上T', 'CH106 前T(溫溼)']
        colors_out = ['#ff6b6b', '#ffa726', '#42a5f5', '#66bb6a', '#ab47bc']
        for col_, lbl, color in zip(out_temp_sensors, out_temp_labels, colors_out):
            fig_out.add_trace(go.Scatter(
                x=dff['時間'], y=dff[col_], name=lbl,
                line=dict(width=2, color=color),
                hovertemplate=f"{lbl}: %{{y:.2f}}°C<extra></extra>"
            ), row=1, col=1)
        # Humidity
        fig_out.add_trace(go.Scatter(
            x=dff['時間'], y=dff['CH105(通道 105)'],
            name='CH105 濕度', fill='tozeroy',
            line=dict(width=2, color='#4fc3f7'),
            fillcolor='rgba(79,195,247,0.15)',
            hovertemplate="濕度: %{y:.1f}%RH<extra></extra>"
        ), row=2, col=1)
        fig_out.update_layout(
            plot_bgcolor='#ffffff', paper_bgcolor='#f5f7fa',
            height=400, margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.12, font=dict(size=10, color='#1565c0'),
                        bgcolor="rgba(0,0,0,0)"),
            hovermode='x unified',
        )
        for axis in ['xaxis', 'xaxis2', 'yaxis', 'yaxis2']:
            fig_out.update_layout(**{axis: dict(gridcolor='#d0e4f7',
                                                tickfont=dict(color='#1a2a45'))})
        # Subplot title color fix
        for ann in fig_out.layout.annotations:
            ann.font.color = "#7ab3d4"
        st.plotly_chart(fig_out, use_container_width=True)

    # ── Tab 3: Stats ──
    with tab3:
        fig_stat = make_subplots(rows=2, cols=2,
                                 subplot_titles=["溫度均勻度 σ (°C)",
                                                 "庫內 Max-Min 溫差 (°C)",
                                                 "庫內平均溫度分布",
                                                 "各通道平均溫度"],
                                 vertical_spacing=0.15, horizontal_spacing=0.1)
        # Uniformity
        fig_stat.add_trace(go.Scatter(
            x=dff['時間'], y=dff['uniformity'],
            fill='tozeroy', line=dict(color='#4fc3f7', width=1.5),
            fillcolor='rgba(79,195,247,0.15)', name='σ',
            hovertemplate="σ: %{y:.3f}°C<extra></extra>"
        ), row=1, col=1)
        # Max-Min span
        span = dff['max_inside_T'] - dff['min_inside_T']
        fig_stat.add_trace(go.Scatter(
            x=dff['時間'], y=span,
            fill='tozeroy', line=dict(color='#ff9800', width=1.5),
            fillcolor='rgba(255,152,0,0.15)', name='Max-Min',
            hovertemplate="差: %{y:.2f}°C<extra></extra>"
        ), row=1, col=2)
        # Histogram of avg temp
        fig_stat.add_trace(go.Histogram(
            x=dff['avg_inside_T'], nbinsx=40,
            marker_color='#4fc3f7', opacity=0.8, name='分布',
        ), row=2, col=1)
        # Bar chart: channel averages
        ch_avg = {name: dff[s['col_key']].mean() for name, s in INSIDE_SENSORS.items()}
        fig_stat.add_trace(go.Bar(
            x=list(ch_avg.keys()), y=list(ch_avg.values()),
            marker_color=['#42a5f5' if v < alarm_high else '#f44336' for v in ch_avg.values()],
            name='各CH平均',
            hovertemplate="%{x}: %{y:.2f}°C<extra></extra>"
        ), row=2, col=2)
        fig_stat.update_layout(
            plot_bgcolor='#ffffff', paper_bgcolor='#f5f7fa',
            height=420, margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        for axis in ['xaxis', 'xaxis2', 'xaxis3', 'xaxis4',
                     'yaxis', 'yaxis2', 'yaxis3', 'yaxis4']:
            fig_stat.update_layout(**{axis: dict(gridcolor='#d0e4f7',
                                                  tickfont=dict(color='#1a2a45'))})
        for ann in fig_stat.layout.annotations:
            ann.font.color = "#7ab3d4"
        st.plotly_chart(fig_stat, use_container_width=True)

# ─────────────────────────────────────────────
# Bottom Row: Heatmap + Alerts
# ─────────────────────────────────────────────
st.markdown("---")
col_hm, col_alert = st.columns([3, 1])

with col_hm:
    st.markdown("<div class='section-title'>🗓️ 時間-通道 溫度熱圖</div>", unsafe_allow_html=True)
    # Sample for heatmap (max 300 points)
    step = max(1, len(dff) // 300)
    df_hm = dff.iloc[::step]
    z_data = df_hm[[s['col_key'] for s in INSIDE_SENSORS.values()]].T.values
    ch_labels = [f"{n} ({s['label'].split(' ')[1]})" for n, s in INSIDE_SENSORS.items()]
    fig_hm = go.Figure(go.Heatmap(
        z=z_data,
        x=df_hm['時間'].dt.strftime('%H:%M'),
        y=ch_labels,
        colorscale=[[0,'#0a2463'],[0.4,'#1e5f9f'],[0.7,'#42a5f5'],[1,'#e3f2fd']],
        hoverongaps=False,
        colorbar=dict(title=dict(text="°C", font=dict(color='#1565c0')),
                      tickfont=dict(color='#1a2a45'), thickness=12),
        hovertemplate="%{y}<br>時間: %{x}<br>溫度: %{z:.2f}°C<extra></extra>"
    ))
    fig_hm.update_layout(
        plot_bgcolor='#ffffff', paper_bgcolor='#f5f7fa',
        height=260, margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(tickfont=dict(size=9, color='#1565c0'), nticks=12),
        yaxis=dict(tickfont=dict(size=9, color='#1565c0')),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

with col_alert:
    st.markdown("<div class='section-title'>🚨 警報與診斷</div>", unsafe_allow_html=True)

    alerts = []
    # Check inside temperature
    for name, s in INSIDE_SENSORS.items():
        v = latest[s['col_key']]
        if v > alarm_high:
            alerts.append(('err', f"{name} 溫度超上限: {v:.1f}°C"))
        elif v < alarm_low:
            alerts.append(('warn', f"{name} 溫度低於下限: {v:.1f}°C"))

    # Check uniformity
    if unif > 1.5:
        alerts.append(('warn', f"溫度均勻性差: σ={unif:.2f}°C"))

    # Check humidity
    if humid > 90:
        alerts.append(('err', f"濕度過高: {humid:.1f}%RH"))
    elif humid < 60:
        alerts.append(('warn', f"濕度偏低: {humid:.1f}%RH"))

    # Check compressor
    if comp_T > 40:
        alerts.append(('err', f"壓縮機溫度高: {comp_T:.1f}°C"))
    elif comp_T > 35:
        alerts.append(('warn', f"壓縮機溫度偏高: {comp_T:.1f}°C"))

    if not alerts:
        st.markdown("<div class='badge-ok' style='padding:8px 12px; font-size:0.9rem;'>✅ 系統運作正常<br>無警報</div>", unsafe_allow_html=True)
    else:
        for level, msg in alerts:
            css_cls = 'alert-box' if level == 'err' else 'warn-box'
            icon = '🚨' if level == 'err' else '⚠️'
            st.markdown(f"<div class='{css_cls}'>{icon} {msg}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # Summary stats box
    st.markdown(f"""
    <div class='kpi-card' style='text-align:left;'>
        <div class='kpi-label'>選取區間統計</div>
        <div style='font-size:0.82rem; color:#e0e8f0; line-height:1.8;'>
        📊 點數: {len(dff):,}<br>
        🌡️ 平均: {dff['avg_inside_T'].mean():.2f}°C<br>
        🔺 最高: {dff['max_inside_T'].max():.2f}°C<br>
        🔻 最低: {dff['min_inside_T'].min():.2f}°C<br>
        📐 平均σ: {dff['uniformity'].mean():.3f}°C<br>
        💧 平均濕度: {dff['CH105(通道 105)'].mean():.1f}%RH
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Data Table (collapsible)
# ─────────────────────────────────────────────
with st.expander("📋 查看原始資料表"):
    display_cols = ['時間'] + [s['col_key'] for s in INSIDE_SENSORS.values()] + \
                  [s['col_key'] for s in OUTSIDE_SENSORS.values()]
    rename_map = {'時間': '時間'}
    rename_map.update({s['col_key']: f"{n} {s['label'].split(' ')[1]}"
                       for n, s in INSIDE_SENSORS.items()})
    rename_map.update({s['col_key']: s['label']
                       for s in OUTSIDE_SENSORS.values()})
    df_show = dff[display_cols].rename(columns=rename_map).tail(200)
    st.dataframe(df_show, hide_index=True, use_container_width=True, height=300)
    csv_bytes = dff[display_cols].to_csv(index=False).encode('utf-8-sig')
    st.download_button("⬇️ 下載篩選後資料 (CSV)", csv_bytes,
                       file_name=f"GM10_filtered_{time_range[0].strftime('%H%M')}_{time_range[1].strftime('%H%M')}.csv",
                       mime="text/csv")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#3a5a7a; font-size:0.78rem;'>
    ❄️ 商錄冷庫 GM10 數位雙生系統 ｜ ITRI 綠能所 智慧控制設備研究室 ｜ GB+44015-2026<br>
    技術支援: 熱流 + IoT + AI + Firmware 整合平台
</div>
""", unsafe_allow_html=True)
