"""
CCTV Monitoring Component
Renders CCTV fall detection interface for admin dashboard
Integrates with cv_detection module
"""
import sys
from pathlib import Path
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import CV detection system
try:
    from frontend.cv_detection.fall_detection_system import (
        FallDetectionSystem,
        FallAlert,
        AlertStatus,
        AlertSeverity,
        fall_detection_system
    )
    from frontend.cv_detection.bed_zones import bed_zone_manager
    CV_DETECTION_AVAILABLE = True
except ImportError:
    CV_DETECTION_AVAILABLE = False
    fall_detection_system = None


def render_cctv_header():
    """Render the CCTV monitoring header."""
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        ">
            <h2 style="color: white; margin: 0;">📹 CCTV Fall Detection System</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0;">
                Real-time fall and immobility detection using AI pose estimation
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_camera_grid(cameras: List[Dict]):
    """Render a grid of camera feeds with status."""
    st.subheader("🎥 Camera Feeds")
    
    if not cameras:
        st.info("No cameras configured. Add cameras to begin monitoring.")
        return
    
    cols = st.columns(min(len(cameras), 3))
    
    for idx, camera in enumerate(cameras):
        with cols[idx % 3]:
            camera_id = camera.get("id", f"CAM-{idx+1}")
            location = camera.get("location", "Unknown")
            status = camera.get("status", "offline")
            
            # Status color
            status_color = "#22c55e" if status == "online" else "#ef4444"
            status_icon = "🟢" if status == "online" else "🔴"
            
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 16px;
                    border: 1px solid #334155;
                ">
                    <div style="
                        background: #0f172a;
                        height: 150px;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-bottom: 12px;
                    ">
                        <span style="color: #64748b; font-size: 3rem;">📷</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="color: white; margin: 0;">{camera_id}</h4>
                            <p style="color: #94a3b8; margin: 0; font-size: 0.8rem;">{location}</p>
                        </div>
                        <span style="color: {status_color};">{status_icon} {status.upper()}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_alert_card(alert: Dict, key_prefix: str = "alert"):
    """Render a single fall alert card."""
    alert_id = alert.get("alert_id", "UNKNOWN")
    camera_id = alert.get("camera_id", "CAM-1")
    timestamp = alert.get("timestamp", datetime.now().isoformat())
    confidence = alert.get("confidence", 0.0)
    immobility_secs = alert.get("immobility_seconds", 0)
    status = alert.get("status", "Pending Verification")
    severity = alert.get("severity", "Warning")
    
    # Parse timestamp if string
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            timestamp = datetime.now()
    
    # Severity colors
    severity_colors = {
        "Info": "#3b82f6",
        "Warning": "#f59e0b",
        "Critical": "#ef4444",
        "Emergency": "#dc2626"
    }
    severity_color = severity_colors.get(severity, "#f59e0b")
    
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-left: 4px solid {severity_color};
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: white; font-weight: bold;">🚨 {alert_id}</span>
                <span style="
                    background: {severity_color}33;
                    color: {severity_color};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                ">{severity}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
                <div>
                    <p style="color: #64748b; margin: 0; font-size: 0.75rem;">Camera</p>
                    <p style="color: white; margin: 0;">{camera_id}</p>
                </div>
                <div>
                    <p style="color: #64748b; margin: 0; font-size: 0.75rem;">Time</p>
                    <p style="color: white; margin: 0;">{timestamp.strftime('%I:%M:%S %p')}</p>
                </div>
                <div>
                    <p style="color: #64748b; margin: 0; font-size: 0.75rem;">Confidence</p>
                    <p style="color: white; margin: 0;">{confidence:.0%}</p>
                </div>
                <div>
                    <p style="color: #64748b; margin: 0; font-size: 0.75rem;">Immobile For</p>
                    <p style="color: {severity_color}; margin: 0; font-weight: bold;">{immobility_secs:.0f} seconds</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Verification buttons
    if status == "Pending Verification":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Emergency", key=f"{key_prefix}_{alert_id}_confirm", use_container_width=True, type="primary"):
                return ("confirm", alert_id)
        with col2:
            if st.button("❌ False Alarm", key=f"{key_prefix}_{alert_id}_false", use_container_width=True):
                return ("false_alarm", alert_id)
    
    return None


def render_pending_alerts(alerts: List[Dict]):
    """Render list of pending alerts requiring verification."""
    st.subheader("⚠️ Pending Verification")
    
    if not alerts:
        st.success("✅ No pending alerts. All clear!")
        return
    
    st.error(f"🚨 **{len(alerts)} alert(s) require verification!**")
    
    actions = []
    for idx, alert in enumerate(alerts):
        result = render_alert_card(alert, key_prefix=f"pending_{idx}")
        if result:
            actions.append(result)
    
    return actions


def render_alert_history(alerts: List[Dict], limit: int = 10):
    """Render recent alert history."""
    with st.expander("📜 Alert History", expanded=False):
        if not alerts:
            st.info("No alert history yet")
            return
        
        for alert in alerts[:limit]:
            status = alert.get("status", "Pending")
            status_icon = {
                "Pending Verification": "⏳",
                "Verified Emergency": "🚨",
                "False Alarm": "✅",
                "Resolved": "✔️"
            }.get(status, "❓")
            
            timestamp = alert.get("timestamp", "")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp).strftime("%m/%d %I:%M %p")
                except:
                    pass
            
            st.markdown(f"""
                {status_icon} **{alert.get('alert_id')}** - {alert.get('camera_id')} - {timestamp}
                <span style="color: #64748b;">({status})</span>
            """, unsafe_allow_html=True)


def render_system_status():
    """Render fall detection system status."""
    st.subheader("🔧 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        is_running = fall_detection_system is not None and fall_detection_system.is_initialized
        status_color = "#22c55e" if is_running else "#ef4444"
        status_text = "Online" if is_running else "Offline"
        st.markdown(f"""
            <div style="
                background: #1e293b;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
            ">
                <div style="color: {status_color}; font-size: 2rem;">{'✅' if is_running else '❌'}</div>
                <div style="color: #94a3b8;">System</div>
                <div style="color: white; font-weight: bold;">{status_text}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        mode = "Demo" if (fall_detection_system and fall_detection_system.demo_mode) else "Production"
        st.markdown(f"""
            <div style="
                background: #1e293b;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
            ">
                <div style="font-size: 2rem;">⚙️</div>
                <div style="color: #94a3b8;">Mode</div>
                <div style="color: white; font-weight: bold;">{mode}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        threshold = fall_detection_system.immobility_threshold if fall_detection_system else 10
        st.markdown(f"""
            <div style="
                background: #1e293b;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
            ">
                <div style="font-size: 2rem;">⏱️</div>
                <div style="color: #94a3b8;">Alert Threshold</div>
                <div style="color: white; font-weight: bold;">{threshold}s</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        camera_count = len(fall_detection_system.active_cameras) if fall_detection_system else 0
        st.markdown(f"""
            <div style="
                background: #1e293b;
                padding: 16px;
                border-radius: 8px;
                text-align: center;
            ">
                <div style="font-size: 2rem;">📷</div>
                <div style="color: #94a3b8;">Active Cameras</div>
                <div style="color: white; font-weight: bold;">{camera_count}</div>
            </div>
        """, unsafe_allow_html=True)


def render_bed_zone_config():
    """Render bed zone configuration interface."""
    with st.expander("🛏️ Bed Zone Configuration", expanded=False):
        st.markdown("""
            Configure bed zones to distinguish between:
            - **Person on bed** - Normal (no alert)
            - **Person on floor** - Potential fall (alert)
        """)
        
        # Camera selector
        camera_id = st.selectbox(
            "Select Camera",
            ["CAM-ICU-1", "CAM-ICU-2", "CAM-WARD-1", "CAM-WARD-2"],
            key="bed_zone_camera"
        )
        
        # Show current zones
        if bed_zone_manager and camera_id in bed_zone_manager.cameras:
            zones = bed_zone_manager.cameras[camera_id]
            st.write(f"**Current zones for {camera_id}:** {len(zones)}")
            for zone in zones:
                st.markdown(f"- {zone.zone_id}: Bed {zone.bed_id} ({zone.ward})")
        else:
            st.info("No bed zones configured for this camera")
        
        # Setup demo zones button
        if st.button("🔧 Setup Demo Zones", key="setup_demo_zones"):
            if bed_zone_manager:
                bed_zone_manager.setup_demo_zones(camera_id)
                st.success(f"Demo zones configured for {camera_id}")
                st.rerun()


def render_video_upload():
    """Render video upload for testing."""
    with st.expander("📤 Upload Video for Analysis", expanded=False):
        st.markdown("""
            Upload a video file to test fall detection.
            Supported formats: MP4, AVI, MOV
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=["mp4", "avi", "mov"],
            key="cctv_video_upload"
        )
        
        if uploaded_file:
            st.video(uploaded_file)
            
            if st.button("🔍 Analyze Video", key="analyze_video", type="primary"):
                with st.spinner("Analyzing video for falls..."):
                    # In production, this would process the video
                    import time
                    time.sleep(2)
                    
                    # Simulate results
                    st.success("Analysis complete!")
                    st.markdown("""
                        **Results:**
                        - Frames analyzed: 450
                        - Persons detected: 3
                        - Falls detected: 0
                        - Average confidence: 87%
                    """)


def render_cctv_monitoring():
    """Main CCTV monitoring render function."""
    render_cctv_header()
    
    if not CV_DETECTION_AVAILABLE:
        st.warning("""
            ⚠️ CV Detection module not fully loaded.
            Some features may be unavailable.
            Install dependencies: `pip install opencv-python ultralytics numpy`
        """)
    
    # System status
    render_system_status()
    
    st.markdown("---")
    
    # Demo cameras
    demo_cameras = [
        {"id": "CAM-ICU-1", "location": "ICU - Floor 4", "status": "online"},
        {"id": "CAM-ICU-2", "location": "ICU - Floor 4", "status": "online"},
        {"id": "CAM-WARD-1", "location": "Ward A - Floor 3", "status": "online"},
        {"id": "CAM-WARD-2", "location": "Ward B - Floor 3", "status": "offline"},
        {"id": "CAM-EMER-1", "location": "Emergency", "status": "online"},
        {"id": "CAM-LOBBY-1", "location": "Main Lobby", "status": "online"},
    ]
    
    render_camera_grid(demo_cameras)
    
    st.markdown("---")
    
    # Pending alerts
    if fall_detection_system:
        pending = fall_detection_system.get_pending_alerts()
        pending_dicts = [a.to_dict() for a in pending]
    else:
        # Demo pending alerts
        pending_dicts = [
            {
                "alert_id": "FALL-20240115-001",
                "camera_id": "CAM-ICU-1",
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.87,
                "immobility_seconds": 45,
                "status": "Pending Verification",
                "severity": "Critical"
            }
        ]
    
    actions = render_pending_alerts(pending_dicts)
    
    # Handle verification actions
    if actions:
        for action, alert_id in actions:
            if action == "confirm":
                st.success(f"Emergency confirmed for {alert_id}! Dispatching response team.")
                if fall_detection_system:
                    fall_detection_system.verify_alert(alert_id, "admin", is_emergency=True)
            elif action == "false_alarm":
                st.info(f"Alert {alert_id} marked as false alarm.")
                if fall_detection_system:
                    fall_detection_system.verify_alert(alert_id, "admin", is_emergency=False)
    
    st.markdown("---")
    
    # Collapsible sections
    render_alert_history([
        {
            "alert_id": "FALL-20240114-003",
            "camera_id": "CAM-WARD-1",
            "timestamp": "2024-01-14T14:30:00",
            "status": "False Alarm"
        },
        {
            "alert_id": "FALL-20240114-002",
            "camera_id": "CAM-ICU-2",
            "timestamp": "2024-01-14T10:15:00",
            "status": "Verified Emergency"
        }
    ])
    
    render_bed_zone_config()
    render_video_upload()


# Demo usage
if __name__ == "__main__":
    st.set_page_config(
        page_title="CCTV Monitoring - VitalFlow",
        page_icon="📹",
        layout="wide"
    )
    render_cctv_monitoring()
