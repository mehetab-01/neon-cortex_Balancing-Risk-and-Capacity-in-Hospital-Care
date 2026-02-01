"""
Shared module initialization.
"""
from .models import (
    Patient,
    Bed,
    Staff,
    Ambulance,
    Hospital,
    PatientStatus,
    BedType,
    StaffRole,
    StaffStatus,
    DecisionLogEntry
)

from .constants import (
    VitalThresholds,
    StaffConfig,
    TriagePriority,
    PRIORITY_COLORS,
    STATUS_COLORS,
    BED_TYPE_COLORS,
    BED_DISTRIBUTION,
    WARD_NAMES
)

__all__ = [
    "Patient",
    "Bed",
    "Staff",
    "Ambulance",
    "Hospital",
    "PatientStatus",
    "BedType",
    "StaffRole",
    "StaffStatus",
    "DecisionLogEntry",
    "VitalThresholds",
    "StaffConfig",
    "TriagePriority",
    "PRIORITY_COLORS",
    "STATUS_COLORS",
    "BED_TYPE_COLORS",
    "BED_DISTRIBUTION",
    "WARD_NAMES"
]
