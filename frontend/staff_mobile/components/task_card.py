"""
VitalFlow AI - Task Card Component
Mobile-optimized task cards for staff views
"""
import streamlit as st
from datetime import datetime
from typing import Callable, Optional


def render_task_card(
    task_id: str,
    description: str,
    patient_name: str = None,
    bed_id: str = None,
    scheduled_time: str = None,
    is_urgent: bool = False,
    is_completed: bool = False,
    on_complete: Callable = None,
    show_checkbox: bool = True
):
    """
    Render a mobile-optimized task card
    
    Args:
        task_id: Unique task identifier
        description: Task description
        patient_name: Patient name (optional)
        bed_id: Bed ID (optional)
        scheduled_time: Scheduled time string (optional)
        is_urgent: Whether task is urgent
        is_completed: Whether task is completed
        on_complete: Callback when task is marked complete
        show_checkbox: Whether to show checkbox
    """
    urgent_badge = "🔴 URGENT" if is_urgent else ""
    status_color = "#00C851" if is_completed else "#FF6B6B" if is_urgent else "#33B5E5"
    bg_color = "#1a3a1a" if is_completed else "#3a1a1a" if is_urgent else "#1a1a2e"
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {status_color};
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #fff; font-size: 14px; font-weight: 500;">
                {description}
            </span>
            <span style="color: {status_color}; font-size: 12px;">{urgent_badge}</span>
        </div>
        <div style="margin-top: 8px; color: #888; font-size: 12px;">
            {f"👤 {patient_name}" if patient_name else ""} 
            {f"🛏️ {bed_id}" if bed_id else ""}
            {f"⏰ {scheduled_time}" if scheduled_time else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if show_checkbox and not is_completed:
        if st.checkbox("Mark Complete", key=f"task_{task_id}", value=is_completed):
            if on_complete:
                on_complete(task_id)
            return True
    
    return is_completed


def render_transfer_card(
    transfer_id: str,
    patient_name: str,
    from_bed: str,
    to_bed: str,
    urgency: str = "Medium",
    reason: str = None,
    on_complete: Callable = None,
    on_approve: Callable = None,
    on_decline: Callable = None,
    show_approval_buttons: bool = False,
    show_complete_button: bool = True
):
    """
    Render a transfer request card
    
    Args:
        transfer_id: Transfer request ID
        patient_name: Patient name
        from_bed: Source bed/ward
        to_bed: Destination bed/ward
        urgency: Urgency level
        reason: Transfer reason
        on_complete: Callback for completion
        on_approve: Callback for approval
        on_decline: Callback for decline
        show_approval_buttons: Show approve/decline buttons
        show_complete_button: Show mark complete button
    """
    urgency_colors = {
        "Critical": "#FF4444",
        "High": "#FF8800",
        "Medium": "#FFBB33",
        "Low": "#00C851"
    }
    
    color = urgency_colors.get(urgency, "#33B5E5")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid {color}40;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <span style="color: #fff; font-size: 18px; font-weight: 600;">👤 {patient_name}</span>
            <span style="
                background: {color}30;
                color: {color};
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            ">{urgency}</span>
        </div>
        
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            padding: 15px;
            background: #0d0d1a;
            border-radius: 10px;
        ">
            <div style="text-align: center;">
                <div style="color: #FF6B6B; font-size: 14px;">FROM</div>
                <div style="color: #fff; font-size: 16px; font-weight: 500;">{from_bed}</div>
            </div>
            <div style="margin: 0 20px; color: #6C63FF; font-size: 24px;">→</div>
            <div style="text-align: center;">
                <div style="color: #00C851; font-size: 14px;">TO</div>
                <div style="color: #fff; font-size: 16px; font-weight: 500;">{to_bed}</div>
            </div>
        </div>
        
        {f'<div style="color: #888; font-size: 13px; margin-top: 10px;">📋 {reason}</div>' if reason else ''}
    </div>
    """, unsafe_allow_html=True)
    
    if show_approval_buttons:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{transfer_id}", use_container_width=True):
                if on_approve:
                    on_approve(transfer_id)
                return "approved"
        with col2:
            if st.button("❌ Decline", key=f"decline_{transfer_id}", use_container_width=True):
                if on_decline:
                    on_decline(transfer_id)
                return "declined"
    
    if show_complete_button:
        if st.button("✅ Mark Complete", key=f"complete_{transfer_id}", use_container_width=True):
            if on_complete:
                on_complete(transfer_id)
            return "completed"
    
    return None


def render_alert_card(
    alert_id: str,
    message: str,
    alert_type: str,
    priority: str = "Medium",
    is_voice_alert: bool = False,
    timestamp: str = None,
    on_acknowledge: Callable = None,
    on_play_voice: Callable = None
):
    """
    Render an alert card
    
    Args:
        alert_id: Alert ID
        message: Alert message
        alert_type: Type of alert
        priority: Priority level
        is_voice_alert: Whether it has voice
        timestamp: When alert was created
        on_acknowledge: Callback for acknowledgment
        on_play_voice: Callback for playing voice
    """
    priority_colors = {
        "Critical": "#FF4444",
        "High": "#FF8800",
        "Medium": "#FFBB33",
        "Low": "#00C851"
    }
    
    color = priority_colors.get(priority, "#33B5E5")
    icon = "🚨" if priority == "Critical" else "⚠️" if priority == "High" else "ℹ️"
    
    st.markdown(f"""
    <div style="
        background: {color}15;
        border: 2px solid {color};
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        animation: pulse 2s infinite;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">{icon}</span>
            <div style="flex: 1;">
                <div style="color: #fff; font-size: 15px; font-weight: 500;">{message}</div>
                <div style="color: #888; font-size: 11px; margin-top: 4px;">
                    {timestamp if timestamp else "Just now"} • {alert_type}
                </div>
            </div>
            {f'<span style="font-size: 20px;">🔊</span>' if is_voice_alert else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if is_voice_alert:
            if st.button("🔊 Play", key=f"play_{alert_id}", use_container_width=True):
                if on_play_voice:
                    on_play_voice(alert_id)
    with col2:
        if st.button("✓ Acknowledge", key=f"ack_{alert_id}", use_container_width=True):
            if on_acknowledge:
                on_acknowledge(alert_id)
