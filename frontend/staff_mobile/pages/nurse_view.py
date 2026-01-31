"""
VitalFlow AI - Nurse View
Mobile interface for nurses with task checklists, 
voice alerts, and bed assignments
"""
import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# UI STYLE ONLY - VitalFlow Healthcare Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* UI STYLE ONLY - Healthcare background */
    .stApp {max-width: 480px; margin: 0 auto; background: #F4F7FA !important;}
    
    /* UI STYLE ONLY - Nurse header with primary blue */
    .nurse-header {
        background: #2F80ED;
        color: white;
        padding: 20px 18px;
        border-radius: 14px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.25);
    }
    
    /* UI STYLE ONLY - Task card */
    .task-card {
        background: #E9EEF3;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 10px 0;
        border-left: 4px solid #2F80ED;
        border: 1px solid #CBD5E1;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }
    
    .task-card:hover {
        transform: translateX(2px);
        border-color: #2F80ED;
    }
    
    .task-urgent {
        border-left-color: #EB5757 !important;
        background: #E9EEF3 !important;
    }
    
    .task-completed {
        border-left-color: #27AE60 !important;
        opacity: 0.7;
    }
    
    /* UI STYLE ONLY - Progress bar */
    .progress-container {
        background: #CBD5E1;
        border-radius: 8px;
        padding: 3px;
        margin: 12px 0;
    }
    
    .progress-fill {
        background: #27AE60;
        height: 10px;
        border-radius: 6px;
        transition: width 0.4s ease;
    }
    
    /* UI STYLE ONLY - Voice alert */
    .voice-alert {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-left: 4px solid #2F80ED;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 14px 0;
        display: flex;
        align-items: center;
        gap: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .voice-alert:hover {
        background: #FFFFFF;
        border-color: #2F80ED;
    }
    
    /* UI STYLE ONLY - Code blue banner */
    .code-blue-banner {
        background: #EB5757;
        color: white;
        padding: 20px;
        border-radius: 14px;
        text-align: center;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(235, 87, 87, 0.3);
    }
    
    /* UI STYLE ONLY - Bed card */
    .bed-card {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 12px 14px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    
    .bed-card:hover {
        border-color: #2F80ED;
        background: #FFFFFF;
    }
    
    /* UI STYLE ONLY - Status badges */
    .status-badge {
        padding: 4px 10px;
        border-radius: 14px;
        font-size: 11px;
        font-weight: 600;
    }
    
    .badge-urgent {
        background: rgba(235, 87, 87, 0.15);
        color: #EB5757;
    }
    
    .badge-normal {
        background: rgba(39, 174, 96, 0.15);
        color: #27AE60;
    }
    
    /* UI STYLE ONLY - Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 20px 0 14px 0;
    }
    
    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #1F2937;
    }
    
    .badge-count {
        background: #2F80ED;
        color: white;
        padding: 3px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
    }
    
    /* UI STYLE ONLY - Task type icons */
    .task-type {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.2px;
    }
    
    .type-medicine {
        background: rgba(242, 153, 74, 0.15);
        color: #F2994A;
    }
    
    .type-vitals {
        background: rgba(47, 128, 237, 0.15);
        color: #2F80ED;
    }
    
    .type-checkup {
        background: rgba(39, 174, 96, 0.15);
        color: #27AE60;
    }
</style>
""", unsafe_allow_html=True)


def init_nurse_state():
    """Initialize nurse-specific session state"""
    if 'nurse_tasks' not in st.session_state:
        st.session_state.nurse_tasks = generate_mock_tasks()
    if 'nurse_alerts' not in st.session_state:
        st.session_state.nurse_alerts = generate_mock_alerts()
    if 'nurse_beds' not in st.session_state:
        st.session_state.nurse_beds = generate_mock_beds()
    if 'code_blue_active' not in st.session_state:
        st.session_state.code_blue_active = False


def generate_mock_tasks():
    """Generate mock AI-generated task checklist"""
    tasks = [
        {
            "id": "T001",
            "description": "Administer Epinephrine to Bed 4",
            "patient_name": "Raj Kumar",
            "bed_id": "Bed 4",
            "scheduled_time": (datetime.now() + timedelta(minutes=10)).strftime("%I:%M %p"),
            "is_urgent": True,
            "is_completed": False,
            "task_type": "MEDICINE"
        },
        {
            "id": "T002",
            "description": "Check vitals for Sunita Devi",
            "patient_name": "Sunita Devi",
            "bed_id": "Bed 7",
            "scheduled_time": (datetime.now() + timedelta(minutes=20)).strftime("%I:%M %p"),
            "is_urgent": False,
            "is_completed": False,
            "task_type": "VITALS"
        },
        {
            "id": "T003",
            "description": "Insulin injection for Amit Patel",
            "patient_name": "Amit Patel",
            "bed_id": "Bed 2",
            "scheduled_time": (datetime.now() + timedelta(minutes=30)).strftime("%I:%M %p"),
            "is_urgent": False,
            "is_completed": True,
            "task_type": "MEDICINE"
        },
        {
            "id": "T004",
            "description": "Change IV drip for Vikram Singh",
            "patient_name": "Vikram Singh",
            "bed_id": "ICU-3",
            "scheduled_time": (datetime.now() + timedelta(minutes=45)).strftime("%I:%M %p"),
            "is_urgent": True,
            "is_completed": False,
            "task_type": "MEDICINE"
        },
        {
            "id": "T005",
            "description": "Post-op wound dressing - Meena Kumari",
            "patient_name": "Meena Kumari",
            "bed_id": "Bed 12",
            "scheduled_time": (datetime.now() + timedelta(minutes=60)).strftime("%I:%M %p"),
            "is_urgent": False,
            "is_completed": True,
            "task_type": "CHECKUP"
        },
        {
            "id": "T006",
            "description": "Blood pressure monitoring - Room 5",
            "patient_name": "Deepak Sharma",
            "bed_id": "Bed 5",
            "scheduled_time": (datetime.now() + timedelta(minutes=75)).strftime("%I:%M %p"),
            "is_urgent": False,
            "is_completed": False,
            "task_type": "VITALS"
        },
        {
            "id": "T007",
            "description": "Administer pain medication to Bed 9",
            "patient_name": "Kavita Joshi",
            "bed_id": "Bed 9",
            "scheduled_time": (datetime.now() + timedelta(minutes=90)).strftime("%I:%M %p"),
            "is_urgent": False,
            "is_completed": False,
            "task_type": "MEDICINE"
        }
    ]
    return tasks


def generate_mock_alerts():
    """Generate mock voice alerts"""
    return [
        {
            "id": "VA001",
            "message": "Patient in Bed 4 requires immediate attention - SpO2 dropping",
            "is_voice": True,
            "priority": "Critical",
            "timestamp": datetime.now() - timedelta(minutes=2)
        },
        {
            "id": "VA002", 
            "message": "Medication reminder: Insulin for Bed 2 in 15 minutes",
            "is_voice": True,
            "priority": "Medium",
            "timestamp": datetime.now() - timedelta(minutes=10)
        }
    ]


def generate_mock_beds():
    """Generate mock bed assignment overview"""
    return [
        {"bed_id": "Bed 2", "patient": "Amit Patel", "condition": "Stable", "status": "occupied"},
        {"bed_id": "Bed 4", "patient": "Raj Kumar", "condition": "Critical", "status": "critical"},
        {"bed_id": "Bed 5", "patient": "Deepak Sharma", "condition": "Stable", "status": "occupied"},
        {"bed_id": "Bed 7", "patient": "Sunita Devi", "condition": "Recovering", "status": "occupied"},
        {"bed_id": "Bed 9", "patient": "Kavita Joshi", "condition": "Post-Op", "status": "monitoring"},
        {"bed_id": "Bed 12", "patient": "Meena Kumari", "condition": "Stable", "status": "occupied"},
        {"bed_id": "ICU-3", "patient": "Vikram Singh", "condition": "Critical", "status": "critical"},
    ]


def render_header():
    """Render nurse dashboard header"""
    completed = len([t for t in st.session_state.nurse_tasks if t["is_completed"]])
    total = len(st.session_state.nurse_tasks)
    
    st.markdown(f"""
    <div class="nurse-header">
        <div style="font-size: 13px; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase;">👩‍⚕️ Nurse Dashboard</div>
        <div style="font-size: 28px; font-weight: 800; margin: 12px 0; letter-spacing: -0.5px;">
            {st.session_state.staff_name}
        </div>
        <div style="font-size: 12px; opacity: 0.8;">ID: {st.session_state.staff_id} • {completed}/{total} tasks done</div>
    </div>
    """, unsafe_allow_html=True)


def render_code_blue_banner():
    """Render Code Blue emergency banner if active"""
    # For demo, randomly show code blue
    if st.session_state.code_blue_active:
        st.markdown("""
        <div class="code-blue-banner">
            <div style="font-size: 36px;">🚨</div>
            <div style="font-size: 26px; font-weight: 800; letter-spacing: 2px;">CODE BLUE</div>
            <div style="font-size: 15px; font-weight: 500; margin-top: 8px;">Cardiac arrest - ICU Bed 3</div>
            <div style="font-size: 12px; margin-top: 8px; opacity: 0.9;">All available staff respond immediately</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ Acknowledge Code Blue", key="ack_code_blue", use_container_width=True):
            st.session_state.code_blue_active = False
            st.rerun()


def render_voice_alerts():
    """Render voice alert notifications"""
    if not st.session_state.nurse_alerts:
        return
    
    alert_count = len(st.session_state.nurse_alerts)
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">🔊</span>
        <span class="section-title">Voice Alerts</span>
        <span class="badge-count">{alert_count}</span>
    </div>
    """, unsafe_allow_html=True)
    
    for alert in st.session_state.nurse_alerts:
        priority_color = "#FF4444" if alert["priority"] == "Critical" else "#FFBB33" if alert["priority"] == "High" else "#33B5E5"
        time_ago = datetime.now() - alert["timestamp"]
        time_str = f"{int(time_ago.total_seconds() // 60)}m ago"
        
        with st.container():
            st.markdown(f"""
            <div class="voice-alert">
                <div style="
                    width: 44px;
                    height: 44px;
                    background: linear-gradient(135deg, #6C63FF 0%, #5A52E0 100%);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 20px;
                ">🔊</div>
                <div style="flex: 1;">
                    <div style="color: #ffffff; font-size: 13px; font-weight: 500; line-height: 1.4;">{alert['message']}</div>
                    <div style="color: #8888aa; font-size: 11px; margin-top: 4px;">
                        <span style="color: {priority_color};">● {alert['priority']}</span> • {time_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Replay", key=f"play_{alert['id']}", use_container_width=True):
                st.info("🔊 Playing voice alert...")
        with col2:
            if st.button("✓ Dismiss", key=f"dismiss_{alert['id']}", use_container_width=True):
                st.session_state.nurse_alerts.remove(alert)
                st.rerun()


def render_task_progress():
    """Render task progress section"""
    completed = len([t for t in st.session_state.nurse_tasks if t["is_completed"]])
    total = len(st.session_state.nurse_tasks)
    progress = (completed / total * 100) if total > 0 else 0
    
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">✅</span>
        <span class="section-title">Task Progress</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.metric("Done", f"{completed}")
    with col2:
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-fill" style="width: {progress}%;"></div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.metric("Total", f"{total}")


def render_task_checklist():
    """Render AI-generated task checklist"""
    task_count = len(st.session_state.nurse_tasks)
    urgent_count = len([t for t in st.session_state.nurse_tasks if t["is_urgent"] and not t["is_completed"]])
    
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">📋</span>
        <span class="section-title">Today's Tasks</span>
        {f'<span style="background: rgba(255, 68, 68, 0.2); color: #FF6B6B; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">{urgent_count} urgent</span>' if urgent_count > 0 else ''}
    </div>
    <p style="color: #6C63FF; font-size: 12px; margin: -8px 0 16px 0;">🤖 AI-generated based on patient needs</p>
    """, unsafe_allow_html=True)
    
    # Sort tasks: urgent first, then by time
    sorted_tasks = sorted(
        st.session_state.nurse_tasks,
        key=lambda x: (x["is_completed"], not x["is_urgent"], x["scheduled_time"])
    )
    
    for task in sorted_tasks:
        task_class = "task-completed" if task["is_completed"] else "task-urgent" if task["is_urgent"] else ""
        urgent_badge = "🔴 URGENT" if task["is_urgent"] and not task["is_completed"] else ""
        status_icon = "✅" if task["is_completed"] else "⏰"
        
        task_type_icons = {
            "MEDICINE": "💊",
            "VITALS": "📊",
            "CHECKUP": "🩺",
            "VERIFY": "✔️"
        }
        type_icon = task_type_icons.get(task["task_type"], "📋")
        
        with st.container():
            if task["is_urgent"] and not task["is_completed"]:
                st.error(f"{type_icon} {task['description']} 🔴 URGENT")
            elif task["is_completed"]:
                st.success(f"✅ {type_icon} {task['description']}")
            else:
                st.info(f"{type_icon} {task['description']}")
            st.caption(f"👤 {task['patient_name']} • 🛏️ {task['bed_id']} • {status_icon} {task['scheduled_time']}")
        
        if not task["is_completed"]:
            if st.checkbox(
                f"Mark Complete: {task['description'][:30]}...",
                key=f"task_{task['id']}",
                value=False
            ):
                # Log to backend
                from services.api_service import api_service
                api_service.complete_task(task['id'], st.session_state.staff_id)
                
                task["is_completed"] = True
                st.success(f"✅ Completed: {task['description']}")
                st.rerun()


def render_bed_overview():
    """Render bed assignment overview"""
    st.markdown("---")
    
    bed_count = len(st.session_state.nurse_beds)
    critical_count = len([b for b in st.session_state.nurse_beds if b["status"] == "critical"])
    
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">🛏️</span>
        <span class="section-title">My Assigned Beds</span>
        <span class="badge-count">{bed_count}</span>
        {f'<span style="background: rgba(255, 68, 68, 0.2); color: #FF6B6B; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">{critical_count} critical</span>' if critical_count > 0 else ''}
    </div>
    """, unsafe_allow_html=True)
    
    status_colors = {
        "occupied": "#33B5E5",
        "critical": "#FF4444",
        "monitoring": "#FFBB33",
        "empty": "#666"
    }
    
    for bed in st.session_state.nurse_beds:
        color = status_colors.get(bed["status"], "#33B5E5")
        condition_color = "#FF4444" if bed["condition"] == "Critical" else "#00C851" if bed["condition"] == "Stable" else "#FFBB33"
        
        st.markdown(f"""
        <div class="bed-card">
            <div>
                <div style="color: #ffffff; font-size: 15px; font-weight: 600;">🛏️ {bed['bed_id']}</div>
                <div style="color: #8888aa; font-size: 12px; margin-top: 2px;">👤 {bed['patient']}</div>
            </div>
            <div style="
                background: {condition_color}20;
                color: {condition_color};
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            ">{bed['condition']}</div>
        </div>
        """, unsafe_allow_html=True)
def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("---")
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">⚡</span>
        <span class="section-title">Quick Actions</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Emergency", key="emergency_btn", use_container_width=True):
            st.session_state.code_blue_active = True
            st.rerun()
    
    with col2:
        if st.button("📞 Call Doctor", key="call_doctor_btn", use_container_width=True):
            st.info("📞 Connecting to on-duty doctor...")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("📊 All Vitals", key="all_vitals_btn", use_container_width=True):
            st.info("Loading vitals dashboard...")
    
    with col4:
        if st.button("➕ Add Task", key="add_task_btn", use_container_width=True):
            st.info("Opening task form...")


def render_nurse_view():
    """Main render function for nurse view"""
    init_nurse_state()
    
    render_header()
    render_code_blue_banner()
    render_voice_alerts()
    render_task_progress()
    render_task_checklist()
    render_bed_overview()
    render_quick_actions()
    
    # Footer
    st.markdown("""
    <div style="
        text-align: center;
        padding: 40px 0 20px 0;
        margin-top: 30px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #444455; font-size: 11px; margin: 0;">
            VitalFlow AI • Nurse Interface
        </p>
        <p style="color: #333344; font-size: 10px; margin: 6px 0 0 0;">
            🔄 Last sync: Just now
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Nurse View", page_icon="👩‍⚕️", layout="centered")
    st.session_state.staff_id = "N001"
    st.session_state.staff_name = "Nurse Demo"
    render_nurse_view()
