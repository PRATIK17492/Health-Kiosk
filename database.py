import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get database path that works on Render"""
    return '/tmp/healthkiosk.db' if 'RENDER' in os.environ else 'healthkiosk.db'

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            age TEXT NOT NULL,
            weight TEXT NOT NULL,
            bp TEXT NOT NULL,
            sugar TEXT NOT NULL,
            oxygen TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            prescription TEXT DEFAULT '',
            status TEXT DEFAULT 'waiting',
            doctor_name TEXT DEFAULT '',
            prescription_date TEXT DEFAULT '',
            submission_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default doctors if not exists
    default_doctors = [
        ('drjohn', 'password123'),
        ('drsmith', 'password123')
    ]
    
    for username, password in default_doctors:
        cursor.execute("INSERT OR IGNORE INTO doctors (username, password) VALUES (?, ?)", (username, password))
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {db_path}")

def load_doctors():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM doctors")
    doctors = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    print(f"📊 Loaded {len(doctors)} doctors from database")
    return doctors

def save_doctor(username, password):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        print(f"✅ Doctor registered: {username}")
        return True
    except sqlite3.IntegrityError:
        conn.close()
        print(f"❌ Doctor already exists: {username}")
        return False

def load_patients():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    patients = {}
    for row in cursor.fetchall():
        patients[row[0]] = {
            "id": row[0], "name": row[1], "city": row[2], "age": row[3], 
            "weight": row[4], "bp": row[5], "sugar": row[6], "oxygen": row[7],
            "blood_group": row[8], "symptoms": row[9], "prescription": row[10],
            "status": row[11], "doctor_name": row[12], "prescription_date": row[13],
            "submission_date": row[14]
        }
    conn.close()
    print(f"📊 Loaded {len(patients)} patients from database")
    return patients

def save_patient(patient_data):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO patients 
        (id, name, city, age, weight, bp, sugar, oxygen, blood_group, symptoms, prescription, status, doctor_name, prescription_date, submission_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_data["id"], patient_data["name"], patient_data["city"], patient_data["age"],
        patient_data["weight"], patient_data["bp"], patient_data["sugar"], patient_data["oxygen"],
        patient_data["blood_group"], patient_data["symptoms"], patient_data["prescription"],
        patient_data["status"], patient_data["doctor_name"], patient_data["prescription_date"],
        patient_data["submission_date"]
    ))
    conn.commit()
    conn.close()
    print(f"✅ Patient saved: {patient_data['name']} ({patient_data['id']})")

def delete_patient(patient_id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    print(f"✅ Patient deleted: {patient_id}")

def delete_doctor(username):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctors WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    print(f"✅ Doctor deleted: {username}")