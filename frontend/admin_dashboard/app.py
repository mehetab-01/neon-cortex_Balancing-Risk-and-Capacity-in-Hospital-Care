"""
VitalFlow AI - Admin Dashboard
Clean, Responsive Hospital Command Center
"""

import streamlit as st
import sys
import os
from datetime import datetime
import time

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Page config - only set if running standalone (not imported from main.py)
def _set_page_config():
    try:
        st.set_page_config(
            page_title="VitalFlow Command",
            page_icon="🏥",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        pass  # Already set by main.py

if __name__ == "__main__":
    _set_page_config()

# Import services
from shared.data_service import (
    get_hospital_data, get_network_hospitals, get_patients, get_beds,
    get_staff, get_ai_decisions, get_hospital_stats, get_floors,
    transfer_patient, swap_beds, admit_patient, discharge_patient,
    approve_decision, override_decision, refresh_mock_data, check_backend_health
)

# ============================================
# CUSTOM CSS - Warm Ochre/Cream Theme
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    :root {
        --cream: #faf8f5;
        --cream-dark: #f5f0e8;
        --cream-light: #fdfcfa;
        --ochre: #c4a35a;
        --ochre-light: #d4b96a;
        --ochre-dark: #a68b4b;
        --brown: #5c4a32;
        --brown-light: #7a6548;
        --text-dark: #2d2a26;
        --text-muted: #6b6560;
        --text-light: #9a948c;
        --border: #e8e2d9;
        --border-light: #f0ebe3;
        --success: #5a9a6e;
        --success-bg: #eef6f0;
        --warning: #c4893a;
        --warning-bg: #fef6eb;
        --error: #c45c5c;
        --error-bg: #fdf2f2;
        --info: #5a8ac4;
        --info-bg: #eff5fb;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-sm: 0 1px 3px rgba(92, 74, 50, 0.06);
        --shadow-md: 0 4px 12px rgba(92, 74, 50, 0.08);
    }
    
    * { font-family: 'DM Sans', -apple-system, sans-serif; }
    
    .stApp { background: var(--cream); }
    
    .main .block-container {
        padding: 1.5rem 2.5rem;
        max-width: 100%;
        background: var(--cream);
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Dashboard Card */
    .dash-card {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    /* Metric Card */
    .metric-card {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    
    .metric-card .label {
        color: var(--text-muted);
        font-size: 0.8125rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-dark);
        line-height: 1.1;
    }
    
    .metric-card .subtext {
        font-size: 0.8125rem;
        color: var(--text-light);
        margin-top: 0.5rem;
    }
    
    .metric-card .subtext.positive { color: var(--success); }
    .metric-card .subtext.negative { color: var(--error); }
    
    /* Status Chip */
    .status-chip {
        display: inline-block;
        padding: 0.375rem 0.875rem;
        border-radius: var(--radius-sm);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    
    .chip-critical { background: var(--error-bg); color: var(--error); }
    .chip-serious { background: var(--warning-bg); color: var(--warning); }
    .chip-stable { background: var(--success-bg); color: var(--success); }
    .chip-recovering { background: var(--info-bg); color: var(--info); }
    
    /* Stat Box */
    .stat-box {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        text-align: center;
    }
    
    .stat-box .number {
        font-size: 1.875rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .stat-box .label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.5rem;
    }
    
    /* Bed Grid */
    .bed-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
        gap: 10px;
        padding: 1.25rem;
        background: var(--cream-dark);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-light);
    }
    
    .bed-cell {
        aspect-ratio: 1;
        border-radius: var(--radius-sm);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 0.6875rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    
    .bed-cell:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .bed-critical { background: var(--error); color: white; }
    .bed-serious { background: var(--warning); color: white; }
    .bed-stable { background: var(--success); color: white; }
    .bed-recovering { background: var(--info); color: white; }
    .bed-empty { background: var(--cream-light); border: 2px dashed var(--border); color: var(--text-light); }
    
    /* Patient Card */
    .patient-card {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    .patient-card:hover { 
        border-color: var(--ochre); 
        box-shadow: var(--shadow-sm);
    }
    
    .patient-card .info .name {
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.25rem;
    }
    
    .patient-card .info .meta {
        font-size: 0.8125rem;
        color: var(--text-muted);
    }
    
    .patient-card .vitals {
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    
    .patient-card .vital {
        text-align: center;
    }
    
    .patient-card .vital .value {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-dark);
    }
    
    .patient-card .vital .unit {
        font-size: 0.6875rem;
        color: var(--text-light);
        font-weight: 500;
    }
    
    /* Decision Card */
    .decision-card {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-left: 4px solid;
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    
    .decision-card.critical { border-left-color: var(--error); }
    .decision-card.warning { border-left-color: var(--warning); }
    .decision-card.info { border-left-color: var(--info); }
    
    .decision-card .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .decision-card .header .action {
        font-weight: 600;
        color: var(--text-dark);
    }
    
    .decision-card .header .time {
        font-size: 0.75rem;
        color: var(--text-light);
    }
    
    .decision-card .reason {
        font-size: 0.875rem;
        color: var(--text-muted);
        line-height: 1.6;
    }
    
    /* Hospital Mini Card */
    .hospital-mini {
        background: var(--cream-light);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin-bottom: 0.625rem;
    }
    
    .hospital-mini .name {
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.25rem;
    }
    
    .hospital-mini .address {
        font-size: 0.75rem;
        color: var(--text-light);
        margin-bottom: 0.625rem;
    }
    
    .hospital-mini .stats {
        display: flex;
        gap: 1rem;
        font-size: 0.8125rem;
    }
    
    .hospital-mini .stats span { color: var(--text-muted); }
    .hospital-mini .stats strong { color: var(--text-dark); }
    
    /* Progress Bar */
    .progress-container { margin-bottom: 1rem; }
    
    .progress-container .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.375rem;
    }
    
    .progress-container .progress-label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-muted);
    }
    
    .progress-container .progress-value {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--text-dark);
    }
    
    .progress-bar {
        height: 6px;
        background: var(--cream-dark);
        border-radius: 3px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--cream-light);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .block-container { padding: 1.25rem; }
    
    /* Sidebar Header */
    .sidebar-header {
        text-align: center;
        padding: 1rem 0 1.25rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.25rem;
    }
    
    .sidebar-header h1 {
        color: var(--ochre);
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .sidebar-header p {
        color: var(--text-light);
        font-size: 0.8125rem;
        margin: 0.25rem 0 0;
    }
    
    /* Alert Box */
    .alert-box {
        background: var(--error-bg);
        border: 1px solid #f5d5d5;
        border-radius: var(--radius-md);
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .alert-box .count {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--error);
    }
    
    .alert-box .label {
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--error);
        letter-spacing: 0.05em;
    }
    
    /* Live Indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--success);
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        background: var(--success);
        border-radius: 50%;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--cream-dark);
        padding: 0.375rem;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: var(--radius-sm);
        color: var(--text-muted);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--ochre);
        color: white;
    }
    
    /* Primary Button - Ochre */
    .stButton > button[kind="primary"],
    .stButton > button:not([kind]) {
        background: var(--ochre) !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind]):hover {
        background: var(--ochre-dark) !important;
        transform: translateY(-1px);
    }
    
    /* Secondary Button - Outlined */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-dark) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--cream-dark) !important;
        border-color: var(--ochre) !important;
        color: var(--ochre) !important;
    }
    
    /* Patient & Decision Actions Container */
    .patient-actions, .decision-actions {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid var(--border);
    }
    
    /* Action Buttons */
    .action-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: var(--radius-sm);
        font-size: 0.8125rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
        border: none;
    }
    
    .btn-approve {
        background: var(--success-bg);
        color: var(--success);
        border: 1px solid #c5dcc9;
    }
    
    .btn-approve:hover {
        background: var(--success);
        color: white;
    }
    
    .btn-override {
        background: var(--warning-bg);
        color: var(--warning);
        border: 1px solid #f5dfc5;
    }
    
    .btn-override:hover {
        background: var(--warning);
        color: white;
    }
    
    .btn-transfer {
        background: var(--info-bg);
        color: var(--info);
        border: 1px solid #c5d5e5;
    }
    
    .btn-transfer:hover {
        background: var(--info);
        color: white;
    }
    
    .btn-danger {
        background: var(--error-bg);
        color: var(--error);
        border: 1px solid #f5d5d5;
    }
    
    .btn-danger:hover {
        background: var(--error);
        color: white;
    }
    
    /* Section Title */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 1rem;
        padding-bottom: 0.625rem;
        border-bottom: 2px solid var(--border);
    }
    
    /* Page Header */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .page-header h1 {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-dark);
        margin: 0;
    }
    
    .page-header .timestamp {
        font-size: 0.8125rem;
        color: var(--text-light);
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background: var(--cream-light) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-dark) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--ochre) !important;
        box-shadow: 0 0 0 2px rgba(196, 163, 90, 0.15) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--cream-light) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        color: var(--text-dark) !important;
    }

    .streamlit-expanderContent {
        background: var(--cream-light) !important;
        color: var(--text-dark) !important;
    }

    /* Force dark text on all Streamlit components */
    [data-testid="stMetricValue"] {
        color: #2d2a26 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #6b6560 !important;
    }

    [data-testid="stMetricDelta"] {
        color: inherit !important;
    }

    [data-testid="stExpander"] {
        background: var(--cream-light) !important;
    }

    [data-testid="stExpander"] p,
    [data-testid="stExpander"] span,
    [data-testid="stExpander"] div {
        color: #2d2a26 !important;
    }

    /* Fix radio button text */
    .stRadio label {
        color: #2d2a26 !important;
    }

    .stRadio span {
        color: #2d2a26 !important;
    }

    /* Fix selectbox text */
    .stSelectbox label,
    .stSelectbox span {
        color: #2d2a26 !important;
    }

    [data-testid="stSelectbox"] div {
        color: #2d2a26 !important;
    }

    /* Fix markdown text */
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown div,
    .stMarkdown strong {
        color: #2d2a26 !important;
    }

    /* Patient card specific - ensure visibility */
    .patient-card,
    .patient-card .info,
    .patient-card .info .name,
    .patient-card .info .meta,
    .patient-card .vitals,
    .patient-card .vital,
    .patient-card .vital .value,
    .patient-card .vital .unit {
        color: #2d2a26 !important;
    }

    .patient-card .info .meta {
        color: #6b6560 !important;
    }

    .patient-card .vital .unit {
        color: #9a948c !important;
    }

    /* Decision card specific */
    .decision-card,
    .decision-card .header,
    .decision-card .header .action,
    .decision-card .reason {
        color: #2d2a26 !important;
    }

    .decision-card .header .time {
        color: #9a948c !important;
    }

    .decision-card .reason {
        color: #6b6560 !important;
    }

    /* All text elements within main content */
    .main p, .main span, .main div, .main label, .main strong {
        color: #2d2a26;
    }

    /* Hospital mini card */
    .hospital-mini,
    .hospital-mini .name,
    .hospital-mini .stats span,
    .hospital-mini .stats strong {
        color: #2d2a26 !important;
    }

    .hospital-mini .address {
        color: #9a948c !important;
    }

    /* Stat box */
    .stat-box .number,
    .stat-box .label {
        color: #2d2a26 !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container { padding: 1rem; }
        .metric-card .value { font-size: 1.5rem; }
        .bed-grid { grid-template-columns: repeat(auto-fill, minmax(60px, 1fr)); }
    }

    /* Global text visibility override - ensures all text is dark */
    .stApp, .stApp * {
        --tw-text-opacity: 1;
    }

    /* Override any white text from dark themes */
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] div,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 {
        color: #2d2a26;
    }

    /* Keep specific colored elements with their colors */
    .chip-critical { color: var(--error) !important; }
    .chip-serious { color: var(--warning) !important; }
    .chip-stable { color: var(--success) !important; }
    .chip-recovering { color: var(--info) !important; }

    /* Preserve button text colors */
    .stButton button {
        color: white !important;
    }

    .stButton > button[kind="secondary"] {
        color: #2d2a26 !important;
    }

    /* Keep bed cell text white on colored backgrounds */
    .bed-cell.bed-critical,
    .bed-cell.bed-serious,
    .bed-cell.bed-stable,
    .bed-cell.bed-recovering {
        color: white !important;
    }

    /* Live indicator stays green */
    .live-indicator {
        color: #5a9a6e !important;
    }

    /* Alert box text stays red */
    .alert-box .count,
    .alert-box .label {
        color: var(--error) !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================
def init_state():
    if 'hospital_id' not in st.session_state:
        st.session_state.hospital_id = "H001"
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()


def load_data():
    """Load all data from endpoints"""
    hid = st.session_state.hospital_id
    return {
        'hospital': get_hospital_data(hid),
        'stats': get_hospital_stats(hid),
        'patients': get_patients(hid),
        'floors': get_floors(hid),
        'decisions': get_ai_decisions(hid),
        'network': get_network_hospitals(),
        'staff': get_staff(hid)
    }


init_state()


# ============================================
# COMPONENTS
# ============================================

def render_metric_card(title: str, value: str, subtext: str = None, positive: bool = True):
    subtext_html = ""
    if subtext:
        cls = "positive" if positive else "negative"
        subtext_html = f'<div class="subtext {cls}">{subtext}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{title}</div>
        <div class="value">{value}</div>
        {subtext_html}
    </div>
    """, unsafe_allow_html=True)


def render_capacity_bar(label: str, used: int, total: int, color: str = "#0ea5e9"):
    pct = (used / total * 100) if total > 0 else 0
    bar_color = "#ef4444" if pct > 90 else "#f59e0b" if pct > 75 else color
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-header">
            <span class="progress-label">{label}</span>
            <span class="progress-value">{used}/{total}</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pct}%; background: {bar_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_chip(status: str):
    status_lower = status.lower()
    return f'<span class="status-chip chip-{status_lower}">{status}</span>'


def get_bed_class(patient):
    if not patient:
        return "bed-empty"
    status = patient.get('status', 'Stable').lower()
    return f"bed-{status}"


def render_bed_grid(beds: list, patients: list):
    patient_map = {p['id']: p for p in patients}
    
    html = '<div class="bed-grid">'
    for bed in beds:
        patient = patient_map.get(bed.get('patient_id'))
        bed_class = get_bed_class(patient)
        
        if patient:
            name = patient['name'].split()[0][:5]
            spo2 = patient.get('spo2', 0)
            label = f"{name}<br>{spo2}%"
        else:
            label = f"{bed['id'][-3:]}<br>—"
        
        html += f'<div class="bed-cell {bed_class}">{label}</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_patient_card(patient: dict):
    status = patient.get('status', 'Stable')
    chip = render_status_chip(status)
    
    spo2 = patient.get('spo2', 0)
    spo2_color = "#ef4444" if spo2 < 90 else "#f59e0b" if spo2 < 95 else "#10b981"
    hr = patient.get('heart_rate', 0)
    
    st.markdown(f"""
    <div class="patient-card">
        <div class="info">
            <div class="name">{patient['name']}</div>
            <div class="meta">{patient['id']} · Bed {patient.get('bed_id', '—')} · {patient['diagnosis'][:30]}</div>
        </div>
        <div class="vitals">
            <div class="vital">
                <div class="value" style="color: {spo2_color}">{spo2}%</div>
                <div class="unit">SpO2</div>
            </div>
            <div class="vital">
                <div class="value">{hr}</div>
                <div class="unit">BPM</div>
            </div>
            {chip}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_decision_card(decision: dict):
    severity = decision.get('severity', 'INFO').lower()
    timestamp = decision.get('timestamp', '')
    if isinstance(timestamp, str) and timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")
        except:
            time_str = timestamp[:5]
    else:
        time_str = "—"
    
    action = decision.get('action', 'Action').replace('_', ' ').title()
    
    st.markdown(f"""
    <div class="decision-card {severity}">
        <div class="header">
            <span class="action">{action}</span>
            <span class="time">{time_str}</span>
        </div>
        <div class="reason">{decision.get('reason', 'No details available')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_hospital_mini(hospital: dict):
    icu_pct = hospital.get('icu_percentage', 50)
    
    st.markdown(f"""
    <div class="hospital-mini">
        <div class="name">{hospital['name']}</div>
        <div class="address">{hospital.get('address', '')[:40]}</div>
        <div class="stats">
            <span>Beds: <strong>{hospital.get('available_beds', 0)}/{hospital.get('total_beds', 0)}</strong></span>
            <span>ICU: <strong>{hospital.get('icu_available', 0)}</strong></span>
            <span>Load: <strong>{hospital.get('occupancy_rate', 0):.0f}%</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN LAYOUT
# ============================================

# Initialize state
init_state()

# Load data
data = load_data()
stats = data['stats']
patients = data['patients']
floors = data['floors']
decisions = data['decisions']
network = data['network']

# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h1>VitalFlow</h1>
        <p>Hospital Command Center</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hospital selector
    hospitals = {h['id']: h['name'] for h in network}
    selected = st.selectbox("Select Hospital", list(hospitals.keys()), format_func=lambda x: hospitals[x], label_visibility="collapsed")
    if selected != st.session_state.hospital_id:
        st.session_state.hospital_id = selected
        st.rerun()
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    # Critical alert
    critical = stats.get('critical_patients', 0)
    if critical > 0:
        st.markdown(f"""
        <div class="alert-box">
            <div class="count">{critical}</div>
            <div class="label">CRITICAL PATIENTS</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Capacity bars
    st.markdown('<div class="section-title">Capacity</div>', unsafe_allow_html=True)
    render_capacity_bar("ICU Beds", stats.get('icu_total', 0) - stats.get('icu_available', 0), stats.get('icu_total', 1), "#ef4444")
    render_capacity_bar("Emergency", stats.get('emergency_total', 0) - stats.get('emergency_available', 0), stats.get('emergency_total', 1), "#f59e0b")
    render_capacity_bar("General", stats.get('general_total', 0) - stats.get('general_available', 0), stats.get('general_total', 1), "#10b981")
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.auto_refresh = st.toggle("Auto Refresh", st.session_state.auto_refresh)
    with col2:
        if st.button("↻ Refresh", use_container_width=True):
            refresh_mock_data(st.session_state.hospital_id)
            st.rerun()
    
    backend = check_backend_health()
    mode = "Live API" if backend.get('api_available') else "Mock Data"
    st.markdown(f"""
    <div style="text-align: center; margin-top: 1rem;">
        <span class="live-indicator"><span class="live-dot"></span>{mode}</span>
    </div>
    """, unsafe_allow_html=True)


# Main content
hospital_name = data['hospital'].get('hospital', {}).get('name', 'VitalFlow Hospital')
st.markdown(f"""
<div class="page-header">
    <h1>{hospital_name}</h1>
    <div class="timestamp">
        <span class="live-indicator"><span class="live-dot"></span>Live</span>
        &nbsp;·&nbsp; {datetime.now().strftime('%H:%M:%S')}
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("Total Beds", str(stats.get('total_beds', 0)))
with col2:
    render_metric_card("Occupied", str(stats.get('occupied_beds', 0)), f"+{stats.get('admissions_last_hour', 0)} this hour", True)
with col3:
    render_metric_card("Available", str(stats.get('available_beds', 0)), f"{stats.get('discharges_last_hour', 0)} discharged", False)
with col4:
    staff_on = stats.get('staff_on_duty', 0)
    staff_total = stats.get('total_staff', 1)
    render_metric_card("Staff Active", f"{staff_on}/{staff_total}")

st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Floor Map", "Patients", "AI Decisions"])

# TAB 1: Overview
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-title">Patient Status Distribution</div>', unsafe_allow_html=True)
        
        status_counts = {
            'Critical': stats.get('critical_patients', 0),
            'Serious': stats.get('serious_patients', 0),
            'Stable': stats.get('stable_patients', 0),
            'Recovering': stats.get('recovering_patients', 0)
        }
        
        colors = {'Critical': '#ef4444', 'Serious': '#f59e0b', 'Stable': '#10b981', 'Recovering': '#3b82f6'}
        
        cols = st.columns(4)
        for i, (status, count) in enumerate(status_counts.items()):
            with cols[i]:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="number" style="color: {colors[status]}">{count}</div>
                    <div class="label" style="color: {colors[status]}">{status}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Critical Patients</div>', unsafe_allow_html=True)
        
        critical_patients = [p for p in patients if p.get('status') == 'Critical']
        if critical_patients:
            for p in critical_patients[:5]:
                render_patient_card(p)
        else:
            st.markdown("""
            <div class="dash-card" style="text-align: center; padding: 2rem; color: #10b981;">
                ✓ No critical patients at this time
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-title">Network Hospitals</div>', unsafe_allow_html=True)
        for h in network[:4]:
            render_hospital_mini(h)
        
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Recent AI Decisions</div>', unsafe_allow_html=True)
        for d in decisions[:3]:
            render_decision_card(d)


# TAB 2: Floor Map
with tab2:
    st.markdown('<div class="section-title">Hospital Floor Map</div>', unsafe_allow_html=True)
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
        <span style="display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: #64748b;">
            <span style="width: 12px; height: 12px; background: #ef4444; border-radius: 3px;"></span> Critical
        </span>
        <span style="display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: #64748b;">
            <span style="width: 12px; height: 12px; background: #f59e0b; border-radius: 3px;"></span> Serious
        </span>
        <span style="display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: #64748b;">
            <span style="width: 12px; height: 12px; background: #10b981; border-radius: 3px;"></span> Stable
        </span>
        <span style="display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: #64748b;">
            <span style="width: 12px; height: 12px; background: #3b82f6; border-radius: 3px;"></span> Recovering
        </span>
        <span style="display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; color: #64748b;">
            <span style="width: 12px; height: 12px; background: #fff; border: 1px dashed #cbd5e1; border-radius: 3px;"></span> Empty
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    floor_tabs = st.tabs([f"Floor {f['floor_number']}: {f['name']}" for f in floors])
    
    for i, tab in enumerate(floor_tabs):
        with tab:
            floor = floors[i]
            beds = floor.get('beds', [])
            
            occupied = sum(1 for b in beds if b.get('is_occupied'))
            total = len(beds)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Beds", total)
            with col2:
                st.metric("Occupied", occupied)
            with col3:
                st.metric("Available", total - occupied)
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            render_bed_grid(beds, patients)


# TAB 3: Patients
with tab3:
    st.markdown('<div class="section-title">Patient Management</div>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("Search", placeholder="Search by name or ID...", label_visibility="collapsed")
    with col2:
        status_filter = st.selectbox("Status", ["All", "Critical", "Serious", "Stable", "Recovering"], label_visibility="collapsed")
    with col3:
        sort_by = st.selectbox("Sort by", ["Priority", "Name", "SpO2"], label_visibility="collapsed")
    
    # Filter patients
    filtered = patients
    if search:
        search_lower = search.lower()
        filtered = [p for p in filtered if search_lower in p.get('name', '').lower() or search_lower in p.get('id', '').lower()]
    if status_filter != "All":
        filtered = [p for p in filtered if p.get('status') == status_filter]
    
    # Sort
    priority_order = {'Critical': 0, 'Serious': 1, 'Stable': 2, 'Recovering': 3}
    if sort_by == "Priority":
        filtered.sort(key=lambda x: priority_order.get(x.get('status', 'Stable'), 99))
    elif sort_by == "Name":
        filtered.sort(key=lambda x: x.get('name', ''))
    elif sort_by == "SpO2":
        filtered.sort(key=lambda x: x.get('spo2', 100))
    
    st.markdown(f"""
    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 1rem;">
        Showing <strong style="color: #1e293b">{len(filtered)}</strong> patients
    </div>
    """, unsafe_allow_html=True)
    
    # Display patients
    for p in filtered[:20]:
        with st.expander(f"{p['name']} · {p.get('bed_id', '—')} · {p.get('status', 'Unknown')}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"""
                <div style="font-size: 0.875rem; color: #64748b; line-height: 1.8;">
                    <strong>ID:</strong> {p['id']}<br>
                    <strong>Age:</strong> {p.get('age', 'N/A')}<br>
                    <strong>Diagnosis:</strong> {p.get('diagnosis', 'N/A')}<br>
                    <strong>Doctor:</strong> {p.get('assigned_doctor', 'Unassigned')}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.metric("SpO2", f"{p.get('spo2', 'N/A')}%")
                st.metric("Heart Rate", f"{p.get('heart_rate', 'N/A')} bpm")
            
            # Actions - Clean buttons with icons
            st.markdown('<div class="patient-actions">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Transfer", key=f"transfer_{p['id']}", use_container_width=True, type="secondary"):
                    st.info("Transfer endpoint ready")
            with col2:
                if st.button("📋 Details", key=f"details_{p['id']}", use_container_width=True, type="secondary"):
                    st.info("Details endpoint ready")
            with col3:
                if st.button("✓ Discharge", key=f"discharge_{p['id']}", use_container_width=True, type="primary"):
                    result = discharge_patient(st.session_state.hospital_id, p['id'])
                    st.success(f"Discharged: {result.get('message', 'Success')}")
            st.markdown('</div>', unsafe_allow_html=True)


# TAB 4: AI Decisions
with tab4:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-title">AI Decision Log</div>', unsafe_allow_html=True)
        
        # Filter
        severity_filter = st.radio("Filter by severity", ["All", "Critical", "Warning", "Info"], horizontal=True, label_visibility="collapsed")
        
        filtered_decisions = decisions
        if severity_filter != "All":
            filtered_decisions = [d for d in decisions if d.get('severity', '').upper() == severity_filter.upper()]
        
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        
        for d in filtered_decisions[:15]:
            render_decision_card(d)
            
            st.markdown('<div class="decision-actions">', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✓ Approve", key=f"approve_{d['id']}", use_container_width=True, type="primary"):
                    result = approve_decision(d['id'])
                    st.success("Approved" if result.get('success') else "Failed")
            with col_b:
                if st.button("⟳ Override", key=f"override_{d['id']}", use_container_width=True, type="secondary"):
                    result = override_decision(d['id'], "Manual override by admin")
                    st.warning("Overridden" if result.get('success') else "Failed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-title">Statistics</div>', unsafe_allow_html=True)
        
        total = len(decisions)
        critical_count = sum(1 for d in decisions if d.get('severity') == 'CRITICAL')
        warning_count = sum(1 for d in decisions if d.get('severity') == 'WARNING')
        
        st.markdown(f"""
        <div class="stat-box" style="margin-bottom: 0.75rem;">
            <div class="number" style="color: #1e293b">{total}</div>
            <div class="label" style="color: #64748b">Total Decisions</div>
        </div>
        <div class="stat-box" style="margin-bottom: 0.75rem;">
            <div class="number" style="color: #ef4444">{critical_count}</div>
            <div class="label" style="color: #ef4444">Critical</div>
        </div>
        <div class="stat-box" style="margin-bottom: 0.75rem;">
            <div class="number" style="color: #f59e0b">{warning_count}</div>
            <div class="label" style="color: #f59e0b">Warnings</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Action Types</div>', unsafe_allow_html=True)
        
        action_counts = {}
        for d in decisions:
            action = d.get('action', 'OTHER').replace('_', ' ').title()
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">
                <span style="color: #64748b; font-size: 0.875rem;">{action}</span>
                <span style="color: #1e293b; font-weight: 600; font-size: 0.875rem;">{count}</span>
            </div>
            """, unsafe_allow_html=True)


# Auto-refresh
if st.session_state.auto_refresh:
    time.sleep(5)
    refresh_mock_data(st.session_state.hospital_id)
    st.rerun()
