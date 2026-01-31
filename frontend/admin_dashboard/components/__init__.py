"""
VitalFlow AI - Admin Dashboard Components
"""

from .stats_panel import (
    render_stats_panel,
    render_mini_stats,
    render_alerts_summary,
)

from .floor_map import (
    render_floor_map,
    render_bed_grid,
    render_compact_floor_view,
    render_bed_matrix,
)

from .patient_cards import (
    render_patient_card,
    render_patient_list,
    render_critical_patients_panel,
    render_patient_table,
    render_patient_search,
)

from .city_map import (
    render_city_map,
    render_city_map_alternative,
    render_hospital_comparison,
    render_transfer_panel,
)

from .decision_log import (
    render_decision_log,
    render_decision_log_compact,
    render_decision_timeline,
    render_decision_stats,
    render_ai_explanation_panel,
)

__all__ = [
    # Stats Panel
    "render_stats_panel",
    "render_mini_stats",
    "render_alerts_summary",
    # Floor Map
    "render_floor_map",
    "render_bed_grid",
    "render_compact_floor_view",
    "render_bed_matrix",
    # Patient Cards
    "render_patient_card",
    "render_patient_list",
    "render_critical_patients_panel",
    "render_patient_table",
    "render_patient_search",
    # City Map
    "render_city_map",
    "render_city_map_alternative",
    "render_hospital_comparison",
    "render_transfer_panel",
    # Decision Log
    "render_decision_log",
    "render_decision_log_compact",
    "render_decision_timeline",
    "render_decision_stats",
    "render_ai_explanation_panel",
]
