"""
Utility functions for VitalFlow AI.
"""

def get_enum_value(enum_val) -> str:
    """
    Safely get the string value from an enum or return the value if already a string.
    Handles Pydantic's use_enum_values = True which converts enums to strings.
    
    Args:
        enum_val: An Enum instance or string
        
    Returns:
        String value
    """
    return enum_val.value if hasattr(enum_val, 'value') else str(enum_val)
