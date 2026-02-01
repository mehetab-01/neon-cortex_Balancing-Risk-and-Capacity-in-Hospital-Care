"""
Test script for new VitalFlow AI features:
1. Stock Management
2. Patient Reports  
3. Prescription Scanner
4. Doctor Alerts
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_stock_management():
    """Test medicine stock management"""
    print("\n" + "="*60)
    print("📦 Testing STOCK MANAGEMENT")
    print("="*60)
    
    # 1. Get stock summary
    print("\n1️⃣ Getting stock summary...")
    r = requests.get(f"{BASE_URL}/api/stock")
    data = r.json()
    print(f"   ✓ Total medicines: {data['total_medicines']}")
    print(f"   ✓ Status breakdown: {data['status_breakdown']}")
    
    # 2. Get all medicines
    print("\n2️⃣ Getting all medicines...")
    r = requests.get(f"{BASE_URL}/api/stock/medicines")
    medicines = r.json()["medicines"]
    print(f"   ✓ Found {len(medicines)} medicines")
    for med in medicines[:3]:
        print(f"      - {med['name']}: {med['current_stock']}/{med['initial_stock']} ({med['stock_percentage']}%)")
    
    # 3. Record medicine usage
    print("\n3️⃣ Recording medicine usage...")
    r = requests.post(f"{BASE_URL}/api/stock/usage", json={
        "medicine_id": "MED-001",
        "quantity": 50,
        "patient_id": "P001",
        "recorded_by": "Nurse Priya",
        "notes": "Post-surgery pain relief"
    })
    result = r.json()
    if result.get("success"):
        print(f"   ✓ Usage recorded: {result['medicine']['name']}")
        print(f"   ✓ Stock now: {result['medicine']['current_stock']} ({result['medicine']['stock_percentage']}%)")
        if result.get("alert"):
            print(f"   ⚠️ ALERT: {result['alert']['type']} - Stock critical!")
    
    # 4. Record more usage to trigger alert (simulate heavy usage)
    print("\n4️⃣ Simulating heavy usage to trigger 40% threshold alert...")
    r = requests.post(f"{BASE_URL}/api/stock/usage", json={
        "medicine_id": "MED-001",
        "quantity": 200,
        "patient_id": "P002",
        "recorded_by": "Dr. Sharma",
        "notes": "Emergency case"
    })
    result = r.json()
    if result.get("success"):
        print(f"   ✓ Stock now: {result['medicine']['current_stock']} ({result['medicine']['stock_percentage']}%)")
        if result.get("alert"):
            print(f"   🚨 ALERT TRIGGERED: Stock below 40%!")
            print(f"      Recommended order: {result['alert']['recommended_order_quantity']} units")
    
    # 5. Check pending orders
    print("\n5️⃣ Checking pending orders...")
    r = requests.get(f"{BASE_URL}/api/stock/orders/pending")
    orders = r.json()["orders"]
    print(f"   ✓ Pending orders: {len(orders)}")
    for order in orders:
        print(f"      - {order['order_id']}: Rs. {order['total_amount']} (Supplier: {order['supplier']})")
    
    # 6. Verify and approve order (Human-in-the-loop)
    if orders:
        print("\n6️⃣ Verifying order (Human-in-the-loop)...")
        order_id = orders[0]["order_id"]
        r = requests.post(f"{BASE_URL}/api/stock/orders/{order_id}/verify", json={
            "verified_by": "Dr. Admin",
            "approve": True,
            "notes": "Approved for urgent restocking"
        })
        result = r.json()
        if result.get("success"):
            print(f"   ✓ Order {order_id} verified by Dr. Admin")
            print(f"   ✓ Next step: {result.get('next_step')}")
    
    print("\n   ✅ Stock Management Tests PASSED!")

def test_patient_reports():
    """Test patient report system"""
    print("\n" + "="*60)
    print("📋 Testing PATIENT REPORTS")
    print("="*60)
    
    patient_id = "P-TEST-001"
    patient_name = "Test Patient Kumar"
    
    # 1. Initialize patient report
    print("\n1️⃣ Initializing patient report...")
    r = requests.post(f"{BASE_URL}/api/reports/{patient_id}/initialize?patient_name={patient_name}")
    if r.status_code == 200:
        print(f"   ✓ Report initialized for {patient_name}")
    
    # 2. Record vitals
    print("\n2️⃣ Recording patient vitals...")
    r = requests.post(f"{BASE_URL}/api/reports/{patient_id}/vitals", json={
        "recorded_by": "Nurse Anita",
        "spo2": 96.0,
        "heart_rate": 82,
        "blood_pressure": "130/85",
        "temperature": 99.2,
        "respiratory_rate": 18,
        "notes": "Patient stable, slight fever"
    })
    result = r.json()
    if result.get("success"):
        print(f"   ✓ Vitals recorded by Nurse Anita")
        print(f"   ✓ Recovery: {result['recovery']['percentage']}% ({result['recovery']['trend']})")
    
    # 3. Add second vitals reading (to show improvement)
    print("\n3️⃣ Recording improved vitals...")
    r = requests.post(f"{BASE_URL}/api/reports/{patient_id}/vitals", json={
        "recorded_by": "Dr. Sharma",
        "spo2": 98.0,
        "heart_rate": 76,
        "blood_pressure": "120/80",
        "temperature": 98.4,
        "respiratory_rate": 16,
        "notes": "Fever subsided, patient improving"
    })
    result = r.json()
    if result.get("success"):
        print(f"   ✓ Recovery: {result['recovery']['percentage']}% ({result['recovery']['trend']})")
    
    # 4. Add consultation note
    print("\n4️⃣ Adding doctor consultation note...")
    r = requests.post(f"{BASE_URL}/api/reports/{patient_id}/consultation", json={
        "doctor_id": "DOC-001",
        "doctor_name": "Dr. Sharma",
        "findings": "Patient responding well to treatment. Vitals stable.",
        "diagnosis": "Post-operative recovery - Day 2",
        "treatment_plan": "Continue current medications. Encourage mobility.",
        "next_visit": (datetime.now() + timedelta(hours=8)).isoformat(),
        "priority": "Routine"
    })
    result = r.json()
    if result.get("success"):
        print(f"   ✓ Consultation added by Dr. Sharma")
    
    # 5. Get patient-friendly view
    print("\n5️⃣ Getting patient-friendly view...")
    r = requests.get(f"{BASE_URL}/api/reports/{patient_id}/patient-view")
    if r.status_code == 200:
        view = r.json()
        print(f"   ✓ Patient: {view['patient_name']}")
        print(f"   ✓ Recovery: {view['recovery_status']['percentage']}% {view['recovery_status']['trend_emoji']}")
        print(f"   ✓ Message: {view['recovery_status']['message']}")
        if view.get('admission_info', {}).get('estimated_discharge'):
            print(f"   ✓ Estimated Discharge: {view['admission_info']['estimated_discharge']}")
    
    # 6. Get daily summary
    print("\n6️⃣ Getting daily summary for shift handover...")
    r = requests.get(f"{BASE_URL}/api/reports/{patient_id}/summary")
    if r.status_code == 200:
        summary = r.json()
        print(f"   ✓ Vitals recorded: {summary['vitals_count']}")
        print(f"   ✓ Medicines: Given {summary['medicines']['given']}, Pending {summary['medicines']['pending']}")
        print(f"   ✓ Meals served: {summary['meals_served']}")
    
    print("\n   ✅ Patient Report Tests PASSED!")

def test_prescription_scanner():
    """Test prescription scanner"""
    print("\n" + "="*60)
    print("💊 Testing PRESCRIPTION SCANNER")
    print("="*60)
    
    # 1. Upload prescription
    print("\n1️⃣ Uploading prescription for AI scanning...")
    r = requests.post(f"{BASE_URL}/api/prescriptions/upload", json={
        "patient_id": "P-TEST-002",
        "patient_name": "Ramesh Kumar",
        "doctor_id": "DOC-001",
        "doctor_name": "Dr. Sharma",
        "uploaded_by": "Medical Staff",
        "raw_text": """Aspirin 325mg BD x 7 days
Metoprolol 50mg OD x 14 days
Omeprazole 20mg AC x 7 days
Paracetamol 500mg TDS x 5 days"""
    })
    result = r.json()
    if result.get("success"):
        prescription_id = result["prescription"]["prescription_id"]
        print(f"   ✓ Prescription uploaded: {prescription_id}")
        print(f"   ✓ Status: {result['prescription']['status']}")
        print(f"   ✓ Medicines found: {len(result['prescription']['medicines'])}")
    
    # 2. Get detailed medicine info
    print("\n2️⃣ Getting AI-generated medicine details...")
    r = requests.get(f"{BASE_URL}/api/prescriptions/{prescription_id}/details")
    if r.status_code == 200:
        details = r.json()
        print(f"   ✓ Medicine details retrieved for {details['patient_name']}")
        for med in details["medicines"][:2]:
            print(f"\n   💊 {med['medicine_name']} ({med['dosage']})")
            print(f"      Purpose: {med['purpose'][:50]}...")
            print(f"      Schedule: {', '.join(med['scheduled_times'])}")
    
    # 3. Verify prescription
    print("\n3️⃣ Verifying prescription (Medical staff approval)...")
    r = requests.post(
        f"{BASE_URL}/api/prescriptions/{prescription_id}/verify",
        params={"verified_by": "Dr. Admin", "approved": True, "notes": "Verified correct"}
    )
    if r.status_code == 200:
        result = r.json()
        print(f"   ✓ Prescription verified: {result['prescription']['status']}")
    
    # 4. Check pending medicine alerts
    print("\n4️⃣ Checking pending medicine alerts (within 1 hour)...")
    r = requests.get(f"{BASE_URL}/api/prescriptions/alerts/pending?hours=24")
    alerts = r.json()["alerts"]
    print(f"   ✓ Pending alerts: {len(alerts)}")
    for alert in alerts[:3]:
        print(f"      - {alert['medicine_name']} ({alert['dosage']}) at {alert['scheduled_time'][:16]}")
    
    # 5. Simulate alert workflow
    if alerts:
        print("\n5️⃣ Simulating medicine alert workflow...")
        alert_id = alerts[0]["alert_id"]
        
        # Send alert
        r = requests.post(f"{BASE_URL}/api/prescriptions/alerts/{alert_id}/send")
        if r.status_code == 200:
            print(f"   ✓ Alert sent to nurse")
        
        # Acknowledge
        r = requests.post(
            f"{BASE_URL}/api/prescriptions/alerts/{alert_id}/acknowledge",
            params={"acknowledged_by": "Nurse Priya"}
        )
        if r.status_code == 200:
            print(f"   ✓ Alert acknowledged by Nurse Priya")
        
        # Confirm medicine given
        r = requests.post(f"{BASE_URL}/api/prescriptions/alerts/{alert_id}/confirm", json={
            "given_by": "Nurse Priya",
            "notes": "Patient took medicine with water"
        })
        if r.status_code == 200:
            print(f"   ✓ Medicine confirmed as GIVEN")
    
    # 6. Get medicine history
    print("\n6️⃣ Getting patient medicine history...")
    r = requests.get(f"{BASE_URL}/api/prescriptions/patient/P-TEST-002/history")
    if r.status_code == 200:
        history = r.json()
        print(f"   ✓ Total scheduled: {history['total_scheduled']}")
        print(f"   ✓ Given: {history['given']}, Missed: {history['missed']}, Pending: {history['pending']}")
        print(f"   ✓ Compliance rate: {history['compliance_rate']:.1f}%")
    
    print("\n   ✅ Prescription Scanner Tests PASSED!")

def test_doctor_alerts():
    """Test doctor alert system"""
    print("\n" + "="*60)
    print("🚨 Testing DOCTOR ALERT SYSTEM")
    print("="*60)
    
    # 1. Get doctor status summary
    print("\n1️⃣ Getting doctor status summary...")
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/doctors")
    data = r.json()
    print(f"   ✓ Total doctors: {data['total_doctors']}")
    print(f"   ✓ Available: {len(data['available'])}")
    print(f"   ✓ On Leave: {len(data['on_leave'])}")
    
    # 2. Mark doctor on leave
    print("\n2️⃣ Marking Dr. Sharma on leave...")
    r = requests.post(f"{BASE_URL}/api/doctor-alerts/doctors/DOC-001/status", json={
        "status": "On Leave",
        "location": "",
        "on_leave_until": (datetime.now() + timedelta(days=2)).isoformat(),
        "leave_reason": "Personal emergency"
    })
    if r.status_code == 200:
        result = r.json()
        print(f"   ✓ {result['doctor']['name']} marked on leave")
        print(f"   ✓ Until: {result['doctor']['on_leave_until'][:10]}")
    
    # 3. Track patient
    print("\n3️⃣ Tracking critical patient...")
    r = requests.post(f"{BASE_URL}/api/doctor-alerts/track-patient", json={
        "patient_id": "P-CRITICAL-001",
        "patient_name": "Critical Patient Singh",
        "bed_id": "ICU-01",
        "ward": "ICU",
        "primary_doctor_id": "DOC-001",
        "primary_doctor_name": "Dr. Sharma",
        "criticality_level": 3,
        "next_visit": (datetime.now() + timedelta(hours=4)).isoformat()
    })
    if r.status_code == 200:
        print(f"   ✓ Patient tracked: Critical Patient Singh")
    
    # 4. Update patient to critical (should trigger alert since doctor on leave)
    print("\n4️⃣ Patient becomes CRITICAL (Level 1)...")
    r = requests.post(f"{BASE_URL}/api/doctor-alerts/patients/P-CRITICAL-001/criticality", json={
        "criticality_level": 1,
        "condition": "Cardiac arrest risk, BP dropping rapidly",
        "vitals": "BP: 80/50, HR: 120, SpO2: 88%"
    })
    if r.status_code == 200:
        result = r.json()
        print(f"   ✓ Criticality updated to Level 1")
        if result.get("alert"):
            print(f"   🚨 EMERGENCY ALERT SENT!")
            print(f"      Alert ID: {result['alert']['alert_id']}")
            print(f"      To: {result['alert']['doctor_name']}")
            print(f"      Reason: {result['alert']['urgency_reason']}")
    
    # 5. Get pending alerts
    print("\n5️⃣ Getting pending doctor alerts...")
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/alerts")
    alerts = r.json()["alerts"]
    print(f"   ✓ Pending alerts: {len(alerts)}")
    for alert in alerts:
        print(f"      - [{alert['priority']}] {alert['patient_name']}: {alert['message'][:50]}...")
    
    # 6. Doctor acknowledges alert
    if alerts:
        print("\n6️⃣ Doctor acknowledges alert...")
        alert_id = alerts[0]["alert_id"]
        r = requests.post(
            f"{BASE_URL}/api/doctor-alerts/alerts/{alert_id}/acknowledge",
            params={"doctor_id": "DOC-001"},
            json={"response": "Coming immediately", "coming_eta": 15}
        )
        if r.status_code == 200:
            result = r.json()
            print(f"   ✓ Alert acknowledged: {result['alert']['status']}")
            print(f"   ✓ Doctor response: {result['alert']['response_notes']}")
        
        # Mark responding
        print("\n7️⃣ Doctor is responding...")
        r = requests.post(f"{BASE_URL}/api/doctor-alerts/alerts/{alert_id}/responding")
        if r.status_code == 200:
            print(f"   ✓ Doctor marked as responding")
        
        # Resolve
        print("\n8️⃣ Resolving alert...")
        r = requests.post(
            f"{BASE_URL}/api/doctor-alerts/alerts/{alert_id}/resolve",
            params={"notes": "Patient stabilized, crisis averted"}
        )
        if r.status_code == 200:
            print(f"   ✓ Alert resolved successfully")
    
    # 8. Get critical patients
    print("\n9️⃣ Getting all critical patients...")
    r = requests.get(f"{BASE_URL}/api/doctor-alerts/critical-patients")
    patients = r.json()["patients"]
    print(f"   ✓ Critical patients: {len(patients)}")
    for p in patients:
        print(f"      - {p['patient_name']} (Level {p['criticality_level']}): {p['current_condition'][:40]}...")
    
    print("\n   ✅ Doctor Alert System Tests PASSED!")

def main():
    print("\n" + "="*60)
    print("🏥 VitalFlow AI - New Features Test Suite")
    print("="*60)
    
    # Test all new features
    try:
        test_stock_management()
    except Exception as e:
        print(f"\n   ❌ Stock Management Error: {e}")
    
    try:
        test_patient_reports()
    except Exception as e:
        print(f"\n   ❌ Patient Reports Error: {e}")
    
    try:
        test_prescription_scanner()
    except Exception as e:
        print(f"\n   ❌ Prescription Scanner Error: {e}")
    
    try:
        test_doctor_alerts()
    except Exception as e:
        print(f"\n   ❌ Doctor Alerts Error: {e}")
    
    print("\n" + "="*60)
    print("✅ All New Features Test Complete!")
    print("="*60)
    print("\n📍 API Documentation: http://localhost:8000/docs")
    print("\n🆕 NEW ENDPOINTS:")
    print("   📦 Stock: /api/stock/*")
    print("   📋 Reports: /api/reports/*")
    print("   💊 Prescriptions: /api/prescriptions/*")
    print("   🚨 Doctor Alerts: /api/doctor-alerts/*")

if __name__ == "__main__":
    main()
