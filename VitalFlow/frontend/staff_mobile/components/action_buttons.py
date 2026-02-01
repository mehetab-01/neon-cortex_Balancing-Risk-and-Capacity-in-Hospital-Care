"""
Action Buttons Component
Reusable action buttons for staff mobile app
Emergency buttons, quick actions, confirmations
"""
import streamlit as st
from typing import Callable, Optional, List, Dict
from enum import Enum


class ActionType(str, Enum):
    """Types of actions."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    SUCCESS = "success"
    WARNING = "warning"


# Action type styling
ACTION_STYLES = {
    ActionType.PRIMARY: {
        "bg": "#2563eb",
        "hover": "#1d4ed8",
        "text": "white"
    },
    ActionType.SECONDARY: {
        "bg": "#475569",
        "hover": "#334155",
        "text": "white"
    },
    ActionType.DANGER: {
        "bg": "#dc2626",
        "hover": "#b91c1c",
        "text": "white"
    },
    ActionType.SUCCESS: {
        "bg": "#16a34a",
        "hover": "#15803d",
        "text": "white"
    },
    ActionType.WARNING: {
        "bg": "#d97706",
        "hover": "#b45309",
        "text": "white"
    },
}


def render_action_button(
    label: str,
    action_type: ActionType = ActionType.PRIMARY,
    icon: str = "",
    disabled: bool = False,
    key: str = "",
    use_container_width: bool = True
) -> bool:
    """
    Render a styled action button.
    
    Returns:
        True if button was clicked
    """
    button_label = f"{icon} {label}" if icon else label
    
    if action_type == ActionType.PRIMARY:
        return st.button(button_label, key=key, use_container_width=use_container_width, type="primary", disabled=disabled)
    else:
        return st.button(button_label, key=key, use_container_width=use_container_width, disabled=disabled)


def render_emergency_button(
    label: str = "🚨 EMERGENCY",
    confirmation_message: str = "Are you sure you want to trigger an emergency alert?",
    key: str = "emergency_btn"
) -> bool:
    """
    Render a large emergency button with confirmation.
    
    Returns:
        True if emergency was confirmed
    """
    # Emergency button styling
    st.markdown("""
        <style>
        .emergency-btn {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: white;
            padding: 20px 40px;
            border-radius: 12px;
            font-size: 1.5rem;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
            border: 2px solid #fca5a5;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
            100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Use dialog for confirmation
    if f"{key}_triggered" not in st.session_state:
        st.session_state[f"{key}_triggered"] = False
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(label, key=key, use_container_width=True, type="primary"):
            st.session_state[f"{key}_triggered"] = True
    
    if st.session_state[f"{key}_triggered"]:
        st.warning(confirmation_message)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Confirm Emergency", key=f"{key}_confirm", type="primary", use_container_width=True):
                st.session_state[f"{key}_triggered"] = False
                return True
        with col_b:
            if st.button("❌ Cancel", key=f"{key}_cancel", use_container_width=True):
                st.session_state[f"{key}_triggered"] = False
    
    return False


def render_quick_actions(
    actions: List[Dict],
    columns: int = 2,
    key_prefix: str = "quick_action"
) -> Optional[str]:
    """
    Render a grid of quick action buttons.
    
    Args:
        actions: List of action configs with keys: id, label, icon, type
        columns: Number of columns
        key_prefix: Prefix for button keys
        
    Returns:
        ID of clicked action or None
    """
    clicked_action = None
    
    cols = st.columns(columns)
    
    for idx, action in enumerate(actions):
        with cols[idx % columns]:
            action_id = action.get("id", str(idx))
            label = action.get("label", "Action")
            icon = action.get("icon", "")
            action_type = action.get("type", ActionType.SECONDARY)
            disabled = action.get("disabled", False)
            
            if render_action_button(
                label=label,
                action_type=action_type,
                icon=icon,
                disabled=disabled,
                key=f"{key_prefix}_{action_id}"
            ):
                clicked_action = action_id
    
    return clicked_action


def render_punch_button(
    is_punched_in: bool,
    on_punch: Optional[Callable[[bool], None]] = None,
    key: str = "punch_btn"
) -> bool:
    """
    Render a punch in/out button.
    
    Args:
        is_punched_in: Current punch status
        on_punch: Callback with new status
        key: Button key
        
    Returns:
        New punch status if changed, else current status
    """
    if is_punched_in:
        label = "🔴 Punch Out"
        style = ActionType.DANGER
    else:
        label = "🟢 Punch In"
        style = ActionType.SUCCESS
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if render_action_button(label, action_type=style, key=key):
            new_status = not is_punched_in
            if on_punch:
                on_punch(new_status)
            return new_status
    
    return is_punched_in


def render_confirmation_dialog(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    key: str = "confirm_dialog"
) -> Optional[bool]:
    """
    Render a confirmation dialog.
    
    Returns:
        True if confirmed, False if cancelled, None if pending
    """
    st.markdown(f"""
        <div style="
            background: #1e293b;
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
        ">
            <h4 style="color: white; margin: 0 0 8px 0;">{title}</h4>
            <p style="color: #94a3b8; margin: 0 0 16px 0;">{message}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"✅ {confirm_label}", key=f"{key}_confirm", type="primary", use_container_width=True):
            return True
    
    with col2:
        if st.button(f"❌ {cancel_label}", key=f"{key}_cancel", use_container_width=True):
            return False
    
    return None


def render_approval_buttons(
    item_id: str,
    item_label: str,
    on_approve: Optional[Callable[[str], None]] = None,
    on_reject: Optional[Callable[[str, str], None]] = None,
    require_reason_on_reject: bool = True,
    key_prefix: str = "approval"
) -> Optional[str]:
    """
    Render approve/reject buttons with optional rejection reason.
    
    Returns:
        'approved', 'rejected', or None if pending
    """
    st.markdown(f"**{item_label}**")
    
    # Check for rejection in progress
    reject_key = f"{key_prefix}_{item_id}_rejecting"
    if reject_key not in st.session_state:
        st.session_state[reject_key] = False
    
    if st.session_state[reject_key]:
        # Show rejection reason input
        reason = st.text_input(
            "Rejection reason:", 
            key=f"{key_prefix}_{item_id}_reason",
            placeholder="Enter reason for rejection..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Rejection", key=f"{key_prefix}_{item_id}_confirm_reject", use_container_width=True):
                st.session_state[reject_key] = False
                if on_reject:
                    on_reject(item_id, reason)
                return "rejected"
        with col2:
            if st.button("Cancel", key=f"{key_prefix}_{item_id}_cancel_reject", use_container_width=True):
                st.session_state[reject_key] = False
        return None
    
    # Show approve/reject buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve", key=f"{key_prefix}_{item_id}_approve", type="primary", use_container_width=True):
            if on_approve:
                on_approve(item_id)
            return "approved"
    
    with col2:
        if st.button("❌ Reject", key=f"{key_prefix}_{item_id}_reject", use_container_width=True):
            if require_reason_on_reject:
                st.session_state[reject_key] = True
            else:
                if on_reject:
                    on_reject(item_id, "")
                return "rejected"
    
    return None


# Demo usage
if __name__ == "__main__":
    st.set_page_config(page_title="Action Buttons Demo", layout="wide")
    st.title("Action Buttons Component Demo")
    
    st.subheader("1. Standard Action Buttons")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_action_button("Primary", ActionType.PRIMARY, "🔵", key="demo_primary")
    with col2:
        render_action_button("Secondary", ActionType.SECONDARY, "⚪", key="demo_secondary")
    with col3:
        render_action_button("Success", ActionType.SUCCESS, "🟢", key="demo_success")
    with col4:
        render_action_button("Warning", ActionType.WARNING, "🟡", key="demo_warning")
    with col5:
        render_action_button("Danger", ActionType.DANGER, "🔴", key="demo_danger")
    
    st.markdown("---")
    st.subheader("2. Emergency Button")
    
    if render_emergency_button():
        st.success("🚨 Emergency alert triggered!")
    
    st.markdown("---")
    st.subheader("3. Punch In/Out")
    
    if "demo_punched_in" not in st.session_state:
        st.session_state.demo_punched_in = False
    
    new_status = render_punch_button(
        is_punched_in=st.session_state.demo_punched_in,
        key="demo_punch"
    )
    st.session_state.demo_punched_in = new_status
    
    st.markdown("---")
    st.subheader("4. Quick Actions Grid")
    
    quick_actions = [
        {"id": "vitals", "label": "Record Vitals", "icon": "📊", "type": ActionType.PRIMARY},
        {"id": "medication", "label": "Give Medication", "icon": "💊", "type": ActionType.PRIMARY},
        {"id": "notes", "label": "Add Notes", "icon": "📝", "type": ActionType.SECONDARY},
        {"id": "alert", "label": "Call Doctor", "icon": "📞", "type": ActionType.WARNING},
    ]
    
    clicked = render_quick_actions(quick_actions, key_prefix="demo_quick")
    if clicked:
        st.info(f"Clicked: {clicked}")
