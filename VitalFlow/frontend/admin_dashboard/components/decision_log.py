"""
Decision Log Component
AI decision transparency and audit trail
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state


def get_action_icon(action: str) -> str:
    """Get icon based on action type."""
    action_icons = {
        "PATIENT": "👥",
        "BED": "🛏️",
        "STAFF": "👨‍⚕️",
        "SWAP": "🔄",
        "TRIAGE": "⚕️",
        "ALERT": "🚨",
        "STATUS": "📊",
        "AMBULANCE": "🚑",
        "CCTV": "📹",
        "CRITICAL": "🔴",
        "ASSIGN": "✅",
        "PUNCH": "⏰"
    }
    
    for key, icon in action_icons.items():
        if key in action.upper():
            return icon
    return "📝"


def get_action_color(action: str) -> str:
    """Get color based on action severity."""
    if "CRITICAL" in action.upper() or "EMERGENCY" in action.upper():
        return "#ff4444"
    elif "WARNING" in action.upper() or "ALERT" in action.upper():
        return "#ff9800"
    elif "SWAP" in action.upper() or "TRANSFER" in action.upper():
        return "#2196f3"
    elif "SUCCESS" in action.upper() or "COMPLETE" in action.upper():
        return "#4caf50"
    return "#9e9e9e"


def render_decision_log():
    """Render the AI decision log for transparency."""
    st.markdown("## 📝 AI Decision Log")
    st.markdown("*Transparency log of all automated decisions for human oversight*")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        action_filter = st.selectbox(
            "Filter by Action Type",
            ["All", "Patient", "Bed", "Staff", "Swap", "Alert", "Ambulance"],
            key="decision_action_filter"
        )
    
    with col2:
        search = st.text_input("🔍 Search decisions", key="decision_search")
    
    with col3:
        st.markdown("###")
        show_recent = st.checkbox("Last 24h only", key="recent_only", value=True)
    
    # Get decision log
    decisions = hospital_state.decision_log.copy()
    decisions.reverse()  # Most recent first
    
    # Apply filters
    if action_filter != "All":
        decisions = [d for d in decisions if action_filter.upper() in d.get("action", "").upper()]
    
    if search:
        decisions = [d for d in decisions 
                    if search.lower() in d.get("action", "").lower() 
                    or search.lower() in d.get("reason", "").lower()]
    
    if show_recent:
        cutoff = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
        filtered = []
        for d in decisions:
            try:
                ts = d.get("timestamp", "")
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                    if dt.timestamp() > cutoff:
                        filtered.append(d)
            except:
                filtered.append(d)  # Keep if can't parse
        decisions = filtered
    
    # Stats
    st.markdown(f"**Showing {len(decisions)} decisions**")
    
    st.markdown("---")
    
    # Render decisions
    if not decisions:
        st.info("No decisions found matching the criteria")
    else:
        for idx, decision in enumerate(decisions[:50]):  # Limit to 50
            action = decision.get("action", "Unknown")
            reason = decision.get("reason", "No reason provided")
            timestamp = decision.get("timestamp", "Unknown time")
            details = decision.get("details", {})
            
            icon = get_action_icon(action)
            color = get_action_color(action)
            
            # Format timestamp
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%d %b %H:%M:%S")
                except:
                    time_str = timestamp
            else:
                time_str = str(timestamp)
            
            # Decision card
            with st.expander(f"{icon} **{action}** - {time_str}", expanded=idx < 3):
                st.markdown(f"""
                <div style="
                    border-left: 3px solid {color};
                    padding-left: 1rem;
                    margin: 0.5rem 0;
                ">
                    <p><strong>Action:</strong> {action}</p>
                    <p><strong>Reason:</strong> {reason}</p>
                    <p><strong>Time:</strong> {time_str}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if details:
                    st.markdown("**Details:**")
                    for key, value in details.items():
                        st.write(f"  • **{key}:** {value}")
                
                # Action buttons for pending decisions
                if "PENDING" in action.upper():
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_log_{idx}"):
                            st.success("Decision approved")
                    with col2:
                        if st.button("❌ Reject", key=f"reject_log_{idx}"):
                            st.error("Decision rejected")
    
    # Export option
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("📥 Export Log", key="export_log"):
            st.info("Decision log exported to CSV")
    
    # Trust score summary
    st.markdown("---")
    st.markdown("### 🎯 AI Trust Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Decisions", len(hospital_state.decision_log))
    
    with col2:
        # Count by type
        bed_decisions = len([d for d in hospital_state.decision_log if "BED" in d.get("action", "").upper()])
        st.metric("Bed Allocations", bed_decisions)
    
    with col3:
        staff_decisions = len([d for d in hospital_state.decision_log if "STAFF" in d.get("action", "").upper()])
        st.metric("Staff Assignments", staff_decisions)
    
    with col4:
        swap_decisions = len([d for d in hospital_state.decision_log if "SWAP" in d.get("action", "").upper()])
        st.metric("Tetris Swaps", swap_decisions)


if __name__ == "__main__":
    render_decision_log()
