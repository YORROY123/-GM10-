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
    /* Dark theme base */
    .stApp { background-color: #0a0e1a; color: #e0e8f0; }
    .main .block-container { padding: 1rem 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #0d1b2e 0%, #1a2a45 100%);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,100,200,0.15);
    }
    .kpi-label { font-size: 0.75rem; color: #7ab3d4; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
    .kpi-value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .kpi-unit  { font-size: 0.85rem; color: #7ab3d4; }
    .kpi-delta { font-size: 0.78rem; margin-top: 4px; }

    /* Section headers */
    .section-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #4fc3f7;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 12px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 1px solid #1e3a5f;
    }

    /* Status badge */
    .badge-ok   { background:#0d3d2a; color:#4caf50; border:1px solid #4caf50; border-radius:6px; padding:2px 10px; font-size:0.78rem; }
    .badge-warn { background:#3d2d00; color:#ffb300; border:1px solid #ffb300; border-radius:6px; padding:2px 10px; font-size:0.78rem; }
    .badge-err  { background:#3d0d0d; color:#f44336; border:1px solid #f44336; border-radius:6px; padding:2px 10px; font-size:0.78rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #060c18; border-right: 1px solid #1e3a5f; }
    section[data-testid="stSidebar"] .stMarkdown h2 { color: #4fc3f7; }

    /* Plotly chart backgrounds */
    .js-plotly-plot { border-radius: 10px; }

    /* Alert box */
    .alert-box {
        background: #1a0a0a;
        border-left: 4px solid #f44336;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #ff7961;
    }
    .warn-box {
        background: #1a1200;
        border-left: 4px solid #ffb300;
        border-radius: 4px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #ffe082;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sensor Layout Definition
# ─────────────────────────────────────────────
# Inside sensors grid (viewed from top, front=top)
INSIDE_SENSORS = {
    'CH2': {'label': 'CH2\n前-左', 'col_key': 'CH2(測試通道_02)', 'x': 0.25, 'y': 0.85},
    'CH1': {'label': 'CH1\n前-右', 'col_key': 'CH1(測試通道_01)', 'x': 0.75, 'y': 0.85},
    'CH4': {'label': 'CH4\n中前-左', 'col_key': 'CH4(通道 4)', 'x': 0.25, 'y': 0.60},
    'CH3': {'label': 'CH3\n中前-右', 'col_key': 'CH3(通道 3)', 'x': 0.75, 'y': 0.60},
    'CH6': {'label': 'CH6\n中後-左', 'col_key': 'CH6(通道 6)', 'x': 0.25, 'y': 0.38},
    'CH5': {'label': 'CH5\n中後-右', 'col_key': 'CH5(通道 5)', 'x': 0.75, 'y': 0.38},
    'CH8': {'label': 'CH8\n後-左',  'col_key': 'CH8(通道 8)', 'x': 0.25, 'y': 0.15},
    'CH7': {'label': 'CH7\n後-右',  'col_key': 'CH7(通道 7)', 'x': 0.75, 'y': 0.15},
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

# ── LEFT: Cold Storage Floor Plan ──
with col_left:
    st.markdown("<div class='section-title'>🗺️ 冷庫平面圖（庫內溫度分布）</div>", unsafe_allow_html=True)

    # Build heatmap-style scatter on a floor plan
    fig_floor = go.Figure()

    # Draw floor boundary
    fig_floor.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
                        fillcolor="#0d1b2e", line=dict(color="#1e5f9f", width=3))
    # Door indicator (front)
    fig_floor.add_shape(type="rect", x0=0.35, y0=0.96, x1=0.65, y1=1.04,
                        fillcolor="#c8902a", line=dict(color="#f0b030", width=2))
    fig_floor.add_annotation(x=0.5, y=1.06, text="門(正面)", showarrow=False,
                             font=dict(size=10, color="#f0b030"), xref="x", yref="y")

    # Grid lines (shelves)
    for y in [0.73, 0.49, 0.27]:
        fig_floor.add_shape(type="line", x0=0.05, y0=y, x1=0.95, y1=y,
                            line=dict(color="#1e3a5f", width=1, dash="dot"))

    # Sensor bubbles
    for name, s in INSIDE_SENSORS.items():
        val = latest[s['col_key']]
        color = temp_color(val)
        # Size by relative warmth
        sz = 50 + 30 * ((val - (-25)) / 15)
        fig_floor.add_trace(go.Scatter(
            x=[s['x']], y=[s['y']],
            mode='markers+text',
            marker=dict(size=sz, color=color, opacity=0.9,
                        line=dict(color='white', width=1.5)),
            text=[f"{val:.1f}°C"],
            textposition="middle center",
            textfont=dict(size=9, color='white', family='Arial Black'),
            name=name,
            hovertemplate=f"<b>{name}</b><br>{s['label'].replace(chr(10),' ')}<br>溫度: {val:.2f}°C<extra></extra>",
            showlegend=False
        ))
        # Label below
        fig_floor.add_annotation(
            x=s['x'], y=s['y'] - 0.09,
            text=name, showarrow=False,
            font=dict(size=8, color="#7ab3d4"), xref="x", yref="y"
        )

    # Colorbar legend (manual gradient bar)
    fig_floor.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(
            colorscale=[[0,'rgb(30,80,200)'], [0.5,'rgb(80,180,220)'], [1,'rgb(200,220,255)']],
            cmin=-25, cmax=-10,
            colorbar=dict(
                title=dict(text="°C", font=dict(color="#7ab3d4")),
                tickfont=dict(color="#7ab3d4"),
                len=0.6, thickness=12,
                x=1.02,
                tickvals=[-25,-20,-15,-10],
            ),
            showscale=True,
            color=[avg_T],
            size=0.1
        ),
        showlegend=False
    ))

    fig_floor.update_layout(
        plot_bgcolor='#060c18',
        paper_bgcolor='#060c18',
        height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(range=[-0.05, 1.05], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True),
        yaxis=dict(range=[-0.05, 1.15], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True,
                   scaleanchor="x"),
        annotations=[
            dict(x=0.5, y=-0.02, xref="x", yref="y",
                 text="← 後面", showarrow=False, font=dict(size=9, color="#5a7a9f")),
        ]
    )

    # Alarm thresholds annotation
    if avg_T > alarm_high:
        fig_floor.add_annotation(
            x=0.5, y=0.5, text=f"⚠️ 溫度超限！{avg_T:.1f}°C > {alarm_high}°C",
            showarrow=False, font=dict(size=13, color="#f44336"),
            bgcolor="rgba(50,0,0,0.7)", bordercolor="#f44336", borderwidth=1,
            xref="x", yref="y"
        )

    st.plotly_chart(fig_floor, use_container_width=True)

    # Outside sensors compact table
    st.markdown("<div class='section-title'>🌡️ 庫外感測器</div>", unsafe_allow_html=True)
    outside_data = []
    for name, s in OUTSIDE_SENSORS.items():
        val = latest[s['col_key']]
        outside_data.append({"感測器": s['label'].replace('\n', ' '), "數值": f"{val:.2f} {s['unit']}"})
    df_out = pd.DataFrame(outside_data)
    st.dataframe(df_out, hide_index=True, use_container_width=True,
                 column_config={"感測器": st.column_config.TextColumn(width="medium"),
                                "數值": st.column_config.TextColumn(width="small")})

# ── RIGHT: Time Series Chart ──
with col_right:
    st.markdown("<div class='section-title'>📈 時間序列曲線</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔵 庫內溫度 (CH1-CH8)", "🟠 庫外環境", "📊 統計趨勢"])

    # ── Tab 1: Inside temperatures ──
    with tab1:
        fig_inside = go.Figure()
        colors_inside = px.colors.qualitative.Set2
        if show_raw:
            for i, (name, s) in enumerate(INSIDE_SENSORS.items()):
                fig_inside.add_trace(go.Scatter(
                    x=dff['時間'], y=dff[s['col_key']],
                    name=f"{name}({s['label'].split(chr(10))[1]})",
                    line=dict(width=1.5, color=colors_inside[i % len(colors_inside)]),
                    opacity=0.85,
                    hovertemplate=f"{name}: %{{y:.2f}}°C<extra></extra>"
                ))
        # Average line
        fig_inside.add_trace(go.Scatter(
            x=dff['時間'], y=dff['avg_inside_T'],
            name='平均溫度', line=dict(width=3, color='white', dash='dash'),
            hovertemplate="平均: %{y:.2f}°C<extra></extra>"
        ))
        # Alarm bands
        fig_inside.add_hrect(y0=alarm_high, y1=alarm_high+5,
                             fillcolor="rgba(244,67,54,0.1)", line_width=0)
        fig_inside.add_hline(y=alarm_high, line=dict(color="#f44336", dash="dot", width=1.5),
                             annotation_text=f"上限 {alarm_high}°C", annotation_font_color="#f44336")
        fig_inside.add_hline(y=alarm_low, line=dict(color="#ff9800", dash="dot", width=1.5),
                             annotation_text=f"下限 {alarm_low}°C", annotation_font_color="#ff9800")
        fig_inside.update_layout(
            plot_bgcolor='#060c18', paper_bgcolor='#060c18',
            height=380, margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", y=-0.15, font=dict(size=10, color="#7ab3d4"),
                        bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor='#1e3a5f', tickfont=dict(color="#7ab3d4")),
            yaxis=dict(gridcolor='#1e3a5f', tickfont=dict(color="#7ab3d4"),
                       title=dict(text="溫度 (°C)", font=dict(color="#7ab3d4"))),
            hovermode='x unified',
        )
        st.plotly_chart(fig_inside, use_container_width=True)

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
            plot_bgcolor='#060c18', paper_bgcolor='#060c18',
            height=400, margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.12, font=dict(size=10, color="#7ab3d4"),
                        bgcolor="rgba(0,0,0,0)"),
            hovermode='x unified',
        )
        for axis in ['xaxis', 'xaxis2', 'yaxis', 'yaxis2']:
            fig_out.update_layout(**{axis: dict(gridcolor='#1e3a5f',
                                                tickfont=dict(color="#7ab3d4"))})
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
            plot_bgcolor='#060c18', paper_bgcolor='#060c18',
            height=420, margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        for axis in ['xaxis', 'xaxis2', 'xaxis3', 'xaxis4',
                     'yaxis', 'yaxis2', 'yaxis3', 'yaxis4']:
            fig_stat.update_layout(**{axis: dict(gridcolor='#1e3a5f',
                                                  tickfont=dict(color="#7ab3d4"))})
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
    ch_labels = [f"{n}({s['label'].split(chr(10))[1]})" for n, s in INSIDE_SENSORS.items()]
    fig_hm = go.Figure(go.Heatmap(
        z=z_data,
        x=df_hm['時間'].dt.strftime('%H:%M'),
        y=ch_labels,
        colorscale=[[0,'#0a2463'],[0.4,'#1e5f9f'],[0.7,'#42a5f5'],[1,'#e3f2fd']],
        hoverongaps=False,
        colorbar=dict(title=dict(text="°C", font=dict(color="#7ab3d4")),
                      tickfont=dict(color="#7ab3d4"), thickness=12),
        hovertemplate="%{y}<br>時間: %{x}<br>溫度: %{z:.2f}°C<extra></extra>"
    ))
    fig_hm.update_layout(
        plot_bgcolor='#060c18', paper_bgcolor='#060c18',
        height=260, margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(tickfont=dict(size=9, color="#7ab3d4"), nticks=12),
        yaxis=dict(tickfont=dict(size=9, color="#7ab3d4")),
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
    rename_map.update({s['col_key']: f"{n}({s['label'].split(chr(10))[1]})"
                       for n, s in INSIDE_SENSORS.items()})
    rename_map.update({s['col_key']: s['label'].replace('\n', ' ')
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
