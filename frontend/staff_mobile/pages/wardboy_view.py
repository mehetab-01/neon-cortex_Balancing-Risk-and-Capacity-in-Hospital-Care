"""
VitalFlow AI - Ward Boy View
Mobile interface for ward boys with transfer tickets
and simple task management
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
    
    /* UI STYLE ONLY - Wardboy header with primary blue */
    .wardboy-header {
        background: #2F80ED;
        color: white;
        padding: 20px 18px;
        border-radius: 14px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.25);
    }
    
    /* UI STYLE ONLY - Transfer card */
    .transfer-card {
        background: #E9EEF3;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border: 1px solid #CBD5E1;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }
    
    .transfer-card:hover {
        transform: translateY(-1px);
        border-color: #2F80ED;
    }
    
    .transfer-urgent {
        border-color: #EB5757 !important;
        border-left: 4px solid #EB5757;
    }
    
    .transfer-high {
        border-color: #F2994A !important;
        border-left: 4px solid #F2994A;
    }
    
    /* UI STYLE ONLY - Location box */
    .location-box {
        background: #E9EEF3;
        border-radius: 10px;
        padding: 12px;
        margin: 10px 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        border: 1px solid #CBD5E1;
    }
    
    .location-item {
        text-align: center;
        flex: 1;
    }
    
    .location-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        margin-bottom: 4px;
        color: #4B5563;
    }
    
    .location-value {
        font-size: 13px;
        font-weight: 600;
        color: #1F2937;
    }
    
    /* UI STYLE ONLY - Stats card */
    .stats-card {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 14px;
        padding: 18px;
        margin: 16px 0;
    }
    
    .stats-row {
        display: flex;
        justify-content: space-around;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #2F80ED;
    }
    
    .stat-label {
        font-size: 11px;
        color: #4B5563;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
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
    
    /* UI STYLE ONLY - Urgency badges */
    .urgency-badge {
        padding: 4px 10px;
        border-radius: 14px;
        font-size: 11px;
        font-weight: 600;
    }
    
    .urgency-critical {
        background: rgba(235, 87, 87, 0.15);
        color: #EB5757;
    }
    
    .urgency-high {
        background: rgba(242, 153, 74, 0.15);
        color: #F2994A;
    }
    
    .urgency-medium {
        background: rgba(242, 153, 74, 0.1);
        color: #F2994A;
    }
    
    .urgency-low {
        background: rgba(39, 174, 96, 0.15);
        color: #27AE60;
    }
    
    /* UI STYLE ONLY - Complete button */
    .complete-btn button {
        background: #27AE60 !important;
        color: white !important;
        height: 56px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(39, 174, 96, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)


def init_wardboy_state():
    """Initialize ward boy-specific session state"""
    if 'transfer_queue' not in st.session_state:
        st.session_state.transfer_queue = generate_mock_transfers()
    if 'completed_transfers' not in st.session_state:
        st.session_state.completed_transfers = 0


def generate_mock_transfers():
    """Generate mock transfer tickets"""
    transfers = [
        {
            "id": "TF001",
            "patient_name": "Raj Kumar",
            "patient_id": "P001",
            "from_bed": "Ward-2 Bed-5",
            "to_bed": "ICU-4",
            "urgency": "Critical",
            "reason": "Critical condition - needs ICU",
            "requested_at": datetime.now() - timedelta(minutes=5),
            "approved_by": "Dr. Sharma",
            "notes": "Handle with care - oxygen support needed"
        },
        {
            "id": "TF002",
            "patient_name": "Sunita Devi",
            "patient_id": "P002",
            "from_bed": "ICU-2",
            "to_bed": "General-8",
            "urgency": "Medium",
            "reason": "Patient stable - moving to general ward",
            "requested_at": datetime.now() - timedelta(minutes=15),
            "approved_by": "Dr. Patel",
            "notes": ""
        },
        {
            "id": "TF003",
            "patient_name": "Vikram Singh",
            "patient_id": "P003",
            "from_bed": "Emergency-1",
            "to_bed": "Ward-3 Bed-7",
            "urgency": "High",
            "reason": "Post-surgery observation",
            "requested_at": datetime.now() - timedelta(minutes=10),
            "approved_by": "Dr. Kumar",
            "notes": "Post-surgery - gentle movement required"
        },
        {
            "id": "TF004",
            "patient_name": "Meena Kumari",
            "patient_id": "P004",
            "from_bed": "General-12",
            "to_bed": "Discharge Area",
            "urgency": "Low",
            "reason": "Discharge preparation",
            "requested_at": datetime.now() - timedelta(minutes=30),
            "approved_by": "Dr. Sharma",
            "notes": "Patient can walk with assistance"
        }
    ]
    return transfers


def render_header():
    """Render ward boy dashboard header"""
    pending = len(st.session_state.transfer_queue)
    
    st.markdown(f"""
    <div class="wardboy-header">
        <div style="font-size: 13px; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase;">🧑‍🔧 Ward Boy Dashboard</div>
        <div style="font-size: 28px; font-weight: 800; margin: 12px 0; letter-spacing: -0.5px;">
            {st.session_state.staff_name}
        </div>
        <div style="font-size: 12px; opacity: 0.85;">ID: {st.session_state.staff_id} • {pending} pending transfers</div>
    </div>
    """, unsafe_allow_html=True)


def render_stats():
    """Render quick stats"""
    pending = len(st.session_state.transfer_queue)
    urgent = len([t for t in st.session_state.transfer_queue if t["urgency"] in ["Critical", "High"]])
    completed = st.session_state.completed_transfers
    
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-value">{pending}</div>
                <div class="stat-label">📝 Pending</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="background: linear-gradient(135deg, #FF4444 0%, #FF6B6B 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{urgent}</div>
                <div class="stat-label">🚨 Urgent</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="background: linear-gradient(135deg, #00C851 0%, #38ef7d 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{completed}</div>
                <div class="stat-label">✅ Done</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transfer_queue():
    """Render transfer ticket queue"""
    queue_count = len(st.session_state.transfer_queue)
    
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">🛏️</span>
        <span class="section-title">Transfer Queue</span>
        <span class="badge-count">{queue_count}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.transfer_queue:
        st.success("✅ All transfers completed! Great work!")
        return
    
    # Sort by urgency
    urgency_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_transfers = sorted(
        st.session_state.transfer_queue,
        key=lambda x: urgency_order.get(x["urgency"], 4)
    )
    
    for transfer in sorted_transfers:
        urgency_colors = {
            "Critical": "#FF4444",
            "High": "#FF8800",
            "Medium": "#FFBB33",
            "Low": "#00C851"
        }
        urgency_classes = {
            "Critical": "urgency-critical",
            "High": "urgency-high",
            "Medium": "urgency-medium",
            "Low": "urgency-low"
        }
        color = urgency_colors.get(transfer["urgency"], "#33B5E5")
        urgency_class = urgency_classes.get(transfer["urgency"], "urgency-medium")
        
        time_ago = datetime.now() - transfer["requested_at"]
        time_str = f"{int(time_ago.total_seconds() // 60)}m ago"
        
        urgency_icon = "🚨" if transfer["urgency"] == "Critical" else "⚠️" if transfer["urgency"] == "High" else "📋"
        
        with st.container():
            # Transfer card with styled header
            st.markdown(f"""
            <div class="transfer-card {'transfer-urgent' if transfer['urgency'] == 'Critical' else 'transfer-high' if transfer['urgency'] == 'High' else ''}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <div style="color: #ffffff; font-size: 17px; font-weight: 700;">👤 {transfer['patient_name']}</div>
                        <div style="color: #8888aa; font-size: 12px; margin-top: 2px;">ID: {transfer['patient_id']}</div>
                    </div>
                    <div class="urgency-badge {urgency_class}">{urgency_icon} {transfer['urgency']}</div>
                </div>
                
                <div class="location-box">
                    <div class="location-item">
                        <div class="location-label" style="color: #FF6B6B;">FROM</div>
                        <div class="location-value">🛏️ {transfer['from_bed']}</div>
                    </div>
                    <div style="font-size: 24px; color: #6C63FF;">→</div>
                    <div class="location-item">
                        <div class="location-label" style="color: #00C851;">TO</div>
                        <div class="location-value">🛏️ {transfer['to_bed']}</div>
                    </div>
                </div>
                
                <div style="color: #8888aa; font-size: 12px; margin-top: 8px;">
                    📋 {transfer['reason']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if transfer.get("notes"):
                st.warning(f"⚠️ Note: {transfer['notes']}")
            
            st.caption(f"✓ Approved by: {transfer['approved_by']} • 🕐 {time_str}")
        
        # Mark Complete button
        st.markdown('<div class="complete-btn">', unsafe_allow_html=True)
        if st.button(f"✅ Mark Transfer Complete", key=f"complete_{transfer['id']}", use_container_width=True):
            # Log to backend
            from services.api_service import api_service
            api_service.complete_transfer(transfer['id'], st.session_state.staff_id)
            
            st.session_state.transfer_queue.remove(transfer)
            st.session_state.completed_transfers += 1
            st.success(f"✅ Transfer completed for {transfer['patient_name']}")
            st.balloons()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Divider
        st.markdown("""<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, #3d3d5c, transparent); margin: 20px 0;">""", unsafe_allow_html=True)


def render_quick_actions():
    """Render quick action buttons"""
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">⚡</span>
        <span class="section-title">Quick Actions</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📞 Call Nurse", key="call_nurse", use_container_width=True):
            st.info("📞 Connecting to nurse station...")
    
    with col2:
        if st.button("🆘 Need Help", key="need_help", use_container_width=True):
            st.warning("🆘 Help request sent to supervisor")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🔄 Refresh Queue", key="refresh", use_container_width=True):
            st.session_state.transfer_queue = generate_mock_transfers()
            st.rerun()
    
    with col4:
        if st.button("📊 My Stats", key="my_stats", use_container_width=True):
            st.info(f"Today's completed: {st.session_state.completed_transfers}")


def render_wardboy_view():
    """Main render function for ward boy view"""
    init_wardboy_state()
    
    render_header()
    render_stats()
    render_transfer_queue()
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
            VitalFlow AI • Ward Boy Interface
        </p>
        <p style="color: #333344; font-size: 10px; margin: 6px 0 0 0;">
            🔄 Last sync: Just now
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Ward Boy View", page_icon="🧑‍🔧", layout="centered")
    st.session_state.staff_id = "W001"
    st.session_state.staff_name = "Ward Boy Demo"
    render_wardboy_view()
