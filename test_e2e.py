import urllib.request
import json
from datetime import date, timedelta

print('=== 1. Checking Frontend (Vite) ===')
req_fe = urllib.request.urlopen('http://localhost:5173/')
fe_html = req_fe.read().decode('utf-8')
assert 'MediConnect' in fe_html, 'Frontend title missing'
print('Frontend is UP and serving index.html cleanly!')

print('\n=== 2. Testing Full End-to-End Workflow against Backend ===')
BASE_API = 'http://127.0.0.1:8000/api'

def api_post(path, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        f'{BASE_API}{path}',
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode('utf-8'))

def api_get(path, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(f'{BASE_API}{path}', headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode('utf-8'))

def api_patch(path, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        f'{BASE_API}{path}',
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='PATCH'
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode('utf-8'))

# Step A: Register Patient
patient_email = f'alex_e2e_{int(date.today().strftime("%Y%m%d"))}@testmed.com'
try:
    reg_res = api_post('/auth/register/', {
        'full_name': 'Alex Johnson',
        'email': patient_email,
        'password': 'Password123!',
        'role': 'patient'
    })
    patient_token = reg_res['access']
    print(f'Step A: Registered new patient: {patient_email}')
except Exception:
    # If already registered, log in
    login_res = api_post('/auth/login/', {
        'email': patient_email,
        'password': 'Password123!'
    })
    patient_token = login_res['access']
    print(f'Step A: Patient {patient_email} logged in successfully')

# Step B: Browse Cardiologists
doc_res = api_get('/doctors/?specialization=Cardiologist')
assert doc_res['count'] >= 1
doctor = doc_res['results'][0]
doc_id = doctor['id']
print(f'Step B: Found doctor {doctor["full_name"]} ({doctor["specialization"]}, ID: {doc_id})')

# Step C: Get Available Slots
target_date = (date.today() + timedelta(days=4)).isoformat()
slots_res = api_get(f'/doctors/{doc_id}/slots/?date={target_date}')
free_slots = slots_res['slots']
assert len(free_slots) > 0, 'No free slots available'
chosen_slot = free_slots[0]
print(f'Step C: Selected slot {chosen_slot["start_time"]} on {target_date}')

# Step D: Book Appointment (Patient)
booking_res = api_post('/appointments/', {
    'doctor_id': doc_id,
    'date': target_date,
    'time': chosen_slot['start_time'],
    'slot_id': chosen_slot['id']
}, token=patient_token)
apt_id = booking_res['id']
assert booking_res['status'] == 'pending'
print(f'Step D: Appointment #{apt_id} successfully booked! Status: {booking_res["status"]}')

# Step E: Patient views My Appointments
p_apts = api_get('/appointments/', token=patient_token)
assert any(a['id'] == apt_id for a in p_apts['results'])
print(f'Step E: Patient verified appointment #{apt_id} is in My Appointments list!')

# Step F: Doctor Logs in
doc_login = api_post('/auth/login/', {
    'email': doctor['email'],
    'password': 'Password123!'
})
doc_token = doc_login['access']
print(f'Step F: Doctor {doctor["full_name"]} logged in successfully!')

# Step G: Doctor accepts the appointment
status_update = api_patch(f'/appointments/{apt_id}/status/', {'status': 'accepted'}, token=doc_token)
assert status_update['appointment']['status'] == 'accepted'
print(f'Step G: Doctor accepted appointment #{apt_id} (Status: accepted)')

# Step H: Doctor creates digital prescription
presc_res = api_post(f'/appointments/{apt_id}/prescription/', {
    'medical_notes': 'Cardiovascular evaluation completed. Normal sinus rhythm, blood pressure 118/78 mmHg.',
    'prescription_text': '1. Tab. CoQ10 100mg - 1 capsule daily with morning meal for 30 days.\n2. 30 minutes daily moderate cardiovascular exercise.'
}, token=doc_token)
print(f'Step H: Doctor created prescription for appointment #{apt_id}!')

# Verify appointment moved to completed
updated_apt = api_get(f'/appointments/?status=completed', token=doc_token)
assert any(a['id'] == apt_id for a in updated_apt['results'])
print(f'Step H2: Verified appointment #{apt_id} automatically marked COMPLETED!')

# Step I: Patient views prescription
patient_presc = api_get(f'/appointments/{apt_id}/prescription/', token=patient_token)
assert 'CoQ10' in patient_presc['prescription_text']
assert 'Cardiovascular evaluation' in patient_presc['medical_notes']
print(f'Step I: Patient successfully retrieved and viewed prescription!')
print(f'--- Prescription Content ---')
print(f'Medical Notes: {patient_presc["medical_notes"]}')
print(f'Prescription: {patient_presc["prescription_text"]}')

# Step J: Doctor edits consultation fee
updated_fee_res = api_patch('/doctors/me/', {'consultation_fee': 650.00}, token=doc_token)
assert float(updated_fee_res['doctor']['consultation_fee']) == 650.00
print(f'Step J1: Doctor updated consultation fee to ${updated_fee_res["doctor"]["consultation_fee"]} via /doctors/me/!')

# Verify updated fee reflects in public doctor detail
doctor_public = api_get(f'/doctors/{doc_id}/')
assert float(doctor_public['consultation_fee']) == 650.00
print(f'Step J2: Verified doctor public detail reflects updated fee ${doctor_public["consultation_fee"]}!')

# Verify updated fee reflects in doctors listing
doctors_list = api_get('/doctors/?specialization=Cardiologist')
matching_doc = next(d for d in doctors_list['results'] if d['id'] == doc_id)
assert float(matching_doc['consultation_fee']) == 650.00
print(f'Step J3: Verified doctor listing reflects updated fee ${matching_doc["consultation_fee"]}!')

print('\n>>> ALL END-TO-END FLOW VERIFICATIONS PASSED 100%! <<<')
