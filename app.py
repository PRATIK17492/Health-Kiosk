from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "healthkiosk_secret_key_2024"  # Needed for session

PATIENTS_FILE = "patients.json"
DOCTORS_FILE = "doctors.json"

def load_patients():
    if os.path.exists(PATIENTS_FILE):
        try:
            with open(PATIENTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_patients(d):
    with open(PATIENTS_FILE, "w") as f:
        json.dump(d, f, indent=2)

def load_doctors():
    if os.path.exists(DOCTORS_FILE):
        try:
            with open(DOCTORS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_doctors(d):
    with open(DOCTORS_FILE, "w") as f:
        json.dump(d, f, indent=2)

@app.route("/")
def index():
    return redirect(url_for("patient"))

# Patient: submit form
@app.route("/patient", methods=["GET", "POST"])
def patient():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        age = request.form.get("age", "").strip()
        weight = request.form.get("weight", "").strip()
        bp = request.form.get("bp", "").strip()
        sugar = request.form.get("sugar", "").strip()
        oxygen = request.form.get("oxygen", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        symptoms = request.form.get("symptoms", "").strip()

        # Check if all fields are filled
        if not all([name, city, age, weight, bp, sugar, oxygen, blood_group, symptoms]):
            return render_template("patient.html", error="Please fill in all fields before submitting!")

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = name.replace(" ", "_") if name else "patient"
        pid = f"{safe_name}_{ts}"

        patients = load_patients()
        patients[pid] = {
            "id": pid,
            "name": name,
            "city": city,
            "age": age,
            "weight": weight,
            "bp": bp,
            "sugar": sugar,
            "oxygen": oxygen,
            "blood_group": blood_group,
            "symptoms": symptoms,
            "prescription": "",
            "timestamp": ts
        }
        save_patients(patients)

        # show success + patient id so doctor can find it
        return render_template("patient.html", message="Submitted successfully!", pid=pid)

    return render_template("patient.html")

# View a specific patient (patient checks their own record and prescription)
@app.route("/patient/view/<pid>")
def patient_view(pid):
    patients = load_patients()
    pdata = patients.get(pid)
    if not pdata:
        return f"No record found for ID: {pid}"
    return render_template("patient_view.html", pdata=pdata)

# Doctor login
@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        
        doctors = load_doctors()
        
        if name in doctors and doctors[name] == password:
            session["doctor_logged_in"] = True
            session["doctor_name"] = name
            return redirect(url_for("doctor_dashboard"))
        else:
            return render_template("doctor_login.html", error="Invalid credentials!")
    
    return render_template("doctor_login.html")

# Doctor registration
@app.route("/doctor/register", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if not name or not password:
            return render_template("doctor_register.html", error="Please fill all fields!")
        
        if password != confirm_password:
            return render_template("doctor_register.html", error="Passwords don't match!")
        
        doctors = load_doctors()
        
        if name in doctors:
            return render_template("doctor_register.html", error="Doctor already exists!")
        
        doctors[name] = password
        save_doctors(doctors)
        
        return render_template("doctor_register.html", success="Registration successful! Please login.")
    
    return render_template("doctor_register.html")

# Doctor dashboard: list all patients
@app.route("/doctor")
def doctor_dashboard():
    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))
    
    patients = load_patients()
    search_query = request.args.get('search', '').strip().lower()
    
    if search_query:
        filtered_patients = {}
        for pid, pdata in patients.items():
            if (search_query in pdata.get('name', '').lower() or 
                search_query in pid.lower() or
                search_query in pdata.get('city', '').lower()):
                filtered_patients[pid] = pdata
        patients = filtered_patients
    
    # sort by newest (reverse alphanumeric of keys works since keys have timestamp)
    patients_sorted = dict(sorted(patients.items(), key=lambda x: x[1].get('timestamp', ''), reverse=True))
    return render_template("doctor.html", patients=patients_sorted, doctor_name=session.get("doctor_name"), search_query=search_query)

# Clear all patient data
@app.route("/doctor/clear", methods=["POST"])
def clear_patients():
    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))
    
    save_patients({})
    return redirect(url_for("doctor_dashboard"))

# Doctor logout
@app.route("/doctor/logout")
def doctor_logout():
    session.clear()
    return redirect(url_for("doctor_login"))

# Doctor view a single patient and add prescription
@app.route("/doctor/patient/<pid>", methods=["GET", "POST"])
def doctor_patient(pid):
    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))
    
    patients = load_patients()
    pdata = patients.get(pid)
    if not pdata:
        return f"No patient found with ID: {pid}"

    if request.method == "POST":
        prescription = request.form.get("prescription", "").strip()
        pdata["prescription"] = prescription
        patients[pid] = pdata
        save_patients(patients)
        return redirect(url_for("doctor_dashboard"))

    return render_template("doctor_patient.html", pdata=pdata)

if __name__ == "__main__":
    # host=0.0.0.0 lets other devices on same Wi-Fi access the server
    app.run(host="0.0.0.0", port=5000, debug=True)