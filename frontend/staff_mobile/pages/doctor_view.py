"""
VitalFlow AI - Doctor View
Mobile interface for doctors with punch in/out, fatigue tracking,
and patient transfer approvals
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
    
    /* UI STYLE ONLY - Healthcare theme */
    .stApp {max-width: 480px; margin: 0 auto; background: #F4F7FA !important;}
    
    /* UI STYLE ONLY - Punch buttons using #27AE60 for action */
    .punch-btn-in button {
        background: #27AE60 !important;
        color: white !important;
        height: 64px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(39, 174, 96, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    
    .punch-btn-in button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(39, 174, 96, 0.35) !important;
        background: #219653 !important;
    }
    
    .punch-btn-out button {
        background: #EB5757 !important;
        color: white !important;
        height: 64px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(235, 87, 87, 0.25) !important;
    }
    
    .punch-btn-out button:hover {
        background: #d64545 !important;
        transform: translateY(-1px) !important;
    }
    
    /* UI STYLE ONLY - Status card with panel background */
    .status-card {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 14px;
        padding: 20px 16px;
        margin: 16px 0;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    
    .status-on {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(39, 174, 96, 0.15);
        color: #27AE60;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .status-off {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #CBD5E1;
        color: #4B5563;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* UI STYLE ONLY - Fatigue alerts with warning color */
    .fatigue-warning {
        background: #E9EEF3;
        border: 1px solid #EB5757;
        border-left: 4px solid #EB5757;
        color: #1F2937;
        padding: 14px 16px;
        border-radius: 10px;
        text-align: left;
        margin: 16px 0;
    }
    
    .fatigue-caution {
        background: #E9EEF3;
        border: 1px solid #F2994A;
        border-left: 4px solid #F2994A;
        color: #1F2937;
        padding: 14px 16px;
        border-radius: 10px;
        text-align: left;
        margin: 16px 0;
    }
    
    /* UI STYLE ONLY - Critical card */
    .critical-card {
        background: #E9EEF3;
        border: 1px solid #EB5757;
        border-left: 4px solid #EB5757;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    
    /* UI STYLE ONLY - Approval card */
    .approval-card {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    
    /* UI STYLE ONLY - Progress bar */
    .progress-container {
        background: #CBD5E1;
        border-radius: 8px;
        padding: 3px;
        margin: 12px 0;
    }
    
    .progress-bar {
        height: 8px;
        border-radius: 6px;
        transition: width 0.4s ease;
    }
    
    /* UI STYLE ONLY - Vitals box */
    .vitals-box {
        text-align: center;
        padding: 14px 12px;
        background: #E9EEF3;
        border-radius: 10px;
        border: 1px solid #CBD5E1;
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
    
    /* UI STYLE ONLY - Transfer flow */
    .transfer-box {
        text-align: center;
        padding: 10px;
        background: #E9EEF3;
        border-radius: 8px;
        border: 1px solid #CBD5E1;
    }
    
    .transfer-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        color: #4B5563;
    }
    
    .transfer-value {
        font-size: 13px;
        font-weight: 600;
        color: #1F2937;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


def init_doctor_state():
    """Initialize doctor-specific session state"""
    if 'doctor_on_duty' not in st.session_state:
        st.session_state.doctor_on_duty = False
    if 'doctor_shift_start' not in st.session_state:
        st.session_state.doctor_shift_start = None
    if 'doctor_hours_worked' not in st.session_state:
        st.session_state.doctor_hours_worked = 0.0
    if 'pending_approvals' not in st.session_state:
        st.session_state.pending_approvals = generate_mock_approvals()
    if 'critical_patients' not in st.session_state:
        st.session_state.critical_patients = generate_mock_critical_patients()


def generate_mock_approvals():
    """Generate mock transfer approval requests"""
    return [
        {
            "id": "TR001",
            "patient_name": "Raj Kumar",
            "patient_id": "P001",
            "from_bed": "Ward-2 Bed-5",
            "to_bed": "ICU-4",
            "reason": "Critical condition - SpO2 dropping below 88%",
            "urgency": "Critical",
            "requested_by": "Nurse Priya",
            "requested_at": datetime.now() - timedelta(minutes=5),
            "vitals": {"spo2": 87, "heart_rate": 125}
        },
        {
            "id": "TR002",
            "patient_name": "Sunita Devi",
            "patient_id": "P002",
            "from_bed": "General-8",
            "to_bed": "Ward-3 Bed-2",
            "reason": "Post-surgery observation complete",
            "urgency": "Medium",
            "requested_by": "Nurse Anjali",
            "requested_at": datetime.now() - timedelta(minutes=15),
            "vitals": {"spo2": 96, "heart_rate": 78}
        },
        {
            "id": "TR003",
            "patient_name": "Vikram Singh",
            "patient_id": "P003",
            "from_bed": "Emergency-2",
            "to_bed": "ICU-7",
            "reason": "Cardiac monitoring required",
            "urgency": "High",
            "requested_by": "Nurse Meena",
            "requested_at": datetime.now() - timedelta(minutes=8),
            "vitals": {"spo2": 92, "heart_rate": 110}
        }
    ]


def generate_mock_critical_patients():
    """Generate mock critical patients for verification"""
    return [
        {
            "id": "P101",
            "name": "Amit Patel",
            "bed": "ICU-3",
            "condition": "Cardiac Arrest Risk",
            "spo2": 85,
            "heart_rate": 135,
            "alert": "Immediate verification needed"
        },
        {
            "id": "P102",
            "name": "Deepak Sharma",
            "bed": "ICU-6",
            "condition": "Respiratory Distress",
            "spo2": 88,
            "heart_rate": 118,
            "alert": "Ventilator adjustment required"
        }
    ]


def generate_vitals_history():
    """Generate mock vitals history for charts"""
    import random
    history = []
    base_spo2 = 91
    base_hr = 95
    
    for i in range(30):
        timestamp = (datetime.now() - timedelta(minutes=(30 - i))).strftime("%H:%M")
        history.append({
            "timestamp": timestamp,
            "spo2": round(base_spo2 + random.uniform(-3, 5), 1),
            "heart_rate": base_hr + random.randint(-15, 20)
        })
    return history


def calculate_hours_worked():
    """Calculate hours worked since shift start"""
    if st.session_state.doctor_shift_start:
        delta = datetime.now() - st.session_state.doctor_shift_start
        return delta.total_seconds() / 3600
    return 0.0


def render_punch_section():
    """Render punch in/out section"""
    # UI STYLE ONLY - Header with healthcare colors
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="
            font-size: 20px;
            font-weight: 700;
            color: #1F2937;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        ">👨‍⚕️ Doctor Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # UI STYLE ONLY - Staff info card
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 16px;
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        margin-bottom: 16px;
    ">
        <div style="
            width: 42px;
            height: 42px;
            background: #2F80ED;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        ">👨‍⚕️</div>
        <div>
            <div style="color: #1F2937; font-weight: 600; font-size: 15px;">{st.session_state.staff_name}</div>
            <div style="color: #4B5563; font-size: 12px;">ID: {st.session_state.staff_id}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Punch In/Out Toggle
    if st.session_state.doctor_on_duty:
        hours = calculate_hours_worked()
        st.session_state.doctor_hours_worked = hours
        
        # Status display
        hours_display = f"{int(hours)}h {int((hours % 1) * 60)}m"
        
        # UI STYLE ONLY - Status display
        st.markdown(f"""
        <div class="status-card">
            <div class="status-on">
                <span style="font-size: 8px;">●</span> ON DUTY
            </div>
            <div style="color: #1F2937; font-size: 36px; font-weight: 700; letter-spacing: -0.5px; margin: 8px 0;">{hours_display}</div>
            <div style="color: #4B5563; font-size: 12px; font-weight: 500;">Time on Shift</div>
        </div>
        """, unsafe_allow_html=True)
        
        # UI STYLE ONLY - Progress bar colors
        progress = min(hours / 12, 1.0)
        progress_color = "#27AE60" if hours < 10 else "#F2994A" if hours < 12 else "#EB5757"
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="background: {progress_color}; width: {progress * 100}%;"></div>
        </div>
        <div style="text-align: center; color: #4B5563; font-size: 12px; font-weight: 500;">{hours:.1f} / 12 hours max recommended</div>
        """, unsafe_allow_html=True)
        
        # UI STYLE ONLY - Fatigue warnings
        if hours >= 12:
            st.markdown("""
            <div class="fatigue-warning">
                <span style="font-size: 24px;">⚠️</span>
                <strong style="font-size: 15px; margin-left: 8px;">FATIGUE ALERT</strong><br>
                <span style="font-size: 12px; color: #4B5563;">No new critical cases will be assigned</span>
            </div>
            """, unsafe_allow_html=True)
        elif hours >= 10:
            st.markdown("""
            <div class="fatigue-caution">
                <span style="font-size: 24px;">⏰</span>
                <strong style="font-size: 15px; margin-left: 8px;">Approaching Shift Limit</strong><br>
                <span style="font-size: 12px; color: #4B5563;">Consider wrapping up soon</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Punch Out button
        st.markdown('<div class="punch-btn-out">', unsafe_allow_html=True)
        if st.button("🔴 PUNCH OUT", key="punch_out", use_container_width=True):
            # Log action for backend
            from services.api_service import api_service
            api_service.punch_out(st.session_state.staff_id, hours)
            
            st.session_state.doctor_on_duty = False
            st.session_state.doctor_shift_start = None
            st.session_state.doctor_hours_worked = 0.0
            st.success("✅ Punched out successfully!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # UI STYLE ONLY - Off duty display
        st.markdown("""
        <div class="status-card">
            <div class="status-off">
                <span style="font-size: 8px;">○</span> OFF DUTY
            </div>
            <div style="color: #4B5563; font-size: 24px; font-weight: 600; margin: 12px 0;">Not on shift</div>
            <div style="color: #6B7280; font-size: 13px;">Tap below to start your shift</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Punch In button
        st.markdown('<div class="punch-btn-in">', unsafe_allow_html=True)
        if st.button("🟢 PUNCH IN", key="punch_in", use_container_width=True):
            # Log action for backend
            from services.api_service import api_service
            api_service.punch_in(st.session_state.staff_id)
            
            st.session_state.doctor_on_duty = True
            st.session_state.doctor_shift_start = datetime.now()
            st.success("✅ Punched in successfully!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_critical_patients():
    """Render critical patients needing verification"""
    if not st.session_state.doctor_on_duty:
        return
    
    st.markdown("---")
    
    # Section header
    critical_count = len(st.session_state.critical_patients)
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">🚨</span>
        <span class="section-title">Critical Patients</span>
        <span class="badge-count">{critical_count}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.critical_patients:
        st.success("✅ No critical patients at the moment")
        return
    
    for patient in st.session_state.critical_patients:
        spo2_color = "#FF4444" if patient["spo2"] < 90 else "#FFBB33" if patient["spo2"] < 95 else "#00C851"
        hr_color = "#FF4444" if patient["heart_rate"] > 120 or patient["heart_rate"] < 50 else "#00C851"
        
        # Use st.container for proper rendering
        with st.container():
            st.markdown(f"""<div class="critical-card"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div style="color: #fff; font-size: 18px; font-weight: 600;">👤 {patient['name']}</div><div style="color: #888; font-size: 13px;">🛏️ {patient['bed']} • {patient['condition']}</div></div><div style="color: #FF4444; font-size: 12px;">● CRITICAL</div></div></div>""", unsafe_allow_html=True)
            
            # Vitals display using columns
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                st.markdown(f"""<div style="text-align: center; padding: 15px; background: #0d0d1a; border-radius: 10px;"><div style="color: {spo2_color}; font-size: 28px; font-weight: bold;">🫁 {patient['spo2']}%</div><div style="color: #888; font-size: 12px;">SpO2</div></div>""", unsafe_allow_html=True)
            with v_col2:
                st.markdown(f"""<div style="text-align: center; padding: 15px; background: #0d0d1a; border-radius: 10px;"><div style="color: {hr_color}; font-size: 28px; font-weight: bold;">❤️ {patient['heart_rate']}</div><div style="color: #888; font-size: 12px;">BPM</div></div>""", unsafe_allow_html=True)
            
            st.warning(f"⚠️ {patient['alert']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verified", key=f"verify_{patient['id']}", use_container_width=True):
                st.session_state.critical_patients.remove(patient)
                st.success(f"Verified {patient['name']}")
                st.rerun()
        with col2:
            if st.button("📞 Call Nurse", key=f"call_{patient['id']}", use_container_width=True):
                st.info("Calling assigned nurse...")


def render_pending_approvals():
    """Render pending transfer approval requests"""
    if not st.session_state.doctor_on_duty:
        return
    
    st.markdown("---")
    
    # Section header
    approval_count = len(st.session_state.pending_approvals)
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">📋</span>
        <span class="section-title">Pending Approvals</span>
        <span class="badge-count">{approval_count}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <p style="color: #8888aa; font-size: 13px; margin: -8px 0 16px 0;">
        {approval_count} transfer{'s' if approval_count != 1 else ''} awaiting your approval
    </p>
    """, unsafe_allow_html=True)
    
    if not st.session_state.pending_approvals:
        st.success("✅ No pending approvals")
        return
    
    for approval in st.session_state.pending_approvals:
        urgency_colors = {
            "Critical": "#FF4444",
            "High": "#FF8800",
            "Medium": "#FFBB33",
            "Low": "#00C851"
        }
        color = urgency_colors.get(approval["urgency"], "#33B5E5")
        
        spo2 = approval["vitals"]["spo2"]
        hr = approval["vitals"]["heart_rate"]
        spo2_color = "#FF4444" if spo2 < 90 else "#FFBB33" if spo2 < 95 else "#00C851"
        hr_color = "#FF4444" if hr > 110 or hr < 60 else "#00C851"
        
        time_ago = datetime.now() - approval["requested_at"]
        time_str = f"{int(time_ago.total_seconds() // 60)}m ago"
        
        with st.container():
            # Header with patient name and urgency badge
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.markdown(f"#### 👤 {approval['patient_name']}")
            with h_col2:
                st.markdown(f"""<span style="background: {color}30; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 12px;">{approval['urgency']}</span>""", unsafe_allow_html=True)
            
            # Transfer route
            t_col1, t_col2, t_col3 = st.columns([2, 1, 2])
            with t_col1:
                st.markdown(f"""<div style="text-align: center; padding: 10px; background: #0d0d1a; border-radius: 8px;"><div style="color: #FF6B6B; font-size: 11px;">FROM</div><div style="color: #fff; font-size: 13px; font-weight: 500;">{approval['from_bed']}</div></div>""", unsafe_allow_html=True)
            with t_col2:
                st.markdown("""<div style="text-align: center; padding: 15px; color: #6C63FF; font-size: 24px;">→</div>""", unsafe_allow_html=True)
            with t_col3:
                st.markdown(f"""<div style="text-align: center; padding: 10px; background: #0d0d1a; border-radius: 8px;"><div style="color: #00C851; font-size: 11px;">TO</div><div style="color: #fff; font-size: 13px; font-weight: 500;">{approval['to_bed']}</div></div>""", unsafe_allow_html=True)
            
            st.caption(f"📋 {approval['reason']}")
            
            # Vitals display
            vt_col1, vt_col2 = st.columns(2)
            with vt_col1:
                st.metric("🫁 SpO2", f"{spo2}%")
            with vt_col2:
                st.metric("❤️ Heart Rate", f"{hr} BPM")
            
            st.caption(f"Requested by {approval['requested_by']} • {time_str}")
        
        # Mini vitals chart expander
        with st.expander("📊 View Vitals History"):
            import pandas as pd
            vitals_history = generate_vitals_history()
            df = pd.DataFrame(vitals_history)
            
            st.markdown("**SpO2 (Last 30 min)**")
            st.line_chart(df.set_index("timestamp")["spo2"], use_container_width=True)
            
            st.markdown("**Heart Rate (Last 30 min)**")
            st.line_chart(df.set_index("timestamp")["heart_rate"], use_container_width=True)
        
        # Approval buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{approval['id']}", use_container_width=True):
                # Log to backend
                from services.api_service import api_service
                api_service.approve_transfer(approval['id'], st.session_state.staff_id)
                
                st.session_state.pending_approvals.remove(approval)
                st.success(f"✅ Approved transfer for {approval['patient_name']}")
                st.rerun()
        
        with col2:
            if st.button("❌ Decline", key=f"decline_{approval['id']}", use_container_width=True):
                # Log to backend
                from services.api_service import api_service
                api_service.decline_transfer(approval['id'], st.session_state.staff_id, "Doctor declined")
                
                st.session_state.pending_approvals.remove(approval)
                st.warning(f"❌ Declined transfer for {approval['patient_name']}")
                st.rerun()
        
        st.markdown("<hr style='border-color: #2d2d4a; margin: 20px 0;'>", unsafe_allow_html=True)


def render_doctor_view():
    """Main render function for doctor view"""
    init_doctor_state()
    
    render_punch_section()
    render_critical_patients()
    render_pending_approvals()
    
    # Footer
    st.markdown("""
    <div style="
        text-align: center;
        padding: 40px 0 20px 0;
        margin-top: 30px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #444455; font-size: 11px; margin: 0;">
            VitalFlow AI • Doctor Interface
        </p>
        <p style="color: #333344; font-size: 10px; margin: 6px 0 0 0;">
            🔄 Last sync: Just now
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Doctor View", page_icon="👨‍⚕️", layout="centered")
    st.session_state.staff_id = "D001"
    st.session_state.staff_name = "Dr. Demo"
    render_doctor_view()
