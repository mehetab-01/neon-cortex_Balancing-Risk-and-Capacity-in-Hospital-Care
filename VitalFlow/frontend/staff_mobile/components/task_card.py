"""
Task Card Component
Reusable task card for staff mobile app
Displays tasks with priority, status, and action buttons
"""
import streamlit as st
from typing import Dict, Optional, Callable
from datetime import datetime
from enum import Enum


class TaskPriority(str, Enum):
    """Task priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Priority colors
PRIORITY_COLORS = {
    TaskPriority.URGENT: "#dc2626",  # Red
    TaskPriority.HIGH: "#ea580c",    # Orange
    TaskPriority.NORMAL: "#2563eb",  # Blue
    TaskPriority.LOW: "#6b7280",     # Gray
}

PRIORITY_ICONS = {
    TaskPriority.URGENT: "🚨",
    TaskPriority.HIGH: "⚠️",
    TaskPriority.NORMAL: "📋",
    TaskPriority.LOW: "📝",
}

STATUS_ICONS = {
    TaskStatus.PENDING: "⏳",
    TaskStatus.IN_PROGRESS: "🔄",
    TaskStatus.COMPLETED: "✅",
    TaskStatus.CANCELLED: "❌",
}


def render_task_card(
    task_id: str,
    title: str,
    description: str,
    priority: TaskPriority = TaskPriority.NORMAL,
    status: TaskStatus = TaskStatus.PENDING,
    assigned_by: Optional[str] = None,
    due_time: Optional[datetime] = None,
    location: Optional[str] = None,
    patient_name: Optional[str] = None,
    on_start: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    expandable: bool = True,
    key_prefix: str = ""
):
    """
    Render a task card component.
    
    Args:
        task_id: Unique task identifier
        title: Task title
        description: Task description
        priority: Task priority level
        status: Current task status
        assigned_by: Who assigned the task
        due_time: When task is due
        location: Where the task should be performed
        patient_name: Patient associated with task
        on_start: Callback when task is started
        on_complete: Callback when task is completed
        on_cancel: Callback when task is cancelled
        expandable: Whether the card can be expanded
        key_prefix: Prefix for Streamlit keys
    """
    priority_color = PRIORITY_COLORS.get(priority, PRIORITY_COLORS[TaskPriority.NORMAL])
    priority_icon = PRIORITY_ICONS.get(priority, "📋")
    status_icon = STATUS_ICONS.get(status, "⏳")
    
    # Card container with left border color based on priority
    card_style = f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-left: 4px solid {priority_color};
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">{priority_icon}</span>
                    <span style="font-weight: bold; color: white; font-size: 1.1rem;">{title}</span>
                </div>
                <span style="
                    background: {priority_color}33;
                    color: {priority_color};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">{priority.value.upper()}</span>
            </div>
            <p style="color: #94a3b8; margin: 8px 0; font-size: 0.9rem;">{description}</p>
        </div>
    """
    
    st.markdown(card_style, unsafe_allow_html=True)
    
    # Details section
    col1, col2 = st.columns(2)
    
    with col1:
        if patient_name:
            st.markdown(f"👤 **Patient:** {patient_name}")
        if location:
            st.markdown(f"📍 **Location:** {location}")
    
    with col2:
        if assigned_by:
            st.markdown(f"📌 **Assigned by:** {assigned_by}")
        if due_time:
            time_str = due_time.strftime("%I:%M %p")
            st.markdown(f"⏰ **Due:** {time_str}")
    
    # Status badge
    st.markdown(f"{status_icon} **Status:** {status.value.replace('_', ' ').title()}")
    
    # Action buttons based on status
    if status == TaskStatus.PENDING:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶️ Start Task", key=f"{key_prefix}_start_{task_id}", use_container_width=True):
                if on_start:
                    on_start(task_id)
        with col_b:
            if st.button("❌ Cancel", key=f"{key_prefix}_cancel_{task_id}", use_container_width=True):
                if on_cancel:
                    on_cancel(task_id)
    
    elif status == TaskStatus.IN_PROGRESS:
        if st.button("✅ Mark Complete", key=f"{key_prefix}_complete_{task_id}", use_container_width=True, type="primary"):
            if on_complete:
                on_complete(task_id)
    
    st.markdown("---")


def render_task_list(
    tasks: list[Dict],
    on_start: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    filter_status: Optional[TaskStatus] = None,
    filter_priority: Optional[TaskPriority] = None,
    show_completed: bool = False
):
    """
    Render a list of task cards.
    
    Args:
        tasks: List of task dictionaries
        on_start: Callback when task is started
        on_complete: Callback when task is completed
        on_cancel: Callback when task is cancelled
        filter_status: Only show tasks with this status
        filter_priority: Only show tasks with this priority
        show_completed: Whether to show completed tasks
    """
    if not tasks:
        st.info("No tasks to display")
        return
    
    # Apply filters
    filtered_tasks = tasks
    
    if filter_status:
        filtered_tasks = [t for t in filtered_tasks if t.get("status") == filter_status]
    
    if filter_priority:
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == filter_priority]
    
    if not show_completed:
        filtered_tasks = [t for t in filtered_tasks if t.get("status") != TaskStatus.COMPLETED]
    
    # Sort by priority (urgent first)
    priority_order = {
        TaskPriority.URGENT: 0,
        TaskPriority.HIGH: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.LOW: 3
    }
    
    filtered_tasks.sort(key=lambda x: priority_order.get(x.get("priority", TaskPriority.NORMAL), 2))
    
    # Render each task
    for idx, task in enumerate(filtered_tasks):
        render_task_card(
            task_id=task.get("task_id", str(idx)),
            title=task.get("title", "Untitled Task"),
            description=task.get("description", ""),
            priority=task.get("priority", TaskPriority.NORMAL),
            status=task.get("status", TaskStatus.PENDING),
            assigned_by=task.get("assigned_by"),
            due_time=task.get("due_time"),
            location=task.get("location"),
            patient_name=task.get("patient_name"),
            on_start=on_start,
            on_complete=on_complete,
            on_cancel=on_cancel,
            key_prefix=f"task_{idx}"
        )


def render_task_summary(tasks: list[Dict]):
    """
    Render a summary of task counts by status.
    """
    # Count tasks by status
    pending = sum(1 for t in tasks if t.get("status") == TaskStatus.PENDING)
    in_progress = sum(1 for t in tasks if t.get("status") == TaskStatus.IN_PROGRESS)
    completed = sum(1 for t in tasks if t.get("status") == TaskStatus.COMPLETED)
    
    # Count urgent tasks
    urgent = sum(1 for t in tasks if t.get("priority") == TaskPriority.URGENT)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏳ Pending", pending)
    with col2:
        st.metric("🔄 In Progress", in_progress)
    with col3:
        st.metric("✅ Completed", completed)
    with col4:
        st.metric("🚨 Urgent", urgent, delta=None if urgent == 0 else "Priority!")


# Demo usage
if __name__ == "__main__":
    st.set_page_config(page_title="Task Card Demo", layout="wide")
    st.title("Task Card Component Demo")
    
    # Sample tasks
    sample_tasks = [
        {
            "task_id": "T001",
            "title": "Administer Medication",
            "description": "Give Paracetamol 500mg to patient in Room 204",
            "priority": TaskPriority.URGENT,
            "status": TaskStatus.PENDING,
            "assigned_by": "Dr. Sharma",
            "due_time": datetime.now(),
            "location": "Room 204",
            "patient_name": "Ramesh Kumar"
        },
        {
            "task_id": "T002",
            "title": "Check Vitals",
            "description": "Routine vital signs check for post-operative patient",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.IN_PROGRESS,
            "location": "ICU Bed 3",
            "patient_name": "Sunita Devi"
        },
        {
            "task_id": "T003",
            "title": "Change IV Fluid",
            "description": "Replace saline drip",
            "priority": TaskPriority.NORMAL,
            "status": TaskStatus.PENDING,
            "location": "Room 301",
            "patient_name": "Anil Verma"
        }
    ]
    
    render_task_summary(sample_tasks)
    st.markdown("---")
    render_task_list(sample_tasks)
