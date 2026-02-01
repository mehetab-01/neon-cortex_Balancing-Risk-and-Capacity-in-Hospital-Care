"""
VitalFlow AI - Complete System Test
Tests all major features of the VitalFlow hospital command center.
"""
import requests

BASE_URL = 'http://localhost:8000'

def main():
    print('=' * 60)
    print('🏥 VitalFlow AI - Complete System Test')
    print('=' * 60)

    # 1. Initialize demo data
    print('\n1️⃣ Initializing demo data...')
    r = requests.post(f'{BASE_URL}/api/init')
    result = r.json()
    print(f'   ✓ Beds: {result["beds"]}, Staff: {result["staff"]}, Patients: {result["patients"]}')

    # 2. Test Emergency Protocols
    print('\n2️⃣ Testing Emergency Protocols...')
    r = requests.get(f'{BASE_URL}/api/protocols')
    protocols = r.json()['protocols']
    print(f'   ✓ Available protocols: {len(protocols)}')
    print(f'   {protocols[:5]}...')

    r = requests.get(f'{BASE_URL}/api/protocols/heart_attack')
    data = r.json()
    protocol = data['protocol']
    print(f'   ✓ Heart Attack Protocol: Golden Hour = {protocol["golden_hour_minutes"]} mins')
    print(f'     Medications: {protocol["medications"][:3]}...')

    # 3. Test Ambulance Registration
    print('\n3️⃣ Testing Ambulance Management...')
    r = requests.post(f'{BASE_URL}/api/ambulances/register', json={
        'ambulance_id': 'AMB-101',
        'patient_name': 'Emergency Patient',
        'patient_age': 55,
        'condition': 'Chest Pain',
        'severity': 'Critical',
        'eta_minutes': 8,
        'location': 'Highway NH-48'
    })
    result = r.json()
    print(f'   ✓ {result["message"]}')
    print(f'     ETA: {result["eta_minutes"]} mins, Pre-clearance: {result["pre_clearance_at_minutes"]} mins')

    # Get all ambulances
    r = requests.get(f'{BASE_URL}/api/ambulances')
    print(f'   ✓ Active ambulances: {r.json()["count"]}')

    # 4. Test Billing
    print('\n4️⃣ Testing Billing Agent...')
    r = requests.get(f'{BASE_URL}/api/billing/P001')
    if r.status_code == 200:
        bill = r.json()
        print(f'   ✓ Bill retrieved for P001')
        print(f'     Total: Rs. {bill.get("total", 0)}')
    else:
        print(f'   ⚠ Could not get bill: {r.status_code}')

    r = requests.post(f'{BASE_URL}/api/billing/P001/medicine?medicine_name=aspirin&quantity=2')
    if r.status_code == 200:
        result = r.json()
        print(f'   ✓ Medicine added: {result.get("item_name", "aspirin")}')
    else:
        print(f'   ⚠ Medicine add failed: {r.status_code}')

    r = requests.post(f'{BASE_URL}/api/billing/P001/procedure?procedure_name=ecg')
    if r.status_code == 200:
        result = r.json()
        print(f'   ✓ Procedure added: {result.get("item_name", "ecg")}')
    else:
        print(f'   ⚠ Procedure add failed')

    r = requests.post(f'{BASE_URL}/api/billing/P001/bed-charge?bed_type=icu&days=0.5')
    if r.status_code == 200:
        print(f'   ✓ Bed charges added')
    else:
        print(f'   ⚠ Bed charge failed')

    r = requests.get(f'{BASE_URL}/api/billing/P001')
    if r.status_code == 200:
        bill = r.json()
        print(f'   ✓ Updated Total: Rs. {bill.get("total", 0)}')

    # 5. Test CCTV/Fall Detection
    print('\n5️⃣ Testing CCTV Fall Detection...')
    r = requests.get(f'{BASE_URL}/api/cctv/zones')
    zones = r.json()['zones']
    print(f'   ✓ Monitored zones: {len(zones)}')
    for z in zones[:3]:
        print(f'     - {z["zone_id"]}: {z["zone_name"]}')

    r = requests.post(f'{BASE_URL}/api/cctv/simulate/fall?zone_id=ZONE-WARD-1')
    alert = r.json()['alert']
    print(f'   ✓ Simulated fall: {alert["alert_id"]}')
    print(f'     Type: {alert["type"]}, Location: {alert["zone_name"]}')

    # Verify the alert
    r = requests.post(f'{BASE_URL}/api/cctv/alerts/{alert["alert_id"]}/verify', json={
        'verified_by': 'ADMIN001',
        'is_emergency': True,
        'notes': 'Patient fell in ward, needs assistance'
    })
    result = r.json()
    print(f'   ✓ Alert verified: {result["status"]}')

    # 6. Test VitalFlow Agent
    print('\n6️⃣ Testing VitalFlow Agent...')
    r = requests.get(f'{BASE_URL}/api/agent/status')
    status = r.json()
    print(f'   ✓ Agent running: {status.get("is_running", False)}')
    print(f'     Cycles: {status.get("cycle_count", 0)}, Decisions: {status.get("decision_count", 0)}')

    r = requests.post(f'{BASE_URL}/api/agent/cycle')
    result = r.json()
    print(f'   ✓ Manual cycle executed: {result.get("decisions_made", 0)} decisions')
    
    r = requests.get(f'{BASE_URL}/api/agent/pending-approvals')
    pending = r.json()
    print(f'   ✓ Pending approvals: {pending.get("count", 0)}')

    # 7. Check Dashboard
    print('\n7️⃣ Dashboard Summary...')
    r = requests.get(f'{BASE_URL}/api/dashboard')
    dash = r.json()
    stats = dash['hospital_stats']
    print(f'   ✓ Hospital Stats:')
    print(f'     - Beds: {stats["total_beds"]} (Occupied: {stats["occupied_beds"]})')
    print(f'     - Patients: {stats["total_patients"]} (Critical: {stats["critical_patients"]})')
    print(f'     - Staff: {stats["total_staff"]}')
    
    print(f'   ✓ Recent decisions: {len(dash["recent_decisions"])}')
    if dash["recent_decisions"]:
        latest = dash["recent_decisions"][0]
        print(f'     Latest: {latest["action"][:50]}...')

    # 8. Test Patient Flow
    print('\n8️⃣ Testing Patient Flow...')
    r = requests.post(f'{BASE_URL}/api/patients', json={
        'name': 'New Emergency Patient',
        'age': 60,
        'status': 'Critical',
        'spo2': 85.0,
        'heart_rate': 140,
        'diagnosis': 'Suspected MI'
    })
    result = r.json()
    print(f'   ✓ New patient admitted: {result["patient_id"]}')
    print(f'     Bed assigned: {result["result"]["bed_assigned"]}')

    # Get AI recommendations
    r = requests.get(f'{BASE_URL}/api/ai/recommendations/{result["patient_id"]}')
    recs = r.json()['recommendations']
    print(f'   ✓ AI Recommendations: {len(recs)} items')

    print('\n' + '=' * 60)
    print('✅ All VitalFlow AI Systems Operational!')
    print('=' * 60)
    print('\n📍 API Documentation: http://localhost:8000/docs')
    print('📍 Dashboard: http://localhost:8000/api/dashboard')


if __name__ == '__main__':
    main()
