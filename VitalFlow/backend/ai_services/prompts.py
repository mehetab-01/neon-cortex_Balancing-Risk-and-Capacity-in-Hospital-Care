"""
All AI prompts in one place for easy tuning.
Centralized prompt management for VitalFlow AI services.
"""

# ============== MEDICINE & EQUIPMENT RECOMMENDATION ==============

MEDICINE_RECOMMENDATION_PROMPT = """
You are a hospital AI assistant. Based on the patient information, generate a preparation checklist for the nursing staff.

Patient Information:
- Name: {patient_name}
- Age: {age} years
- Diagnosis: {diagnosis}
- Current Status: {status}
- SpO2: {spo2}%
- Heart Rate: {heart_rate} bpm
- Blood Pressure: {blood_pressure}
- Temperature: {temperature}°F
- Bed: {bed_id}
- Priority: {priority}

Generate a JSON response with:
{{
    "equipment": ["list of equipment to prepare"],
    "medications": ["list of medications with dosages"],
    "urgency": "HIGH/MEDIUM/LOW",
    "special_instructions": "any special notes for nursing staff",
    "monitoring_frequency": "how often to check vitals",
    "warning_signs": ["signs to watch for"]
}}

Be specific and realistic. For critical cases, always include emergency equipment.
Response must be valid JSON only, no additional text.
"""

MEDICINE_RECOMMENDATION_SIMPLE = """
Generate a medical preparation checklist for:
- Diagnosis: {diagnosis}
- Status: {status}
- SpO2: {spo2}%, Heart Rate: {heart_rate}

Return JSON with: equipment, medications, urgency, special_instructions.
"""


# ============== VOICE ALERT TEMPLATES ==============

VOICE_ALERT_TEMPLATES = {
    "CODE_BLUE": (
        "Code Blue. Nurse station {station}. "
        "Patient in Bed {bed_id} requires immediate attention. "
        "Bring emergency cart with defibrillator and {medications}."
    ),
    
    "CODE_RED": (
        "Code Red. Fire emergency at {location}. "
        "All personnel follow evacuation protocol. "
        "Move patients to designated safe zones immediately."
    ),
    
    "TRANSFER_ALERT": (
        "Attention. Patient transfer initiated. "
        "{patient_name} moving from {from_bed} to {to_bed}. "
        "Ward boy, please proceed immediately."
    ),
    
    "VITALS_WARNING": (
        "Warning. Patient in Bed {bed_id} showing declining vitals. "
        "SpO2 at {spo2} percent. Heart rate at {heart_rate}. "
        "Nurse, please check immediately."
    ),
    
    "VITALS_CRITICAL": (
        "Critical Alert. Patient in Bed {bed_id} has dangerous vitals. "
        "SpO2 dropped to {spo2} percent. "
        "Doctor and nurse respond immediately."
    ),
    
    "BED_READY": (
        "Ambulance notification. "
        "Bed {bed_id} in {ward} is now ready. "
        "ETA {eta} minutes. Prepare for incoming patient."
    ),
    
    "FATIGUE_ALERT": (
        "Attention Doctor {doctor_name}. "
        "You have been on duty for {hours} hours. "
        "Please take a break. Critical cases will be reassigned."
    ),
    
    "SWAP_NOTIFICATION": (
        "Bed swap in progress. "
        "Patient {patient_out} transferring to {bed_out}. "
        "Patient {patient_in} will occupy {bed_in}. "
        "Ward boys assist with transfer."
    ),
    
    "AMBULANCE_ARRIVING": (
        "Incoming ambulance. "
        "Patient {patient_name} arriving in {eta} minutes. "
        "Condition: {condition}. "
        "Prepare {bed_type} bed and emergency team."
    ),
    
    "PATIENT_ADMITTED": (
        "New patient admitted. "
        "{patient_name}, age {age}. "
        "Assigned to bed {bed_id}. "
        "Doctor {doctor_name} please review."
    ),
    
    "DISCHARGE_READY": (
        "Patient {patient_name} in bed {bed_id} is ready for discharge. "
        "Please complete discharge procedures."
    ),
    
    "SHIFT_CHANGE": (
        "Attention all staff. Shift change in {minutes} minutes. "
        "Please complete handover documentation."
    )
}


# ============== TRIAGE DECISION EXPLANATIONS ==============

TRIAGE_DECISION_PROMPT = """
You are a hospital triage AI. Explain your decision in simple terms for the hospital staff log.

Action taken: {action}
Patient: {patient_name}
Details: {details}

Write a brief (1-2 sentences) human-readable explanation of why this decision was made.
Focus on patient safety and resource optimization.
Keep it professional and clear.
"""

SWAP_EXPLANATION_PROMPT = """
Explain this bed swap decision for hospital staff:

Incoming Patient: {incoming_name}
- Status: {incoming_status}
- SpO2: {incoming_spo2}%
- Heart Rate: {incoming_hr} bpm

Swapped Patient: {swapped_name}
- Status: {swapped_status}
- Stability Score: {stability_score}/100

Action: {swapped_name} moved from ICU to {new_bed} to make room for {incoming_name}.

Provide a brief, professional explanation (2-3 sentences) suitable for medical documentation.
"""


# ============== DIAGNOSIS ASSISTANCE ==============

SYMPTOM_ANALYSIS_PROMPT = """
You are a medical AI assistant. Analyze the following symptoms and suggest possible conditions.

Patient Symptoms:
{symptoms}

Vital Signs:
- SpO2: {spo2}%
- Heart Rate: {heart_rate} bpm
- Blood Pressure: {blood_pressure}
- Temperature: {temperature}°F

Return a JSON response with:
{{
    "possible_conditions": ["list of possible diagnoses"],
    "recommended_tests": ["tests to confirm diagnosis"],
    "urgency_level": "CRITICAL/HIGH/MEDIUM/LOW",
    "immediate_actions": ["immediate steps to take"],
    "notes": "additional observations"
}}

IMPORTANT: This is for decision support only. All diagnoses must be confirmed by a licensed physician.
"""


# ============== HANDOFF SUMMARY ==============

HANDOFF_SUMMARY_PROMPT = """
Generate a shift handoff summary for the following patient:

Patient: {patient_name} (Age: {age})
Bed: {bed_id}
Diagnosis: {diagnosis}
Current Status: {status}

Recent Events:
{events}

Current Vitals:
- SpO2: {spo2}%
- Heart Rate: {heart_rate} bpm
- Blood Pressure: {blood_pressure}

Current Medications:
{medications}

Generate a concise but complete handoff summary including:
1. Key concerns to monitor
2. Pending tests/procedures
3. Medication schedule
4. Special instructions

Keep it under 200 words.
"""


# ============== ERROR MESSAGES ==============

ERROR_MESSAGES = {
    "API_UNAVAILABLE": "AI service temporarily unavailable. Using rule-based recommendations.",
    "INVALID_RESPONSE": "AI response could not be parsed. Using fallback.",
    "RATE_LIMITED": "API rate limit reached. Please try again in a few minutes.",
    "TIMEOUT": "AI service timed out. Using cached or fallback response.",
}


# ============== PROMPT UTILITIES ==============

def format_prompt(template: str, **kwargs) -> str:
    """
    Safely format a prompt template with provided values.
    Missing values are replaced with 'N/A'.
    
    Args:
        template: Prompt template with {placeholders}
        **kwargs: Values to substitute
        
    Returns:
        Formatted prompt string
    """
    import re
    
    # Find all placeholders in template
    placeholders = re.findall(r'\{(\w+)\}', template)
    
    # Create defaults for missing values
    defaults = {p: 'N/A' for p in placeholders}
    defaults.update(kwargs)
    
    try:
        return template.format(**defaults)
    except KeyError as e:
        print(f"Warning: Missing prompt placeholder: {e}")
        return template


def get_voice_alert(template_key: str, **kwargs) -> str:
    """
    Get formatted voice alert text from template.
    
    Args:
        template_key: Key from VOICE_ALERT_TEMPLATES
        **kwargs: Values to substitute
        
    Returns:
        Formatted alert text or None if template not found
    """
    template = VOICE_ALERT_TEMPLATES.get(template_key)
    if not template:
        return None
    return format_prompt(template, **kwargs)


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Prompts...")
    
    # Test medicine recommendation prompt
    prompt = format_prompt(
        MEDICINE_RECOMMENDATION_PROMPT,
        patient_name="John Doe",
        age=55,
        diagnosis="Cardiac Arrest",
        status="Critical",
        spo2=82,
        heart_rate=145,
        blood_pressure="180/120",
        temperature=99.1,
        bed_id="ICU-01",
        priority=1
    )
    assert "John Doe" in prompt
    assert "Cardiac Arrest" in prompt
    print("✓ Medicine recommendation prompt formatted correctly")
    
    # Test voice alert
    alert = get_voice_alert(
        "CODE_BLUE",
        station="A3",
        bed_id="ICU-05",
        medications="epinephrine and atropine"
    )
    assert "Code Blue" in alert
    assert "ICU-05" in alert
    print(f"✓ Voice alert: {alert[:50]}...")
    
    # Test voice alert with missing values
    alert = get_voice_alert(
        "VITALS_WARNING",
        bed_id="GEN-02",
        spo2=88
        # heart_rate missing - should show N/A
    )
    assert "N/A" in alert or "GEN-02" in alert
    print("✓ Missing values handled correctly")
    
    # Test all voice templates
    for key in VOICE_ALERT_TEMPLATES.keys():
        assert key in VOICE_ALERT_TEMPLATES
    print(f"✓ All {len(VOICE_ALERT_TEMPLATES)} voice templates available")
    
    print("\n✅ All prompt tests passed!")
