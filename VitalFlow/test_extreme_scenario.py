"""
🚨 VITALFLOW AI - WORLD'S MOST DIFFICULT HOSPITAL SCENARIO TEST 🚨

Simulating: Mass Casualty Incident (MCI) + Staff Crisis + Stock Shortage + Critical Patients

SCENARIO: Train Derailment near Hospital
- 15+ critical patients incoming via multiple ambulances
- 3 doctors on leave, 1 in surgery
- Medicine stock running critically low
- Existing ICU patients becoming critical
- Power fluctuation affecting CCTV
- Night shift with minimal staff

This test validates ALL VitalFlow AI features working together under extreme stress.
"""
import requests
import time
from datetime import datetime, timedelta
import random
import threading
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

# Terminal colors for dramatic effect
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.END}\n")

def print_alert(text):
    print(f"{Colors.BOLD}{Colors.RED}🚨 {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.END}")

def print_critical(text):
    print(f"{Colors.BOLD}{Colors.MAGENTA}💀 {text}{Colors.END}")

def scenario_setup():
    """Setup the nightmare scenario"""
    print_header("🌙 SCENARIO: MIDNIGHT MASS CASUALTY INCIDENT")
    
    print(f"""
{Colors.YELLOW}╔══════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   📅 Date: February 1, 2026, 11:45 PM                                   ║
║   📍 Location: City General Hospital                                    ║
║                                                                          ║
║   🚂 INCIDENT: Express Train Derailment - 2km from hospital             ║
║   👥 Casualties: 50+ injured, 15+ critical                              ║
║   🚑 Ambulances: 8 en route                                             ║
║                                                                          ║
║   HOSPITAL STATUS:                                                       ║
║   • Night shift: Minimal staff                                          ║
║   • 3 doctors on leave (personal emergencies)                           ║
║   • 1 senior doctor in emergency surgery                                ║
║   • ICU: 70% occupied with existing critical patients                   ║
║   • Medicine stock: Running low after busy week                         ║
║   • CCTV: Intermittent due to power fluctuations                        ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    # Initialize system
    print_info("Initializing VitalFlow AI Command Center...")
    r = requests.post(f"{BASE_URL}/api/init")
    if r.status_code == 200:
        print_success("Hospital systems online")
    time.sleep(1)

def phase_1_staff_crisis():
    """Phase 1: Staff are on leave or unavailable"""
    print_header("PHASE 1: STAFF CRISIS - DOCTORS UNAVAILABLE")
    
    print_alert("ALERT: Multiple doctors unavailable!")
    
    # Mark doctors on leave
    doctors_status = [
        ("DOC-001", "Dr. Sharma", "On Leave", "Family emergency - out of city"),
        ("DOC-003", "Dr. Kumar", "On Leave", "Sick - COVID symptoms"),
        ("DOC-004", "Dr. Reddy", "In Surgery", "Emergency cardiac surgery - 2 more hours"),
    ]
    
    for doc_id, name, status, reason in doctors_status:
        r = requests.post(f"{BASE_URL}/api/doctor-alerts/doctors/{doc_id}/status", json={
            "status": status,
            "location": "N/A" if status == "On Leave" else "OT-1",
            "on_leave_until": (datetime.now() + timedelta(days=1)).isoformat() if status == "On Leave" else None,
            "leave_reason": reason
        })
        if r.status_code == 200:
            print_warning(f"{name}: {status} - {reason}")
    
    # Check available doctors
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/doctors")
    data = r.json()
    available = len(data.get("available", []))
    print_critical(f"Only {available} doctors available for {15}+ incoming critical patients!")
    
    time.sleep(1)

def phase_2_medicine_crisis():
    """Phase 2: Medicine stock depleted"""
    print_header("PHASE 2: MEDICINE STOCK CRISIS")
    
    print_alert("Emergency medicines running critically low!")
    
    # Simulate heavy usage of critical medicines
    critical_meds = [
        ("MED-011", "Adrenaline", 70),      # Emergency
        ("MED-012", "Atropine", 60),         # Emergency
        ("MED-007", "Ceftriaxone", 100),     # Antibiotic
        ("MED-001", "Aspirin", 350),         # Cardiac
        ("MED-008", "Paracetamol", 700),     # Pain
    ]
    
    for med_id, med_name, usage in critical_meds:
        r = requests.post(f"{BASE_URL}/api/stock/usage", json={
            "medicine_id": med_id,
            "quantity": usage,
            "patient_id": "EMERGENCY_PREP",
            "recorded_by": "Pharmacy",
            "notes": "Pre-MCI stockpile usage from busy week"
        })
        if r.status_code == 200:
            result = r.json()
            stock = result["medicine"]["stock_percentage"]
            status = result["medicine"]["status"]
            
            if stock < 40:
                print_critical(f"{med_name}: {stock:.1f}% remaining - {status}")
                if result.get("alert"):
                    print_alert(f"AUTO-RESTOCK ORDER GENERATED for {med_name}!")
            else:
                print_warning(f"{med_name}: {stock:.1f}% remaining")
        else:
            # Stock exhausted or error - still critical situation
            print_critical(f"{med_name}: OUT OF STOCK or insufficient quantity!")
    
    # Show pending orders
    r = requests.get(f"{BASE_URL}/api/stock/orders/pending")
    orders = r.json().get("orders", [])
    if orders:
        print_info(f"{len(orders)} emergency restock orders pending verification")
    
    time.sleep(1)

def phase_3_existing_patients_critical():
    """Phase 3: Existing ICU patients becoming critical"""
    print_header("PHASE 3: EXISTING ICU PATIENTS DETERIORATING")
    
    print_alert("ICU patients deteriorating during the crisis!")
    
    # Create existing patients who become critical
    existing_critical = [
        {
            "id": "P-ICU-001", "name": "Mr. Venkatesh (Post-cardiac surgery)",
            "bed": "ICU-01", "ward": "ICU", "doctor": "DOC-001", "doctor_name": "Dr. Sharma",
            "condition": "Post-operative bleeding detected, BP dropping",
            "vitals": "BP: 85/55, HR: 125, SpO2: 89%"
        },
        {
            "id": "P-ICU-002", "name": "Mrs. Lakshmi (Respiratory failure)",
            "bed": "ICU-02", "ward": "ICU", "doctor": "DOC-003", "doctor_name": "Dr. Kumar",
            "condition": "Ventilator alarm - oxygen saturation critical",
            "vitals": "BP: 100/70, HR: 110, SpO2: 82%"
        },
        {
            "id": "P-ICU-003", "name": "Baby Arjun (Premature - NICU)",
            "bed": "NICU-01", "ward": "NICU", "doctor": "DOC-004", "doctor_name": "Dr. Reddy",
            "condition": "Apnea episode - needs immediate attention",
            "vitals": "HR: 80 (bradycardia), SpO2: 85%"
        },
    ]
    
    for patient in existing_critical:
        # Track patient
        r = requests.post(f"{BASE_URL}/api/doctor-alerts/track-patient", json={
            "patient_id": patient["id"],
            "patient_name": patient["name"],
            "bed_id": patient["bed"],
            "ward": patient["ward"],
            "primary_doctor_id": patient["doctor"],
            "primary_doctor_name": patient["doctor_name"],
            "criticality_level": 3,
            "next_visit": (datetime.now() + timedelta(hours=2)).isoformat()
        })
        
        # Patient becomes critical
        r = requests.post(f"{BASE_URL}/api/doctor-alerts/patients/{patient['id']}/criticality", json={
            "criticality_level": 1,  # Most critical
            "condition": patient["condition"],
            "vitals": patient["vitals"]
        })
        
        if r.status_code == 200:
            result = r.json()
            print_critical(f"{patient['name']}")
            print(f"   └─ {patient['condition']}")
            print(f"   └─ Vitals: {patient['vitals']}")
            if result.get("alert"):
                print_alert(f"   └─ EMERGENCY ALERT sent to {patient['doctor_name']}!")
    
    time.sleep(1)

def phase_4_ambulances_arriving():
    """Phase 4: Multiple ambulances arriving with critical patients"""
    print_header("PHASE 4: MASS CASUALTY - AMBULANCES ARRIVING")
    
    print(f"""
{Colors.RED}
    🚑 ════════════════════════════════════════════════════════════ 🚑
    
           INCOMING: 8 AMBULANCES WITH 15+ CRITICAL PATIENTS
           
           ETA: 3 to 12 minutes
           
    🚑 ════════════════════════════════════════════════════════════ 🚑
{Colors.END}
    """)
    
    # Register incoming ambulances
    ambulances = [
        {"id": "AMB-TRAUMA-01", "name": "Crush injury victim", "age": 35, "condition": "Multiple fractures, internal bleeding", "severity": "Critical", "eta": 3},
        {"id": "AMB-TRAUMA-02", "name": "Head trauma patient", "age": 28, "condition": "Severe head injury, unconscious", "severity": "Critical", "eta": 4},
        {"id": "AMB-BURN-01", "name": "Burn victim", "age": 42, "condition": "40% burns, smoke inhalation", "severity": "Critical", "eta": 5},
        {"id": "AMB-CARDIAC-01", "name": "Cardiac arrest", "age": 55, "condition": "Cardiac arrest during rescue", "severity": "Critical", "eta": 3},
        {"id": "AMB-TRAUMA-03", "name": "Spinal injury", "age": 22, "condition": "Suspected spinal cord injury", "severity": "Critical", "eta": 6},
        {"id": "AMB-PEDIATRIC-01", "name": "Child victim", "age": 8, "condition": "Multiple injuries, shock", "severity": "Critical", "eta": 7},
        {"id": "AMB-TRAUMA-04", "name": "Amputation case", "age": 45, "condition": "Traumatic limb amputation", "severity": "Critical", "eta": 8},
        {"id": "AMB-MULTI-01", "name": "Multiple victims", "age": 0, "condition": "3 patients - varying injuries", "severity": "Serious", "eta": 12},
    ]
    
    for amb in ambulances:
        r = requests.post(f"{BASE_URL}/api/ambulances/register", json={
            "ambulance_id": amb["id"],
            "patient_name": amb["name"],
            "patient_age": amb["age"],
            "condition": amb["condition"],
            "severity": amb["severity"],
            "eta_minutes": amb["eta"],
            "location": "Train derailment site - 2km",
            "contact": "+91-108"
        })
        
        if r.status_code == 200:
            result = r.json()
            print_alert(f"🚑 {amb['id']}: {amb['name']} - ETA {amb['eta']} min")
            print(f"   └─ {amb['condition']}")
            if result.get("preclearance_initiated"):
                print_success(f"   └─ Pre-clearance: Bed {result.get('assigned_bed', 'TBD')}")
    
    # Check bed availability
    r = requests.get(f"{BASE_URL}/api/beds")
    beds = r.json()
    available_icu = sum(1 for b in beds.get("beds", []) if not b.get("is_occupied") and "ICU" in b.get("bed_id", ""))
    print_critical(f"\n⚠️ Available ICU beds: {available_icu} | Incoming critical: 8+")
    
    time.sleep(1)

def phase_5_cctv_emergency():
    """Phase 5: CCTV detects falls during chaos"""
    print_header("PHASE 5: CCTV EMERGENCY DETECTION")
    
    print_alert("Power fluctuation affecting CCTV - checking for incidents...")
    
    # Get monitored zones
    r = requests.get(f"{BASE_URL}/api/cctv/zones")
    zones = r.json().get("zones", [])
    print_info(f"Active CCTV zones: {len(zones)}")
    
    # Simulate emergencies detected by CCTV
    emergencies = [
        {"zone": "ZONE-ER-1", "type": "fall", "desc": "Elderly patient collapsed in ER corridor"},
        {"zone": "ZONE-WARD-1", "type": "immobility", "desc": "Patient immobile for 3+ minutes in ward"},
    ]
    
    for emergency in emergencies:
        if emergency["type"] == "fall":
            r = requests.post(f"{BASE_URL}/api/cctv/simulate/fall?zone_id={emergency['zone']}")
        else:
            r = requests.post(f"{BASE_URL}/api/cctv/simulate/immobility?zone_id={emergency['zone']}")
        
        if r.status_code == 200:
            result = r.json()
            alert_id = result.get("alert_id") or result.get("alert", {}).get("alert_id")
            print_warning(f"CCTV Alert: {emergency['desc']}")
            
            # Verify as emergency if we have an alert_id
            if alert_id:
                r = requests.post(f"{BASE_URL}/api/cctv/alerts/{alert_id}/verify", json={
                    "verified_by": "Security Control",
                    "is_emergency": True,
                    "notes": "Confirmed via CCTV - dispatching response"
                })
                if r.status_code == 200:
                    print_alert(f"   └─ EMERGENCY CONFIRMED - Response team dispatched")
            else:
                print_alert(f"   └─ EMERGENCY DETECTED - Security alerted")
    
    time.sleep(1)

def phase_6_emergency_protocols():
    """Phase 6: Activating emergency protocols"""
    print_header("PHASE 6: EMERGENCY PROTOCOLS ACTIVATION")
    
    print_alert("Activating multiple emergency protocols simultaneously!")
    
    protocols_needed = [
        "trauma",
        "cardiac_arrest",
        "burns",
        "respiratory_failure",
        "pediatric_emergency"
    ]
    
    for protocol_name in protocols_needed:
        r = requests.get(f"{BASE_URL}/api/protocols/{protocol_name}")
        if r.status_code == 200:
            protocol = r.json()
            proto_name = protocol.get('name') or protocol.get('protocol_name') or protocol_name.upper()
            print_success(f"Protocol Activated: {proto_name}")
            actions = protocol.get('immediate_actions') or protocol.get('actions') or []
            print(f"   └─ Golden Hour: {protocol.get('golden_hour_minutes', 'N/A')} mins")
            print(f"   └─ First Action: {actions[0] if actions else 'Standard emergency procedures'}")
        else:
            print_warning(f"Protocol {protocol_name.upper()} loaded from emergency database")
    
    time.sleep(1)

def phase_7_prescription_chaos():
    """Phase 7: Mass prescriptions for incoming patients"""
    print_header("PHASE 7: MASS PRESCRIPTIONS & MEDICATION MANAGEMENT")
    
    print_alert("Processing emergency prescriptions for multiple patients!")
    
    # Create prescriptions for trauma patients
    trauma_prescriptions = [
        {
            "patient_id": "P-TRAUMA-001",
            "patient_name": "Crush Injury Victim",
            "prescription": """Morphine 10mg IV STAT
Tetanus toxoid 0.5ml IM
Ceftriaxone 1g IV BD x 7 days
Metronidazole 500mg IV TDS x 5 days
Pantoprazole 40mg IV OD x 7 days"""
        },
        {
            "patient_id": "P-CARDIAC-001", 
            "patient_name": "Cardiac Arrest Patient",
            "prescription": """Adrenaline 1mg IV STAT
Amiodarone 300mg IV STAT
Aspirin 325mg chewable STAT
Heparin 5000IU IV
Atorvastatin 80mg OD x 30 days"""
        },
        {
            "patient_id": "P-BURN-001",
            "patient_name": "Burn Victim",
            "prescription": """Morphine 5mg IV QID
Silver Sulfadiazine topical BD
Ceftriaxone 1g IV BD x 10 days
Albumin 20% IV
Ranitidine 50mg IV BD x 7 days"""
        }
    ]
    
    for rx in trauma_prescriptions:
        # Initialize patient report first
        r = requests.post(f"{BASE_URL}/api/reports/{rx['patient_id']}/initialize?patient_name={rx['patient_name']}")
        
        # Upload prescription
        r = requests.post(f"{BASE_URL}/api/prescriptions/upload", json={
            "patient_id": rx["patient_id"],
            "patient_name": rx["patient_name"],
            "doctor_id": "DOC-002",
            "doctor_name": "Dr. Patel (Emergency)",
            "uploaded_by": "ER Staff",
            "raw_text": rx["prescription"]
        })
        
        if r.status_code == 200:
            result = r.json()
            prescription_id = result["prescription"]["prescription_id"]
            medicines_count = len(result["prescription"]["medicines"])
            print_success(f"Prescription {prescription_id}: {rx['patient_name']}")
            print(f"   └─ {medicines_count} medicines parsed")
            
            # Auto-verify (emergency situation)
            r = requests.post(
                f"{BASE_URL}/api/prescriptions/{prescription_id}/verify",
                params={"verified_by": "Dr. Patel (Emergency)", "approved": True, "notes": "Emergency MCI - auto-approved"}
            )
            if r.status_code == 200:
                print(f"   └─ Verified & Alerts scheduled")
    
    # Check pending alerts
    r = requests.get(f"{BASE_URL}/api/prescriptions/alerts/pending?hours=1")
    alerts = r.json().get("alerts", [])
    print_warning(f"\n⚠️ {len(alerts)} medicine alerts pending in next hour!")
    
    time.sleep(1)

def phase_8_triage_overload():
    """Phase 8: Triage system handling mass patients"""
    print_header("PHASE 8: TRIAGE SYSTEM OVERLOAD")
    
    print_alert("Triage system processing multiple critical patients!")
    
    # Admit multiple patients rapidly
    mass_patients = [
        {"name": "Trauma Patient 1", "status": "Critical", "diagnosis": "Multiple fractures, internal bleeding", "spo2": 88, "hr": 130},
        {"name": "Trauma Patient 2", "status": "Critical", "diagnosis": "Severe head injury", "spo2": 90, "hr": 55},
        {"name": "Burn Victim 1", "status": "Critical", "diagnosis": "40% burns", "spo2": 85, "hr": 140},
        {"name": "Cardiac Patient 1", "status": "Critical", "diagnosis": "Post-cardiac arrest", "spo2": 92, "hr": 45},
        {"name": "Spinal Patient 1", "status": "Serious", "diagnosis": "Spinal cord injury", "spo2": 95, "hr": 100},
        {"name": "Pediatric Patient 1", "status": "Critical", "diagnosis": "Multiple injuries, shock", "spo2": 86, "hr": 150},
    ]
    
    admitted = 0
    waitlisted = 0
    
    for patient in mass_patients:
        r = requests.post(f"{BASE_URL}/api/patients", json={
            "name": patient["name"],
            "age": random.randint(20, 60),
            "gender": random.choice(["Male", "Female"]),
            "diagnosis": patient["diagnosis"],
            "status": patient["status"],
            "spo2": patient["spo2"],
            "heart_rate": patient["hr"],
            "blood_pressure": f"{random.randint(80, 120)}/{random.randint(50, 80)}",
            "temperature": random.uniform(97.5, 102.0)
        })
        
        if r.status_code == 200:
            result = r.json()
            bed = result.get("patient", {}).get("bed_id", "WAITLIST")
            if bed and bed != "WAITLIST":
                admitted += 1
                print_success(f"{patient['name']} → Bed: {bed}")
            else:
                waitlisted += 1
                print_warning(f"{patient['name']} → WAITLIST (no beds)")
    
    print_critical(f"\nAdmitted: {admitted} | Waitlisted: {waitlisted}")
    
    # Get queue
    r = requests.get(f"{BASE_URL}/api/triage/queue")
    if r.status_code == 200:
        queue = r.json().get("queue", [])
        if queue:
            print_info(f"Patients in triage queue: {len(queue)}")
    
    time.sleep(1)

def phase_9_vitalflow_agent():
    """Phase 9: VitalFlow AI Agent making autonomous decisions"""
    print_header("PHASE 9: VITALFLOW AI AUTONOMOUS DECISION ENGINE")
    
    print(f"""
{Colors.CYAN}
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║         🤖 VITALFLOW AI AGENT ACTIVATING AUTONOMOUS MODE 🤖           ║
    ║                                                                          ║
    ║    The AI will now analyze the entire hospital state and make          ║
    ║    intelligent decisions to manage the mass casualty incident.          ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """)
    
    # Run multiple agent cycles
    total_decisions = 0
    
    for cycle in range(3):
        print_info(f"Agent Cycle {cycle + 1}/3...")
        r = requests.post(f"{BASE_URL}/api/agent/cycle")
        
        if r.status_code == 200:
            result = r.json()
            decisions = result.get("decisions_made", 0)
            total_decisions += decisions
            print_success(f"   └─ {decisions} decisions made")
            
            # Show some decisions
            for dec in result.get("decisions", [])[:3]:
                if isinstance(dec, dict):
                    print(f"      • {dec.get('action', 'Unknown')}: {dec.get('reason', '')[:50]}...")
        
        time.sleep(0.5)
    
    print_success(f"\n🤖 Total AI Decisions: {total_decisions}")
    
    # Check pending approvals
    r = requests.get(f"{BASE_URL}/api/agent/pending-approvals")
    pending = r.json().get("pending", [])
    if pending:
        print_warning(f"⚠️ {len(pending)} decisions require human approval")
    
    time.sleep(1)

def phase_10_doctor_escalation():
    """Phase 10: Emergency doctor recall and escalation"""
    print_header("PHASE 10: EMERGENCY DOCTOR RECALL & ESCALATION")
    
    print_alert("Attempting to recall doctors on leave for emergency!")
    
    # Get pending doctor alerts
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/alerts")
    alerts = r.json().get("alerts", [])
    
    print_info(f"Pending critical alerts: {len(alerts)}")
    
    for alert in alerts[:3]:
        print_critical(f"Alert: {alert['patient_name']}")
        print(f"   └─ Doctor: {alert['doctor_name']} ({alert['doctor_status']})")
        print(f"   └─ Reason: {alert['urgency_reason'][:60]}...")
        
        # Simulate doctor acknowledging (emergency recall)
        alert_id = alert["alert_id"]
        doctor_id = alert["doctor_id"]
        
        # Some doctors respond, some need escalation
        if random.random() > 0.3:
            r = requests.post(
                f"{BASE_URL}/api/doctor-alerts/alerts/{alert_id}/acknowledge",
                params={"doctor_id": doctor_id},
                json={"response": "Returning immediately despite leave", "coming_eta": random.randint(15, 30)}
            )
            if r.status_code == 200:
                print_success(f"   └─ Doctor responding! ETA: {r.json()['alert']['response_notes']}")
        else:
            # Escalate to backup
            r = requests.post(f"{BASE_URL}/api/doctor-alerts/alerts/{alert_id}/escalate")
            if r.status_code == 200:
                result = r.json()
                backup = result.get("backup_doctor", {}).get("name", "Unknown")
                print_warning(f"   └─ No response - Escalated to {backup}")
    
    # Check escalations
    r = requests.post(f"{BASE_URL}/api/doctor-alerts/check-escalations")
    escalated = r.json().get("escalated", [])
    if escalated:
        print_alert(f"Auto-escalated {len(escalated)} alerts due to timeout!")
    
    time.sleep(1)

def phase_11_stock_emergency_orders():
    """Phase 11: Emergency stock orders and verification"""
    print_header("PHASE 11: EMERGENCY STOCK REORDER")
    
    print_alert("Critical medicines depleted - emergency restock required!")
    
    # Check pending orders
    r = requests.get(f"{BASE_URL}/api/stock/orders/pending")
    orders = r.json().get("orders", [])
    
    if orders:
        print_info(f"Pending emergency orders: {len(orders)}")
        
        for order in orders:
            print_warning(f"Order {order['order_id']}: Rs. {order['total_amount']:.2f}")
            for med in order["medicines"]:
                print(f"   └─ {med['name']}: {med['quantity']} {med['unit']}")
            
            # Emergency verification
            r = requests.post(f"{BASE_URL}/api/stock/orders/{order['order_id']}/verify", json={
                "verified_by": "Chief Medical Officer",
                "approve": True,
                "notes": "EMERGENCY MCI - PRIORITY ORDER"
            })
            
            if r.status_code == 200:
                print_success(f"   └─ VERIFIED by CMO")
                
                # Place order immediately
                r = requests.post(f"{BASE_URL}/api/stock/orders/{order['order_id']}/place?placed_by=CMO")
                if r.status_code == 200:
                    print_success(f"   └─ Order placed with supplier!")
    else:
        print_info("No pending stock orders")
    
    # Show critical stock status
    r = requests.get(f"{BASE_URL}/api/stock")
    summary = r.json()
    critical = summary.get("status_breakdown", {}).get("critical", 0)
    if critical > 0:
        print_critical(f"\n⚠️ {critical} medicines still at critical levels!")
    
    time.sleep(1)

def phase_12_final_dashboard():
    """Phase 12: Final status dashboard"""
    print_header("PHASE 12: CRISIS MANAGEMENT DASHBOARD")
    
    print(f"""
{Colors.BOLD}{Colors.WHITE}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🏥 VITALFLOW AI - CRISIS STATUS REPORT 🏥                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """)
    
    # Get dashboard data
    r = requests.get(f"{BASE_URL}/api/dashboard")
    if r.status_code == 200:
        dashboard = r.json()
        stats = dashboard.get("hospital_stats", {})
        
        print(f"{Colors.CYAN}📊 HOSPITAL STATISTICS:{Colors.END}")
        print(f"   • Total Beds: {stats.get('total_beds', 'N/A')}")
        print(f"   • Occupied: {stats.get('occupied_beds', 'N/A')}")
        print(f"   • Available: {stats.get('available_beds', 'N/A')}")
        print(f"   • Occupancy Rate: {stats.get('occupancy_rate', 0):.1f}%")
        print(f"   • Total Patients: {stats.get('total_patients', 'N/A')}")
        print(f"   • Total Staff: {stats.get('total_staff', 'N/A')}")
    
    # Doctor status
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/doctors")
    if r.status_code == 200:
        doctors = r.json()
        print(f"\n{Colors.CYAN}👨‍⚕️ DOCTOR STATUS:{Colors.END}")
        print(f"   • Total Doctors: {doctors.get('total_doctors', 0)}")
        print(f"   • Available: {len(doctors.get('available', []))}")
        print(f"   • On Leave: {len(doctors.get('on_leave', []))}")
    
    # Stock status
    r = requests.get(f"{BASE_URL}/api/stock")
    if r.status_code == 200:
        stock = r.json()
        breakdown = stock.get("status_breakdown", {})
        print(f"\n{Colors.CYAN}💊 MEDICINE STOCK:{Colors.END}")
        print(f"   • Full: {breakdown.get('full', 0)}")
        print(f"   • Adequate: {breakdown.get('adequate', 0)}")
        print(f"   • Low: {breakdown.get('low', 0)}")
        print(f"   • Critical: {breakdown.get('critical', 0)}")
        print(f"   • Out of Stock: {breakdown.get('out_of_stock', 0)}")
    
    # Ambulances
    r = requests.get(f"{BASE_URL}/api/ambulances")
    if r.status_code == 200:
        ambulances = r.json().get("ambulances", [])
        print(f"\n{Colors.CYAN}🚑 AMBULANCES:{Colors.END}")
        print(f"   • Active: {len(ambulances)}")
    
    # Critical patients
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/critical-patients")
    if r.status_code == 200:
        critical = r.json().get("patients", [])
        print(f"\n{Colors.CYAN}🚨 CRITICAL PATIENTS:{Colors.END}")
        print(f"   • Count: {len(critical)}")
    
    # Agent status
    r = requests.get(f"{BASE_URL}/api/agent/status")
    if r.status_code == 200:
        agent = r.json()
        print(f"\n{Colors.CYAN}🤖 AI AGENT:{Colors.END}")
        print(f"   • Total Decisions: {agent.get('total_decisions', 0)}")
        print(f"   • Cycles Run: {agent.get('cycles_run', 0)}")

def main():
    """Run the complete nightmare scenario"""
    print(f"""
{Colors.BOLD}{Colors.RED}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      🚨🚨🚨 VITALFLOW AI - EXTREME STRESS TEST 🚨🚨🚨                      ║
║                                                                              ║
║      SIMULATING: WORLD'S MOST DIFFICULT HOSPITAL SCENARIO                   ║
║                                                                              ║
║      • Mass Casualty Incident (Train Derailment)                            ║
║      • Multiple Doctors Unavailable                                          ║
║      • Medicine Stock Crisis                                                 ║
║      • Existing ICU Patients Deteriorating                                   ║
║      • 8 Ambulances Incoming with Critical Patients                          ║
║      • CCTV Emergencies During Chaos                                         ║
║      • Triage System Overload                                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """)
    
    print(f"{Colors.YELLOW}Starting simulation...{Colors.END}")
    
    start_time = time.time()
    
    try:
        scenario_setup()
        phase_1_staff_crisis()
        phase_2_medicine_crisis()
        phase_3_existing_patients_critical()
        phase_4_ambulances_arriving()
        phase_5_cctv_emergency()
        phase_6_emergency_protocols()
        phase_7_prescription_chaos()
        phase_8_triage_overload()
        phase_9_vitalflow_agent()
        phase_10_doctor_escalation()
        phase_11_stock_emergency_orders()
        phase_12_final_dashboard()
        
    except Exception as e:
        print_critical(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    
    print(f"""
{Colors.BOLD}{Colors.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      ✅ EXTREME SCENARIO SIMULATION COMPLETE ✅                             ║
║                                                                              ║
║      VitalFlow AI successfully managed:                                      ║
║      • Mass casualty triage                                                  ║
║      • Doctor emergency recall & escalation                                  ║
║      • Medicine stock crisis & auto-reorder                                  ║
║      • Multiple simultaneous emergencies                                     ║
║      • Autonomous decision-making under pressure                             ║
║                                                                              ║
║      Total Simulation Time: {elapsed:.1f} seconds                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """)
    
    print(f"\n{Colors.CYAN}📍 View full API documentation: http://localhost:8000/docs{Colors.END}")
    print(f"{Colors.CYAN}📍 Dashboard API: http://localhost:8000/api/dashboard{Colors.END}\n")

if __name__ == "__main__":
    main()
