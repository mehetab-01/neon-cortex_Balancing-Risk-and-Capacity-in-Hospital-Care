"""
VitalFlow AI - Decision Log Component
AI decision explanations and history log
"""

import streamlit as st
from typing import Dict, List, Any
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


# Severity colors and icons
SEVERITY_CONFIG = {
    "CRITICAL": {"color": "#FF4B4B", "icon": "🚨", "bg": "#FF4B4B20"},
    "WARNING": {"color": "#FFA500", "icon": "⚠️", "bg": "#FFA50020"},
    "INFO": {"color": "#4DA6FF", "icon": "ℹ️", "bg": "#4DA6FF20"},
    "SUCCESS": {"color": "#00CC66", "icon": "✅", "bg": "#00CC6620"},
}

# Action type icons
ACTION_ICONS = {
    "BED_SWAP": "🔄",
    "ALERT": "🚨",
    "STAFF_ASSIGN": "👨‍⚕️",
    "DISCHARGE_RECOMMEND": "🏠",
    "ICU_TRANSFER": "🏥",
    "MEDICATION": "💊",
    "TEST_ORDER": "🧪",
    "VITAL_ALERT": "❤️",
}


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        dt = timestamp
    
    return dt.strftime("%H:%M")


def format_timestamp_full(timestamp: str) -> str:
    """Format timestamp with date"""
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        dt = timestamp
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def render_decision_item(decision: Dict, show_full: bool = False):
    """
    Render a single decision log item
    """
    severity = decision.get('severity', 'INFO')
    config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['INFO'])
    action = decision.get('action', 'UNKNOWN')
    action_icon = ACTION_ICONS.get(action, "📋")
    
    timestamp = format_timestamp(decision.get('timestamp', datetime.now().isoformat()))
    
    st.markdown(
        f"""
        <div style="
            background: {config['bg']};
            border-left: 3px solid {config['color']};
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 8px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <span style="color: #888; font-size: 12px;">[{timestamp}]</span>
                    <span style="color: {config['color']}; font-weight: bold;"> {action_icon} {action}</span>
                </div>
                <span style="font-size: 16px;">{config['icon']}</span>
            </div>
            <p style="margin: 5px 0 0 0; color: #DDD; font-size: 14px;">
                {decision.get('reason', 'No details available')}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if show_full:
        with st.expander("Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Decision ID:** {decision.get('id', 'N/A')}")
                st.markdown(f"**Timestamp:** {format_timestamp_full(decision.get('timestamp', ''))}")
            with col2:
                st.markdown(f"**Patient ID:** {decision.get('patient_id', 'N/A')}")
                st.markdown(f"**Severity:** {severity}")


def render_decision_log(decisions: List[Dict], max_items: int = 10, 
                        filter_severity: str = None, filter_action: str = None):
    """
    Render the scrollable decision log
    """
    st.markdown("### 🤖 AI Decision Log")
    
    # Filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        severity_options = ["All", "CRITICAL", "WARNING", "INFO"]
        selected_severity = st.selectbox("Severity", severity_options, key="log_severity")
    
    with col2:
        action_options = ["All"] + list(ACTION_ICONS.keys())
        selected_action = st.selectbox("Action Type", action_options, key="log_action")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="refresh_log"):
            st.rerun()
    
    # Filter decisions
    filtered = decisions
    
    if selected_severity != "All":
        filtered = [d for d in filtered if d.get('severity') == selected_severity]
    
    if selected_action != "All":
        filtered = [d for d in filtered if d.get('action') == selected_action]
    
    # Limit items
    filtered = filtered[:max_items]
    
    st.divider()
    
    # Stats bar
    total = len(decisions)
    critical_count = sum(1 for d in decisions if d.get('severity') == 'CRITICAL')
    warning_count = sum(1 for d in decisions if d.get('severity') == 'WARNING')
    
    if critical_count > 0:
        st.error(f"🚨 {critical_count} critical decisions in the last hour")
    
    # Log container
    if not filtered:
        st.info("No decisions matching the criteria")
        return
    
    # Render each decision
    for decision in filtered:
        render_decision_item(decision)


def render_decision_log_compact(decisions: List[Dict], max_items: int = 5):
    """
    Render a compact version of the decision log for sidebar
    """
    st.markdown("### 🤖 Recent AI Decisions")
    
    # Show only recent critical/warning decisions
    important = [d for d in decisions if d.get('severity') in ['CRITICAL', 'WARNING']][:max_items]
    
    if not important:
        important = decisions[:max_items]
    
    for decision in important:
        severity = decision.get('severity', 'INFO')
        config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['INFO'])
        timestamp = format_timestamp(decision.get('timestamp', ''))
        
        # Truncate reason
        reason = decision.get('reason', '')
        if len(reason) > 80:
            reason = reason[:80] + "..."
        
        st.markdown(
            f"""
            <div style="
                background: {config['bg']};
                border-left: 2px solid {config['color']};
                padding: 8px;
                margin-bottom: 5px;
                border-radius: 3px;
                font-size: 12px;
            ">
                <span style="color: #888;">[{timestamp}]</span>
                <span style="color: {config['color']};">{config['icon']}</span>
                <br>
                <span style="color: #CCC;">{reason}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    if len(decisions) > max_items:
        st.markdown(f"<p style='color: #888; font-size: 12px; text-align: center;'>+{len(decisions) - max_items} more decisions</p>", unsafe_allow_html=True)


def render_decision_timeline(decisions: List[Dict]):
    """
    Render decisions as a visual timeline
    """
    st.markdown("### 📅 Decision Timeline")
    
    # Group by hour
    from collections import defaultdict
    hourly = defaultdict(list)
    
    for d in decisions:
        timestamp = d.get('timestamp', '')
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        hour_key = dt.strftime("%H:00")
        hourly[hour_key].append(d)
    
    # Render timeline
    for hour, hour_decisions in sorted(hourly.items(), reverse=True):
        critical = sum(1 for d in hour_decisions if d.get('severity') == 'CRITICAL')
        warning = sum(1 for d in hour_decisions if d.get('severity') == 'WARNING')
        info = sum(1 for d in hour_decisions if d.get('severity') == 'INFO')
        
        with st.expander(f"🕐 {hour} - {len(hour_decisions)} decisions ({critical} critical, {warning} warnings)"):
            for d in hour_decisions:
                render_decision_item(d)


def render_decision_stats(decisions: List[Dict]):
    """
    Render statistics about AI decisions
    """
    st.markdown("### 📊 Decision Statistics")
    
    total = len(decisions)
    
    # Count by severity
    severity_counts = {
        "CRITICAL": sum(1 for d in decisions if d.get('severity') == 'CRITICAL'),
        "WARNING": sum(1 for d in decisions if d.get('severity') == 'WARNING'),
        "INFO": sum(1 for d in decisions if d.get('severity') == 'INFO'),
    }
    
    # Count by action
    action_counts = {}
    for d in decisions:
        action = d.get('action', 'UNKNOWN')
        action_counts[action] = action_counts.get(action, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Decisions", total)
    with col2:
        st.metric("🚨 Critical", severity_counts["CRITICAL"])
    with col3:
        st.metric("⚠️ Warnings", severity_counts["WARNING"])
    with col4:
        st.metric("ℹ️ Info", severity_counts["INFO"])
    
    st.divider()
    
    # Action breakdown
    st.markdown("**Actions Breakdown:**")
    
    cols = st.columns(len(action_counts))
    for i, (action, count) in enumerate(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)):
        icon = ACTION_ICONS.get(action, "📋")
        with cols[i % len(cols)]:
            st.markdown(f"{icon} **{action}**: {count}")


def render_ai_explanation_panel(decision: Dict = None):
    """
    Render detailed AI explanation for a specific decision
    """
    st.markdown("### 🧠 AI Decision Explanation")
    
    if not decision:
        st.info("Select a decision from the log to see detailed explanation")
        return
    
    severity = decision.get('severity', 'INFO')
    config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['INFO'])
    
    st.markdown(
        f"""
        <div style="
            background: {config['bg']};
            border: 1px solid {config['color']};
            border-radius: 10px;
            padding: 20px;
        ">
            <h3 style="color: {config['color']}; margin: 0;">
                {config['icon']} {decision.get('action', 'Unknown Action')}
            </h3>
            <p style="color: #888; margin: 5px 0;">
                {format_timestamp_full(decision.get('timestamp', ''))}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("#### 📝 What happened?")
    st.write(decision.get('reason', 'No details available'))
    
    st.markdown("#### 🎯 Why this decision?")
    st.write("""
    The AI analyzed the following factors:
    - Patient vital signs and trends
    - Current bed availability and type requirements  
    - Staff assignments and workload
    - Hospital capacity constraints
    - Historical patterns for similar cases
    """)
    
    st.markdown("#### 📊 Confidence Level")
    confidence = 0.85  # Mock confidence
    st.progress(confidence, text=f"{confidence*100:.0f}% confidence")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("✅ Approve", type="primary", use_container_width=True)
    with col2:
        st.button("❌ Override", use_container_width=True)
