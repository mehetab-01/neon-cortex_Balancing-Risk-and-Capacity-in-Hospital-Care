"""
Core Logic Engine initialization.
Exports all managers and engines for easy importing.
"""
from .state import hospital_state, HospitalState
from .bed_manager import bed_manager, BedManager
from .staff_manager import staff_manager, StaffManager
from .triage_engine import triage_engine, TriageEngine

__all__ = [
    "hospital_state",
    "HospitalState",
    "bed_manager",
    "BedManager",
    "staff_manager",
    "StaffManager",
    "triage_engine",
    "TriageEngine"
]
