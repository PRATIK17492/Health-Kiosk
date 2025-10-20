import sqlite3
import os

def init_db():
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    
    # Create doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
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
            submission_date TEXT NOT NULL
        )
    ''')
    
    # Insert default doctors if not exists
    cursor.execute("INSERT OR IGNORE INTO doctors (username, password) VALUES ('drjohn', 'password123')")
    cursor.execute("INSERT OR IGNORE INTO doctors (username, password) VALUES ('drsmith', 'password123')")
    
    conn.commit()
    conn.close()

def load_doctors():
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM doctors")
    doctors = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return doctors

def save_doctor(username, password):
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def load_patients():
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
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
    return patients

def save_patient(patient_data):
    conn = sqlite3.connect('healthkiosk.db')
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

def delete_patient(patient_id):
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()

def delete_doctor(username):
    conn = sqlite3.connect('healthkiosk.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctors WHERE username = ?", (username,))
    conn.commit()
    conn.close()