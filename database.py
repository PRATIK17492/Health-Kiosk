import json
import os
from datetime import datetime

def init_db():
    """Initialize database files if they don't exist"""
    try:
        # Create patients data file if it doesn't exist
        if not os.path.exists('patients_data.json'):
            with open('patients_data.json', 'w') as f:
                json.dump({}, f)
            print("✅ Created patients_data.json")
        
        # Create doctors data file if it doesn't exist  
        if not os.path.exists('doctors_data.json'):
            # Pre-defined doctors only - no registration allowed
            predefined_doctors = {
                "shreyas": "123",
                "drjohn": "password123",
                "drsmith": "password456",
                "drwilson": "health2024",
                "drsarah": "medic123"
            }
            with open('doctors_data.json', 'w') as f:
                json.dump(predefined_doctors, f, indent=2)
            print("✅ Created doctors_data.json with predefined doctors")
        
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def load_doctors():
    """Load predefined doctors from JSON file"""
    try:
        if os.path.exists('doctors_data.json'):
            with open('doctors_data.json', 'r') as f:
                doctors = json.load(f)
                print(f"✅ Loaded {len(doctors)} predefined doctors from file")
                return doctors
        else:
            print("❌ doctors_data.json not found")
            return {}
    except Exception as e:
        print(f"❌ Error loading doctors: {e}")
        return {}

def load_patients():
    """Load patients from JSON file"""
    try:
        if os.path.exists('patients_data.json'):
            with open('patients_data.json', 'r') as f:
                patients = json.load(f)
                print(f"✅ Loaded {len(patients)} patients from file")
                return patients
        else:
            print("❌ patients_data.json not found")
            return {}
    except Exception as e:
        print(f"❌ Error loading patients: {e}")
        return {}

def save_patient(patient_data):
    """Save patient to JSON file"""
    try:
        patients = load_patients()
        
        # Add or update patient
        patient_id = patient_data['id']
        patients[patient_id] = patient_data
        
        # Save to file
        with open('patients_data.json', 'w') as f:
            json.dump(patients, f, indent=2)
        
        print(f"✅ Saved patient: {patient_data['name']} (ID: {patient_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error saving patient: {e}")
        return False

def delete_patient(patient_id):
    """Delete patient from JSON file"""
    try:
        patients = load_patients()
        
        if patient_id in patients:
            del patients[patient_id]
            
            # Save updated data to file
            with open('patients_data.json', 'w') as f:
                json.dump(patients, f, indent=2)
            
            print(f"✅ Deleted patient: {patient_id}")
            return True
        else:
            print(f"❌ Patient not found: {patient_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting patient: {e}")
        return False