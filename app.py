from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "healthkiosk_secret_key_2024"
socketio = SocketIO(app, cors_allowed_origins="*")

# Data storage
PATIENTS_FILE = "patients_data.json"

def load_patients():
    try:
        if os.path.exists(PATIENTS_FILE):
            with open(PATIENTS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_patients(patients_data):
    try:
        with open(PATIENTS_FILE, 'w') as f:
            json.dump(patients_data, f, indent=2)
        return True
    except:
        return False

# Routes
@app.route('/')
def home():
    return redirect('/patient/welcome')

@app.route('/patient/welcome')
def patient_welcome():
    return render_template('patient_welcome.html')

@app.route('/doctor/welcome')
def doctor_welcome():
    return render_template('doctor_welcome.html')

# Patient Routes
@app.route('/patient', methods=['GET', 'POST'])
def patient():
    patients_data = load_patients()
    
    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        age = request.form.get("age", "").strip()
        weight = request.form.get("weight", "").strip()
        bp = request.form.get("bp", "").strip()
        sugar = request.form.get("sugar", "").strip()
        oxygen = request.form.get("oxygen", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        symptoms = request.form.get("symptoms", "").strip()

        if not all([name, city, age, weight, bp, sugar, oxygen, blood_group, symptoms]):
            return render_template("patient.html", error="Please fill all fields!")

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        pid = f"{name.replace(' ', '_')}_{ts}"

        patients_data[pid] = {
            "id": pid, "name": name, "city": city, "age": age, "weight": weight,
            "bp": bp, "sugar": sugar, "oxygen": oxygen, "blood_group": blood_group,
            "symptoms": symptoms, "prescription": "", "timestamp": ts,
            "status": "waiting", "doctor_name": "", "prescription_date": "",
            "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_patients(patients_data)

        socketio.emit('new_patient_notification', {
            'patient_id': pid,
            'patient_name': name,
            'message': f'New patient {name} submitted form'
        })

        return render_template("patient.html", message="Submitted successfully!", pid=pid)

    return render_template("patient.html")

@app.route('/patient/history')
def patient_history():
    patients_data = load_patients()
    return render_template("patient_history.html", patients=patients_data)

@app.route('/patient/search', methods=['GET', 'POST'])
def patient_search():
    patients_data = load_patients()
    search_results = {}
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get("patient_id", "").strip()
        if search_query:
            for pid, pdata in patients_data.items():
                if search_query.lower() in pid.lower() or search_query.lower() in pdata.get('name', '').lower():
                    search_results[pid] = pdata
    
    return render_template("patient_search.html", patients=search_results, search_query=search_query)

@app.route('/patient/delete/<pid>', methods=['POST'])
def patient_delete(pid):
    patients_data = load_patients()
    if pid in patients_data:
        del patients_data[pid]
        save_patients(patients_data)
    return redirect('/patient/history')

@app.route('/patient/view/<pid>')
def patient_view(pid):
    patients_data = load_patients()
    pdata = patients_data.get(pid)
    if not pdata:
        return "No record found for ID: " + pid, 404
    return render_template("patient_view.html", pdata=pdata)

# Doctor Routes (Fixed login, no registration)
DOCTOR_PASSWORD = "Pratik1714"  # 🔒 Only password to log in
DOCTOR_NAME = "Pratik"  # 🔒 Fixed doctor name

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        password = request.form.get("password", "").strip()

        # ✅ Only one password required for login
        if password == DOCTOR_PASSWORD:
            session['doctor_logged_in'] = True
            session['doctor_name'] = DOCTOR_NAME  # Always set to "Pratik"
            return redirect('/doctor/dashboard')
        else:
            return render_template("doctor_login.html", error="❌ Incorrect password. Access denied!")

    return render_template("doctor_login.html")


# ❌ Disabled registration page
@app.route('/doctor/register')
def doctor_register():
    # Redirect to login instead of showing registration form
    return redirect('/doctor/login')


@app.route('/doctor/dashboard')
def doctor_dashboard():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    patients_data = load_patients()
    waiting_patients = {pid: pdata for pid, pdata in patients_data.items() if pdata.get('status') == 'waiting'}
    
    return render_template("doctor.html", patients=patients_data, waiting_patients=waiting_patients)


@app.route('/doctor/search', methods=['GET', 'POST'])
def doctor_search():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    patients_data = load_patients()
    search_results = {}
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get("patient_id", "").strip()
        if search_query:
            for pid, pdata in patients_data.items():
                if (search_query.lower() in pid.lower() or 
                    search_query.lower() in pdata.get('name', '').lower()):
                    search_results[pid] = pdata
    
    return render_template("doctor_search.html", patients=search_results, search_query=search_query)


@app.route('/doctor/delete/<pid>', methods=['POST'])
def doctor_delete(pid):
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    patients_data = load_patients()
    if pid in patients_data:
        del patients_data[pid]
        save_patients(patients_data)
    return redirect('/doctor/dashboard')


@app.route('/doctor/patient/<pid>', methods=['GET', 'POST'])
def doctor_patient(pid):
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    patients_data = load_patients()
    pdata = patients_data.get(pid)
    if not pdata:
        return "Patient not found: " + pid, 404

    if request.method == 'POST':
        prescription = request.form.get("prescription", "").strip()
        doctor_name = DOCTOR_NAME  # Always use fixed doctor name
        
        if not prescription:
            return render_template("doctor_patient.html", pdata=pdata, error="Please write a prescription!")
        
        prescription_with_info = f"Patient ID: {pid}\nPatient Name: {pdata['name']}\nPrescribed by: Dr. {doctor_name}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n--- PRESCRIPTION ---\n{prescription}"
        
        pdata["prescription"] = prescription_with_info
        pdata["status"] = "prescribed"
        pdata["doctor_name"] = doctor_name
        pdata["prescription_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        patients_data[pid] = pdata
        
        save_patients(patients_data)

        socketio.emit('prescription_notification', {
            'patient_id': pid,
            'patient_name': pdata['name'],
            'doctor_name': doctor_name,
            'message': f'Prescription ready from Dr. {doctor_name}'
        })

        return redirect('/doctor/dashboard')

    return render_template("doctor_patient.html", pdata=pdata)


@app.route('/doctor/logout')
def doctor_logout():
    session.clear()
    return redirect('/doctor/login')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ != "__main__":
    gunicorn_app = app

if __name__ == '__main__':
    print("🚀 Health Kiosk Server Starting...")
    print("📍 Patient Portal: http://127.0.0.1:5000/patient/welcome")
    print("📍 Doctor Portal:  http://127.0.0.1:5000/doctor/welcome")
    print("🔑 Doctor Password: Pratik1714")
    print("👨‍⚕️ Doctor Name: Pratik")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)