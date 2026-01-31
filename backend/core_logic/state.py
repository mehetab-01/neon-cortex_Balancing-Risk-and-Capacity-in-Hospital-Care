# State Management Module
# Shared state management

class State:
    """Shared state manager"""
    def __init__(self):
        self.patients = {}
        self.beds = {}
        self.staff = {}
