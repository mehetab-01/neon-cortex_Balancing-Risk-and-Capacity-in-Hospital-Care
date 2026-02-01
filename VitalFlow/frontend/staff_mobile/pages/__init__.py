"""
Staff Mobile Pages Package
Role-specific views for different staff types
"""
from .doctor_view import render_doctor_view
from .nurse_view import render_nurse_view
from .wardboy_view import render_wardboy_view
from .driver_view import render_driver_view
from .patient_view import render_patient_view
