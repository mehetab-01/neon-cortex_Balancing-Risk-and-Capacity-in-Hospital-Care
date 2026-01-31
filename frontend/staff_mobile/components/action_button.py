"""
VitalFlow AI - Action Button Component
Large, touch-friendly action buttons for mobile
"""
import streamlit as st
from typing import Callable, Optional


def render_action_button(
    label: str,
    key: str,
    button_type: str = "primary",
    icon: str = None,
    size: str = "large",
    disabled: bool = False,
    full_width: bool = True,
    on_click: Callable = None
) -> bool:
    """
    Render a mobile-optimized action button
    
    Args:
        label: Button text
        key: Unique key for button
        button_type: "primary", "success", "danger", "warning", "info"
        icon: Emoji icon to prepend
        size: "small", "medium", "large", "xlarge"
        disabled: Whether button is disabled
        full_width: Whether button spans full width
        on_click: Callback function
        
    Returns:
        True if button was clicked
    """
    colors = {
        "primary": {"bg": "#6C63FF", "hover": "#5A52E0"},
        "success": {"bg": "#00C851", "hover": "#00A844"},
        "danger": {"bg": "#FF4444", "hover": "#CC0000"},
        "warning": {"bg": "#FFBB33", "hover": "#FF8800"},
        "info": {"bg": "#33B5E5", "hover": "#0099CC"},
        "dark": {"bg": "#2D2D2D", "hover": "#404040"}
    }
    
    sizes = {
        "small": {"height": "40px", "font": "14px", "padding": "8px 16px"},
        "medium": {"height": "50px", "font": "16px", "padding": "12px 24px"},
        "large": {"height": "60px", "font": "18px", "padding": "15px 30px"},
        "xlarge": {"height": "80px", "font": "22px", "padding": "20px 40px"}
    }
    
    color = colors.get(button_type, colors["primary"])
    size_config = sizes.get(size, sizes["large"])
    
    button_label = f"{icon} {label}" if icon else label
    
    # Custom CSS for this specific button
    st.markdown(f"""
    <style>
        div[data-testid="stButton"] > button[kind="secondary"]:has(p:contains("{label}")) {{
            background: {color['bg']};
            color: white;
            border: none;
            height: {size_config['height']};
            font-size: {size_config['font']};
            font-weight: 600;
            border-radius: 12px;
            width: {'100%' if full_width else 'auto'};
            transition: all 0.3s ease;
        }}
        div[data-testid="stButton"] > button[kind="secondary"]:has(p:contains("{label}")):hover {{
            background: {color['hover']};
            transform: scale(1.02);
        }}
    </style>
    """, unsafe_allow_html=True)
    
    clicked = st.button(
        button_label,
        key=key,
        disabled=disabled,
        use_container_width=full_width
    )
    
    if clicked and on_click:
        on_click()
    
    return clicked


def render_toggle_button(
    label_on: str,
    label_off: str,
    key: str,
    is_on: bool = False,
    icon_on: str = "✅",
    icon_off: str = "⭕",
    on_toggle: Callable = None
) -> bool:
    """
    Render a toggle button that changes state
    
    Args:
        label_on: Label when toggled on
        label_off: Label when toggled off
        key: Unique key
        is_on: Current state
        icon_on: Icon when on
        icon_off: Icon when off
        on_toggle: Callback with new state
        
    Returns:
        New toggle state
    """
    current_label = f"{icon_on} {label_on}" if is_on else f"{icon_off} {label_off}"
    button_type = "success" if is_on else "danger"
    
    color = "#00C851" if is_on else "#FF4444"
    
    st.markdown(f"""
    <style>
        div[data-testid="stButton"] > button[key="{key}"] {{
            background: {color};
            color: white;
            border: none;
            height: 70px;
            font-size: 20px;
            font-weight: 600;
            border-radius: 15px;
            width: 100%;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    if st.button(current_label, key=key, use_container_width=True):
        new_state = not is_on
        if on_toggle:
            on_toggle(new_state)
        return new_state
    
    return is_on


def render_status_button(
    status: str,
    key: str,
    statuses: list = None,
    on_change: Callable = None
) -> str:
    """
    Render a status cycling button
    
    Args:
        status: Current status
        key: Unique key
        statuses: List of possible statuses
        on_change: Callback with new status
        
    Returns:
        Current or new status
    """
    if statuses is None:
        statuses = ["IDLE", "EN_ROUTE", "PATIENT_LOADED", "ARRIVING", "COMPLETED"]
    
    status_config = {
        "IDLE": {"color": "#666", "icon": "⚪", "label": "Ready"},
        "EN_ROUTE": {"color": "#33B5E5", "icon": "🚑", "label": "En Route"},
        "PATIENT_LOADED": {"color": "#FFBB33", "icon": "👤", "label": "Patient Loaded"},
        "ARRIVING": {"color": "#00C851", "icon": "🏥", "label": "Arriving"},
        "COMPLETED": {"color": "#6C63FF", "icon": "✅", "label": "Completed"}
    }
    
    config = status_config.get(status, status_config["IDLE"])
    
    st.markdown(f"""
    <div style="
        background: {config['color']}20;
        border: 2px solid {config['color']};
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    ">
        <div style="font-size: 48px;">{config['icon']}</div>
        <div style="color: {config['color']}; font-size: 24px; font-weight: bold; margin-top: 10px;">
            {config['label']}
        </div>
        <div style="color: #888; font-size: 14px; margin-top: 5px;">
            Status: {status}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Next status button
    current_idx = statuses.index(status) if status in statuses else 0
    if current_idx < len(statuses) - 1:
        next_status = statuses[current_idx + 1]
        next_config = status_config.get(next_status, {})
        
        if st.button(
            f"➡️ Move to: {next_config.get('label', next_status)}",
            key=f"{key}_next",
            use_container_width=True
        ):
            if on_change:
                on_change(next_status)
            return next_status
    
    return status


def render_emergency_button(
    label: str = "🚨 EMERGENCY",
    key: str = "emergency",
    on_click: Callable = None
) -> bool:
    """
    Render a large emergency action button
    
    Args:
        label: Button label
        key: Unique key
        on_click: Callback function
        
    Returns:
        True if clicked
    """
    st.markdown("""
    <style>
        .emergency-btn {
            background: linear-gradient(135deg, #FF4444 0%, #CC0000 100%);
            color: white;
            border: none;
            height: 100px;
            font-size: 24px;
            font-weight: bold;
            border-radius: 20px;
            width: 100%;
            cursor: pointer;
            animation: pulse-emergency 1.5s infinite;
            box-shadow: 0 4px 15px rgba(255, 68, 68, 0.4);
        }
        @keyframes pulse-emergency {
            0% { transform: scale(1); box-shadow: 0 4px 15px rgba(255, 68, 68, 0.4); }
            50% { transform: scale(1.02); box-shadow: 0 6px 20px rgba(255, 68, 68, 0.6); }
            100% { transform: scale(1); box-shadow: 0 4px 15px rgba(255, 68, 68, 0.4); }
        }
    </style>
    """, unsafe_allow_html=True)
    
    clicked = st.button(label, key=key, use_container_width=True)
    
    if clicked and on_click:
        on_click()
    
    return clicked
