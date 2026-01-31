"""
VitalFlow AI - Mock Data Generator
Generates realistic hospital data for demo/hackathon purposes
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from faker import Faker

fake = Faker('en_IN')  # Indian locale for realistic names

# Common diagnoses
DIAGNOSES = [
    "Acute Myocardial Infarction",
    "Pneumonia",
    "Sepsis",
    "Stroke",
    "Diabetic Ketoacidosis",
    "Respiratory Failure",
    "Heart Failure",
    "Renal Failure",
    "Trauma - Multiple Injuries",
    "Post-Surgical Recovery",
    "COVID-19 Complications",
    "Gastrointestinal Bleeding",
    "Acute Pancreatitis",
    "Chronic Obstructive Pulmonary Disease",
    "Fracture - Hip",
]

# AI Decision Templates
AI_DECISION_TEMPLATES = [
    {
        "action": "BED_SWAP",
        "template": "Moved Patient #{p1} ({s1}) from {b1} to {b2} because Patient #{p2} ({s2}, SpO2: {spo2}%) needs {bed_type}"
    },
    {
        "action": "ALERT",
        "template": "Critical alert for Patient #{p1}: SpO2 dropped to {spo2}%, Heart Rate: {hr} bpm"
    },
    {
        "action": "STAFF_ASSIGN",
        "template": "Assigned Dr. {doc} to Patient #{p1} due to deteriorating condition"
    },
    {
        "action": "DISCHARGE_RECOMMEND",
        "template": "Patient #{p1} recommended for discharge - stable vitals for 48 hours"
    },
    {
        "action": "ICU_TRANSFER",
        "template": "Urgent ICU transfer initiated for Patient #{p1} - {diagnosis} worsening"
    },
]


def generate_patient_id() -> str:
    """Generate a unique patient ID"""
    return f"P{random.randint(1000, 9999)}"


def generate_bed_id(floor: int, bed_num: int, bed_type: str) -> str:
    """Generate a bed ID based on floor and type"""
    prefix = {"Emergency": "ER", "ICU": "ICU", "General": "GW"}
    return f"{prefix.get(bed_type, 'BED')}-{floor}{bed_num:02d}"


def generate_vitals(status: str) -> Dict[str, Any]:
    """Generate realistic vitals based on patient status"""
    if status == "Critical":
        return {
            "spo2": random.randint(75, 89),
            "heart_rate": random.choice([random.randint(35, 50), random.randint(120, 160)]),
            "blood_pressure": f"{random.randint(70, 90)}/{random.randint(40, 60)}",
            "temperature": round(random.uniform(38.5, 40.5), 1),
        }
    elif status == "Serious":
        return {
            "spo2": random.randint(90, 93),
            "heart_rate": random.choice([random.randint(50, 60), random.randint(100, 120)]),
            "blood_pressure": f"{random.randint(90, 110)}/{random.randint(55, 70)}",
            "temperature": round(random.uniform(37.8, 38.5), 1),
        }
    elif status == "Stable":
        return {
            "spo2": random.randint(95, 98),
            "heart_rate": random.randint(60, 90),
            "blood_pressure": f"{random.randint(110, 130)}/{random.randint(70, 85)}",
            "temperature": round(random.uniform(36.5, 37.3), 1),
        }
    else:  # Recovering
        return {
            "spo2": random.randint(96, 100),
            "heart_rate": random.randint(65, 85),
            "blood_pressure": f"{random.randint(115, 125)}/{random.randint(75, 82)}",
            "temperature": round(random.uniform(36.3, 37.0), 1),
        }


def generate_patient(bed_id: str = None, status: str = None) -> Dict[str, Any]:
    """Generate a single mock patient"""
    if status is None:
        status = random.choices(
            ["Critical", "Serious", "Stable", "Recovering"],
            weights=[15, 25, 35, 25]
        )[0]
    
    vitals = generate_vitals(status)
    admitted_hours_ago = random.randint(1, 168)  # Up to 1 week
    
    return {
        "id": generate_patient_id(),
        "name": fake.name(),
        "age": random.randint(18, 85),
        "diagnosis": random.choice(DIAGNOSES),
        "status": status,
        "spo2": vitals["spo2"],
        "heart_rate": vitals["heart_rate"],
        "blood_pressure": vitals["blood_pressure"],
        "temperature": vitals["temperature"],
        "bed_id": bed_id,
        "admitted_at": (datetime.now() - timedelta(hours=admitted_hours_ago)).isoformat(),
        "assigned_doctor": f"Dr. {fake.last_name()}",
        "notes": random.choice([None, "Requires monitoring", "Family notified", "Awaiting test results"]),
    }


def generate_beds_for_floor(floor: int, bed_type: str, total_beds: int, occupancy_rate: float = 0.75) -> List[Dict]:
    """Generate beds for a floor with patients"""
    beds = []
    patients = []
    
    for i in range(1, total_beds + 1):
        bed_id = generate_bed_id(floor, i, bed_type)
        is_occupied = random.random() < occupancy_rate
        
        bed = {
            "id": bed_id,
            "floor": floor,
            "bed_type": bed_type,
            "is_occupied": is_occupied,
            "patient_id": None,
            "room_number": f"{floor}{i:02d}",
        }
        
        if is_occupied:
            # Critical patients more likely in ICU/Emergency
            if bed_type in ["ICU", "Emergency"]:
                status = random.choices(
                    ["Critical", "Serious", "Stable", "Recovering"],
                    weights=[30, 40, 20, 10]
                )[0]
            else:
                status = random.choices(
                    ["Critical", "Serious", "Stable", "Recovering"],
                    weights=[5, 20, 45, 30]
                )[0]
            
            patient = generate_patient(bed_id, status)
            bed["patient_id"] = patient["id"]
            patients.append(patient)
        
        beds.append(bed)
    
    return beds, patients


def generate_staff(count: int = 20) -> List[Dict]:
    """Generate mock staff members"""
    roles = ["Doctor", "Nurse", "Wardboy", "Driver"]
    role_weights = [20, 40, 25, 15]
    staff = []
    
    for i in range(count):
        role = random.choices(roles, weights=role_weights)[0]
        shift_hours = random.randint(0, 8)
        
        staff.append({
            "id": f"S{i+1:03d}",
            "name": f"{'Dr. ' if role == 'Doctor' else ''}{fake.name()}",
            "role": role,
            "is_on_duty": random.random() < 0.6,
            "shift_start": (datetime.now() - timedelta(hours=shift_hours)).isoformat() if random.random() < 0.6 else None,
            "fatigue_level": min(100, shift_hours * 10 + random.randint(0, 20)),
            "assigned_patients": [],
        })
    
    return staff


def generate_ai_decisions(patients: List[Dict], count: int = 15) -> List[Dict]:
    """Generate mock AI decisions"""
    decisions = []
    
    for i in range(count):
        minutes_ago = random.randint(1, 120)
        timestamp = datetime.now() - timedelta(minutes=minutes_ago)
        
        template = random.choice(AI_DECISION_TEMPLATES)
        
        # Select random patient info
        p1 = random.choice(patients) if patients else {"id": "P0001", "status": "Stable", "spo2": 95, "heart_rate": 80, "diagnosis": "Unknown"}
        p2 = random.choice(patients) if patients else {"id": "P0002", "status": "Critical", "spo2": 82, "heart_rate": 130, "diagnosis": "Unknown"}
        
        action = template["action"]
        
        if action == "BED_SWAP":
            reason = template["template"].format(
                p1=p1["id"].replace("P", ""),
                s1=p1["status"],
                b1=p1.get("bed_id", "ER-101"),
                b2=f"ICU-{random.randint(1, 15):02d}",
                p2=p2["id"].replace("P", ""),
                s2=p2["status"],
                spo2=p2["spo2"],
                bed_type="ICU"
            )
            severity = "WARNING"
        elif action == "ALERT":
            reason = template["template"].format(
                p1=p1["id"].replace("P", ""),
                spo2=random.randint(75, 88),
                hr=random.randint(125, 150)
            )
            severity = "CRITICAL"
        elif action == "STAFF_ASSIGN":
            reason = template["template"].format(
                doc=fake.last_name(),
                p1=p1["id"].replace("P", "")
            )
            severity = "INFO"
        elif action == "DISCHARGE_RECOMMEND":
            reason = template["template"].format(
                p1=p1["id"].replace("P", "")
            )
            severity = "INFO"
        else:  # ICU_TRANSFER
            reason = template["template"].format(
                p1=p1["id"].replace("P", ""),
                diagnosis=p1["diagnosis"]
            )
            severity = "CRITICAL"
        
        decisions.append({
            "id": f"DEC{i+1:04d}",
            "timestamp": timestamp.isoformat(),
            "action": action,
            "reason": reason,
            "patient_id": p1["id"],
            "severity": severity,
        })
    
    # Sort by timestamp (most recent first)
    decisions.sort(key=lambda x: x["timestamp"], reverse=True)
    return decisions


def generate_hospital_data(hospital_id: str = "H001") -> Dict[str, Any]:
    """Generate complete mock hospital data"""
    
    floor_config = {
        1: {"name": "Emergency Department", "bed_type": "Emergency", "beds": 20, "occupancy": 0.85},
        2: {"name": "ICU Complex", "bed_type": "ICU", "beds": 15, "occupancy": 0.90},
        3: {"name": "General Ward A", "bed_type": "General", "beds": 30, "occupancy": 0.70},
        4: {"name": "General Ward B", "bed_type": "General", "beds": 30, "occupancy": 0.65},
        5: {"name": "General Ward C", "bed_type": "General", "beds": 25, "occupancy": 0.60},
    }
    
    floors = []
    all_beds = []
    all_patients = []
    
    for floor_num, config in floor_config.items():
        beds, patients = generate_beds_for_floor(
            floor_num,
            config["bed_type"],
            config["beds"],
            config["occupancy"]
        )
        
        floors.append({
            "floor_number": floor_num,
            "name": config["name"],
            "bed_type": config["bed_type"],
            "total_beds": config["beds"],
            "beds": beds,
        })
        
        all_beds.extend(beds)
        all_patients.extend(patients)
    
    # Generate staff and AI decisions
    staff = generate_staff(25)
    decisions = generate_ai_decisions(all_patients, 20)
    
    # Calculate statistics
    total_beds = len(all_beds)
    occupied_beds = sum(1 for b in all_beds if b["is_occupied"])
    icu_beds = [b for b in all_beds if b["bed_type"] == "ICU"]
    icu_available = sum(1 for b in icu_beds if not b["is_occupied"])
    emergency_beds = [b for b in all_beds if b["bed_type"] == "Emergency"]
    emergency_available = sum(1 for b in emergency_beds if not b["is_occupied"])
    general_beds = [b for b in all_beds if b["bed_type"] == "General"]
    general_available = sum(1 for b in general_beds if not b["is_occupied"])
    
    # Patient status counts
    critical_count = sum(1 for p in all_patients if p["status"] == "Critical")
    serious_count = sum(1 for p in all_patients if p["status"] == "Serious")
    stable_count = sum(1 for p in all_patients if p["status"] == "Stable")
    recovering_count = sum(1 for p in all_patients if p["status"] == "Recovering")
    
    return {
        "hospital": {
            "id": hospital_id,
            "name": "VitalFlow Central Hospital",
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "icu_available": icu_available,
            "emergency_available": emergency_available,
            "general_available": general_available,
            "lat": 19.0760,
            "lon": 72.8777,
            "address": "Marine Drive, Mumbai",
        },
        "floors": floors,
        "beds": all_beds,
        "patients": all_patients,
        "staff": staff,
        "decisions": decisions,
        "stats": {
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": total_beds - occupied_beds,
            "icu_total": len(icu_beds),
            "icu_available": icu_available,
            "emergency_total": len(emergency_beds),
            "emergency_available": emergency_available,
            "general_total": len(general_beds),
            "general_available": general_available,
            "critical_patients": critical_count,
            "serious_patients": serious_count,
            "stable_patients": stable_count,
            "recovering_patients": recovering_count,
            "staff_on_duty": sum(1 for s in staff if s["is_on_duty"]),
            "total_staff": len(staff),
            "admissions_last_hour": random.randint(0, 5),
            "discharges_last_hour": random.randint(0, 3),
        },
        "last_updated": datetime.now().isoformat(),
    }


def generate_network_hospitals() -> List[Dict]:
    """Generate data for multiple hospitals in the network"""
    hospitals = [
        {"id": "H001", "name": "VitalFlow Central Hospital", "lat": 19.0760, "lon": 72.8777, "address": "Marine Drive, Mumbai"},
        {"id": "H002", "name": "VitalFlow North Wing", "lat": 19.1136, "lon": 72.8697, "address": "Bandra West, Mumbai"},
        {"id": "H003", "name": "VitalFlow South Medical", "lat": 19.0176, "lon": 72.8562, "address": "Colaba, Mumbai"},
        {"id": "H004", "name": "VitalFlow East Care", "lat": 19.0596, "lon": 72.9295, "address": "Chembur, Mumbai"},
    ]
    
    result = []
    for h in hospitals:
        total = random.randint(80, 150)
        occupied = int(total * random.uniform(0.6, 0.9))
        icu_total = random.randint(10, 25)
        icu_available = random.randint(0, 5)
        
        result.append({
            **h,
            "total_beds": total,
            "occupied_beds": occupied,
            "available_beds": total - occupied,
            "icu_total": icu_total,
            "icu_available": icu_available,
            "icu_percentage": round((icu_available / icu_total) * 100, 1),
            "occupancy_rate": round((occupied / total) * 100, 1),
        })
    
    return result


# For quick testing
if __name__ == "__main__":
    data = generate_hospital_data()
    print(f"Generated {len(data['patients'])} patients across {len(data['floors'])} floors")
    print(f"Stats: {data['stats']}")
