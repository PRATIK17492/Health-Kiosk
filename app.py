from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import logging
import json
import os
import random
import base64
import threading
import time

app = Flask(__name__)
app.secret_key = 'healthcare-kiosk-secret-key-2024'
app.config['SESSION_TIMEOUT'] = timedelta(minutes=120)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def update_db_schema():
    """Update database schema to add missing columns"""
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    
    try:
        # Check if doctor_type column exists in doctors table
        cursor.execute("PRAGMA table_info(doctors)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'doctor_type' not in columns:
            print("Adding doctor_type column to doctors table...")
            cursor.execute('ALTER TABLE doctors ADD COLUMN doctor_type TEXT DEFAULT "human"')
            print("doctor_type column added successfully!")
        
        # Update existing records to have doctor_type
        cursor.execute('UPDATE doctors SET doctor_type = "human" WHERE doctor_type IS NULL')
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
    finally:
        conn.close()

# Database setup
def init_db():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            village TEXT,
            age INTEGER,
            gender TEXT,
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            temperature REAL,
            pulse INTEGER,
            sugar INTEGER,
            oxygen INTEGER,
            symptoms TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            emergency_flag BOOLEAN DEFAULT FALSE,
            prescription TEXT,
            prescription_date DATETIME,
            prescribed_by TEXT,
            status TEXT DEFAULT 'pending',
            patient_type TEXT DEFAULT 'human'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT UNIQUE NOT NULL,
            owner_name TEXT,
            owner_phone TEXT,
            animal_type TEXT,
            animal_breed TEXT,
            animal_age TEXT,
            animal_gender TEXT,
            symptoms TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            emergency_flag BOOLEAN DEFAULT FALSE,
            prescription TEXT,
            prescription_date DATETIME,
            prescribed_by TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            specialization TEXT,
            email TEXT,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            doctor_type TEXT DEFAULT 'human'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            doctor_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender_type TEXT NOT NULL,
            image_data TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            type TEXT
        )
    ''')
    
    # Insert sample data
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        doctors = [
            ('doctor', 'password123', 'Dr. Smith', 'General Medicine', 'doctor@healthcare.com', 'human'),
            ('vet', 'password123', 'Dr. Johnson', 'Veterinary', 'vet@healthcare.com', 'animal')
        ]
        cursor.executemany(
            "INSERT INTO doctors (username, password, name, specialization, email, doctor_type) VALUES (?, ?, ?, ?, ?, ?)",
            doctors
        )
    
    cursor.execute("SELECT COUNT(*) FROM emergency_contacts")
    if cursor.fetchone()[0] == 0:
        contacts = [
            ('Ambulance Service', '108', 'emergency'),
            ('Local Clinic', '+91-1234567890', 'clinic'),
            ('Health Center', '+91-9876543210', 'health_center')
        ]
        cursor.executemany(
            "INSERT INTO emergency_contacts (name, phone_number, type) VALUES (?, ?, ?)",
            contacts
        )
    
    conn.commit()
    conn.close()
    
    # Update schema for existing databases
    update_db_schema()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('healthcare.db')
    conn.row_factory = sqlite3.Row
    return conn

# Translation dictionaries
translations = {
    'en': {
        # Common
        'welcome': 'Welcome',
        'back': 'Back',
        'submit': 'Submit',
        'cancel': 'Cancel',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'save': 'Save',
        'refresh': 'Refresh',
        'minutes': 'minutes',
        'estimated_wait': 'Estimated Wait Time',
        
        # Patient Welcome
        'health_assessment': 'Health Assessment',
        'view_history': 'View History',
        'animal_health': 'Animal Health',
        'emergency_sos': 'Emergency SOS',
        'patient_queue': 'Patient Queue',
        'chat_with_doctor': 'Chat with Doctor',
        'check_health': 'Check Health',
        
        # Patient Form
        'village_name': 'Village Name',
        'age': 'Age',
        'gender': 'Gender',
        'male': 'Male',
        'female': 'Female',
        'other': 'Other',
        'blood_pressure': 'Blood Pressure',
        'systolic': 'Systolic',
        'diastolic': 'Diastolic',
        'temperature': 'Temperature',
        'pulse': 'Pulse',
        'blood_sugar': 'Blood Sugar',
        'oxygen': 'Oxygen',
        'symptoms': 'Symptoms',
        'describe_symptoms': 'Describe your symptoms in detail...',
        'network_error': 'Network error. Please check your connection and try again.',
        
        # Animal Form
        'owner_name': 'Owner Name',
        'owner_phone': 'Owner Phone',
        'animal_type': 'Animal Type',
        'animal_breed': 'Animal Breed',
        'animal_age': 'Animal Age',
        'animal_gender': 'Animal Gender',
        'animal_symptoms': 'Animal Symptoms',
        'animal_submitted': 'Your animal health assessment has been submitted to our veterinary team.',
        'vet_review': 'Our veterinary doctors will review your case and provide a prescription shortly.',
        'chat_with_vet': 'Chat with Veterinarian',
        'next_steps': 'Next Steps',
        'save_id': 'Save this ID to access your records and prescriptions',
        'animal_id': 'Animal ID',
        'check_prescription': 'Check Prescription Status',
        'data_usage': 'Your data will be used anonymously to improve local health services.',
        'emergency_confirm': 'Are you sure you want to trigger emergency alert? Help will be notified immediately.',
        'emergency_sent': 'Emergency alert sent! Help is on the way',
        'emergency_failed': 'Emergency alert failed. Please call 108 directly.',
        'complete_assessment': 'Please complete a health assessment first',
        
        # Doctor
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'password': 'Password',
        'specialization': 'Specialization',
        'human_doctor': 'Human Doctor',
        'veterinary_doctor': 'Veterinary Doctor',
        'doctor_portal': 'Dedicated Healthcare Professionals Platform',
        'doctor_quote': 'The good physician treats the disease; the great physician treats the patient who has the disease',
        'doctor_author': 'William Osler',
        'existing_doctors': 'Existing Doctors',
        'existing_doctors_desc': 'Access your medical dashboard to manage patient queues, review cases, and provide prescriptions',
        'new_doctors': 'New Doctors',
        'new_doctors_desc': 'Join our healthcare network to serve patients through our advanced kiosk system',
        'back_to_patient': 'Back to Patient Portal',
        'registered_doctors': 'Registered Doctors',
        'patients_served': 'Patients Served',
        'available': 'Available',
        
        # Queue
        'your_turn': 'Your Turn',
        'you_are_next': "You're Next",
        'please_wait': 'Please Wait',
        'patients_ahead': 'patients ahead of you',
        
        # Chat
        'send_message': 'Send Message',
        'type_message': 'Type your message...',
        'take_photo': 'Take Photo',
        'attach_photo': 'Attach Photo',
        'select_doctor': 'Select Doctor',
        'write_prescription': 'Write Prescription',
        'prescription_saved': 'Prescription saved successfully',
        
        # Prescription
        'prescription': 'Prescription',
        'download_prescription': 'Download Prescription',
        'print_prescription': 'Print Prescription',
        'prescribed_by': 'Prescribed by',
        'prescription_date': 'Prescription Date',
        'pending_prescription': 'Pending Prescription',
        'prescription_arrived': 'Prescription Arrived',
        
        # Status
        'pending': 'Pending',
        'prescribed': 'Prescribed',
        'emergency': 'Emergency',
        
        # NEW TRANSLATION KEYS ADDED
        'logout': 'Logout',
        'chat_with_patients': 'Chat with Patients',
        'select_patient': 'Select a Patient',
        'select_patient_to_chat': 'Select a patient to start chatting',
        'no_chat_selected': 'No Chat Selected',
        'select_patient_to_start_chat': 'Select a patient from the list to start chatting',
        'capture': 'Capture',
        'no_patients_available': 'No patients available for chat',
        'chat_with_vet': 'Chat with Veterinarian',
    },
    
    'hi': {
        # Common
        'welcome': 'स्वागत है',
        'back': 'वापस',
        'submit': 'जमा करें',
        'cancel': 'रद्द करें',
        'loading': 'लोड हो रहा है...',
        'error': 'त्रुटि',
        'success': 'सफलता',
        'save': 'सेव',
        'refresh': 'रिफ्रेश',
        'minutes': 'मिनट',
        'estimated_wait': 'अनुमानित प्रतीक्षा समय',
        
        # Patient Welcome
        'health_assessment': 'स्वास्थ्य मूल्यांकन',
        'view_history': 'इतिहास देखें',
        'animal_health': 'पशु स्वास्थ्य',
        'emergency_sos': 'आपातकालीन एसओएस',
        'patient_queue': 'मरीज कतार',
        'chat_with_doctor': 'डॉक्टर से चैट करें',
        'check_health': 'स्वास्थ्य जांच',
        
        # Patient Form
        'village_name': 'गाँव का नाम',
        'age': 'उम्र',
        'gender': 'लिंग',
        'male': 'पुरुष',
        'female': 'महिला',
        'other': 'अन्य',
        'blood_pressure': 'रक्तचाप',
        'systolic': 'सिस्टोलिक',
        'diastolic': 'डायस्टोलिक',
        'temperature': 'तापमान',
        'pulse': 'नब्ज',
        'blood_sugar': 'ब्लड शुगर',
        'oxygen': 'ऑक्सीजन',
        'symptoms': 'लक्षण',
        'describe_symptoms': 'अपने लक्षणों का विस्तार से वर्णन करें...',
        'network_error': 'नेट्वर्क त्रुटि। कृपया अपना कनेक्शन जांचें और पुनः प्रयास करें।',
        
        # Animal Form
        'owner_name': 'मालिक का नाम',
        'owner_phone': 'मालिक का फोन',
        'animal_type': 'पशु प्रकार',
        'animal_breed': 'पशु नस्ल',
        'animal_age': 'पशु की उम्र',
        'animal_gender': 'पशु लिंग',
        'animal_symptoms': 'पशु के लक्षण',
        'animal_submitted': 'आपका पशु स्वास्थ्य मूल्यांकन हमारी पशु चिकित्सा टीम को भेज दिया गया है।',
        'vet_review': 'हमारे पशु चिकित्सक आपके मामले की समीक्षा करेंगे और जल्द ही एक पर्चा प्रदान करेंगे।',
        'chat_with_vet': 'पशु चिकित्सक से चैट करें',
        'next_steps': 'अगले कदम',
        'save_id': 'अपने रिकॉर्ड और पर्चे तक पहुंचने के लिए इस आईडी को सहेजें',
        'animal_id': 'पशु आईडी',
        'check_prescription': 'पर्चा स्थिति जांचें',
        'data_usage': 'आपका डेटा गुमनाम रूप से स्थानीय स्वास्थ्य सेवाओं में सुधार के लिए उपयोग किया जाएगा।',
        'emergency_confirm': 'क्या आप वाकई आपातकालीन अलर्ट ट्रिगर करना चाहते हैं? मदद तुरंत सूचित की जाएगी।',
        'emergency_sent': 'आपातकालीन अलर्ट भेजा गया! मदद रास्ते में है',
        'emergency_failed': 'आपातकालीन अलर्ट विफल। कृपया सीधे 108 पर कॉल करें।',
        'complete_assessment': 'कृपया पहले एक स्वास्थ्य मूल्यांकन पूरा करें',
        
        # Doctor
        'login': 'लॉगिन',
        'register': 'पंजीकरण',
        'username': 'उपयोगकर्ता नाम',
        'password': 'पासवर्ड',
        'specialization': 'विशेषज्ञता',
        'human_doctor': 'मानव डॉक्टर',
        'veterinary_doctor': 'पशु चिकित्सक',
        'doctor_portal': 'समर्पित स्वास्थ्य देखभाल पेशेवर प्लेटफॉर्म',
        'doctor_quote': 'अच्छा चिकित्सक बीमारी का इलाज करता है; महान चिकित्सक उस रोगी का इलाज करता है जिसे बीमारी है',
        'doctor_author': 'विलियम ओस्लर',
        'existing_doctors': 'मौजूदा डॉक्टर',
        'existing_doctors_desc': 'रोगी कतारों को प्रबंधित करने, मामलों की समीक्षा करने और पर्चे प्रदान करने के लिए अपने मेडिकल डैशबोर्ड तक पहुंचें',
        'new_doctors': 'नए डॉक्टर',
        'new_doctors_desc': 'हमारे उन्नत कियोस्क सिस्टम के माध्यम से रोगियों की सेवा करने के लिए हमारे स्वास्थ्य देखभाल नेटवर्क में शामिल हों',
        'back_to_patient': 'रोगी पोर्टल पर वापस जाएं',
        'registered_doctors': 'पंजीकृत डॉक्टर',
        'patients_served': 'सेवा प्राप्त रोगी',
        'available': 'उपलब्ध',
        
        # Queue
        'your_turn': 'आपकी बारी',
        'you_are_next': 'आप अगले हैं',
        'please_wait': 'कृपया प्रतीक्षा करें',
        'patients_ahead': 'मरीज आपके आगे हैं',
        
        # Chat
        'send_message': 'संदेश भेजें',
        'type_message': 'अपना संदेश टाइप करें...',
        'take_photo': 'फोटो लें',
        'attach_photo': 'फोटो संलग्न करें',
        'select_doctor': 'डॉक्टर चुनें',
        'write_prescription': 'पर्चा लिखें',
        'prescription_saved': 'पर्चा सफलतापूर्वक सहेजा गया',
        
        # Prescription
        'prescription': 'पर्चा',
        'download_prescription': 'पर्चा डाउन्लोड करें',
        'print_prescription': 'पर्चा प्रिंट करें',
        'prescribed_by': 'द्वारा निर्धारित',
        'prescription_date': 'पर्चा तिथि',
        'pending_prescription': 'लंबित पर्चा',
        'prescription_arrived': 'पर्चा आ गया',
        
        # Status
        'pending': 'लंबित',
        'prescribed': 'निर्धारित',
        'emergency': 'आपातकाल',
        
        # NEW TRANSLATION KEYS ADDED
        'logout': 'लॉगआउट',
        'chat_with_patients': 'रोगियों के साथ चैट करें',
        'select_patient': 'एक रोगी चुनें',
        'select_patient_to_chat': 'चैटिंग शुरू करने के लिए एक रोगी चुनें',
        'no_chat_selected': 'कोई चैट चयनित नहीं',
        'select_patient_to_start_chat': 'चैटिंग शुरू करने के लिए सूची से एक रोगी चुनें',
        'capture': 'कैप्चर करें',
        'no_patients_available': 'चैट के लिए कोई रोगी उपलब्ध नहीं',
        'chat_with_vet': 'पशु चिकित्सक से चैट करें',
    },
    
    'kn': {
        # Common
        'welcome': 'ಸ್ವಾಗತ',
        'back': 'ಹಿಂದೆ',
        'submit': 'ಸಲ್ಲಿಸು',
        'cancel': 'ರದ್ದುಮಾಡು',
        'loading': 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...',
        'error': 'ದೋಷ',
        'success': 'ಯಶಸ್ಸು',
        'save': 'ಉಳಿಸಿ',
        'refresh': 'ರಿಫ್ರೆಶ್',
        'minutes': 'ನಿಮಿಷಗಳು',
        'estimated_wait': 'ಅಂದಾಜು ಕಾಯುವ ಸಮಯ',
        
        # Patient Welcome
        'health_assessment': 'ಆರೋಗ್ಯ ಮೌಲ್ಯಮಾಪನ',
        'view_history': 'ಇತಿಹಾಸ ನೋಡಿ',
        'animal_health': 'ಪ್ರಾಣಿ ಆರೋಗ್ಯ',
        'emergency_sos': 'ಅತ್ಯಾಹಿತ ಎಸ್ಒಎಸ್',
        'patient_queue': 'ರೋಗಿ ಕ್ಯೂ',
        'chat_with_doctor': 'ಡಾಕ್ಟರ್ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ',
        'check_health': 'ಆರೋಗ್ಯ ಪರಿಶೀಲಿಸಿ',
        
        # Patient Form
        'village_name': 'ಗ್ರಾಮದ ಹೆಸರು',
        'age': 'ವಯಸ್ಸು',
        'gender': 'ಲಿಂಗ',
        'male': 'ಪುರುಷ',
        'female': 'ಮಹಿಳೆ',
        'other': 'ಇತರೆ',
        'blood_pressure': 'ರಕ್ತದೊತ್ತಡ',
        'systolic': 'ಸಿಸ್ಟೋಲಿಕ್',
        'diastolic': 'ಡಯಾಸ್ಟೋಲಿಕ್',
        'temperature': 'ತಾಪಮಾನ',
        'pulse': 'ನಾಡಿ',
        'blood_sugar': 'ಬ್ಲಡ್ ಸುಗರ್',
        'oxygen': 'ಆಕ್ಸಿಜನ್',
        'symptoms': 'ಲಕ್ಷಣಗಳು',
        'describe_symptoms': 'ನಿಮ್ಮ ಲಕ್ಷಣಗಳನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ...',
        'network_error': 'ನೆಟ್ವರ್ಕ್ ದೋಷ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಕನೆಕ್ಷನ್ ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
        
        # Animal Form
        'owner_name': 'ಮಾಲೀಕರ ಹೆಸರು',
        'owner_phone': 'ಮಾಲೀಕರ ಫೋನ್',
        'animal_type': 'ಪ್ರಾಣಿ ಪ್ರಕಾರ',
        'animal_breed': 'ಪ್ರಾಣಿ ಜಾತಿ',
        'animal_age': 'ಪ್ರಾಣಿಯ ವಯಸ್ಸು',
        'animal_gender': 'ಪ್ರಾಣಿ ಲಿಂಗ',
        'animal_symptoms': 'ಪ್ರಾಣಿಯ ಲಕ್ಷಣಗಳು',
        'animal_submitted': 'ನಿಮ್ಮ ಪ್ರಾಣಿ ಆರೋಗ್ಯ ಮೌಲ್ಯಮಾಪನ ನಮ್ಮ ಪಶುವೈದ್ಯಕೀಯ ತಂಡಕ್ಕೆ ಸಲ್ಲಿಸಲಾಗಿದೆ.',
        'vet_review': 'ನಮ್ಮ ಪಶುವೈದ್ಯರು ನಿಮ್ಮ ಪ್ರಕರಣವನ್ನು ಪರಿಶೀಲಿಸುತ್ತಾರೆ ಮತ್ತು ಶೀಘ್ರದಲ್ಲೇ ಒಂದು ಪರ್ಚಿ ಒದಗಿಸುತ್ತಾರೆ.',
        'chat_with_vet': 'ಪಶುವೈದ್ಯರೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ',
        'next_steps': 'ಮುಂದಿನ ಹಂತಗಳು',
        'save_id': 'ನಿಮ್ಮ ರೆಕಾರ್ಡ್ಗಳು ಮತ್ತು ಪರ್ಚಿಗಳನ್ನು ಪ್ರವೇಶಿಸಲು ಈ ಐಡಿಯನ್ನು ಉಳಿಸಿ',
        'animal_id': 'ಪ್ರಾಣಿ ಐಡಿ',
        'check_prescription': 'ಪರ್ಚಿ ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸಿ',
        'data_usage': 'ನಿಮ್ಮ ಡೇಟಾ ಅನಾಮಧೇಯವಾಗಿ ಸ್ಥಳೀಯ ಆರೋಗ್ಯ ಸೇವೆಗಳನ್ನು ಸುಧಾರಿಸಲು ಬಳಸಲಾಗುತ್ತದೆ.',
        'emergency_confirm': 'ನೀವು ಖಚಿತವಾಗಿ ಅತ್ಯಾಹಿತ ಎಚ್ಚರಿಕೆಯನ್ನು ಪ್ರಚೋದಿಸಲು ಬಯಸುವಿರಾ? ಸಹಾಯ ತಕ್ಷಣವೇ ತಿಳಿಸಲಾಗುವುದು.',
        'emergency_sent': 'ಅತ್ಯಾಹಿತ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಲಾಗಿದೆ! ಸಹಾಯ ದಾರಿಯಲ್ಲಿದೆ',
        'emergency_failed': 'ಅತ್ಯಾಹಿತ ಎಚ್ಚರಿಕೆ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ನೇರವಾಗಿ 108 ಗೆ ಕರೆ ಮಾಡಿ.',
        'complete_assessment': 'ದಯವಿಟ್ಟು ಮೊದಲು ಆರೋಗ್ಯ ಮೌಲ್ಯಮಾಪನವನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ',
        
        # Doctor
        'login': 'ಲಾಗಿನ್',
        'register': 'ನೋಂದಣಿ',
        'username': 'ಬಳಕೆದಾರ ಹೆಸರು',
        'password': 'ಪಾಸ್ವರ್ಡ್',
        'specialization': 'ವಿಶೇಷತೆ',
        'human_doctor': 'ಮಾನವ ಡಾಕ್ಟರ್',
        'veterinary_doctor': 'ಪಶುವೈದ್ಯ',
        'doctor_portal': 'ಸಮರ್ಪಿತ ಆರೋಗ್ಯ ರಕ್ಷಣಾ ವೃತ್ತಿಪರರ ವೇದಿಕೆ',
        'doctor_quote': 'ಉತ್ತಮ ವೈದ್ಯನು ರೋಗವನ್ನು ಚಿಕಿತ್ಸೆ ಮಾಡುತ್ತಾನೆ; ಮಹಾನ್ ವೈದ್ಯನು ರೋಗ ಹೊಂದಿರುವ ರೋಗಿಯನ್ನು ಚಿಕಿತ್ಸೆ ಮಾಡುತ್ತಾನೆ',
        'doctor_author': 'ವಿಲಿಯಂ ಓಸ್ಲರ್',
        'existing_doctors': 'ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ವೈದ್ಯರು',
        'existing_doctors_desc': 'ರೋಗಿ ಕ್ಯೂಗಳನ್ನು ನಿರ್ವಹಿಸಲು, ಪ್ರಕರಣಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಮತ್ತು ಪರ್ಚಿಗಳನ್ನು ಒದಗಿಸಲು ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ಡ್ಯಾಶ್ಬೋರ್ಡ್ಗೆ ಪ್ರವೇಶಿಸಿ',
        'new_doctors': 'ಹೊಸ ವೈದ್ಯರು',
        'new_doctors_desc': 'ನಮ್ಮ ಸುಧಾರಿತ ಕಿಯೋಸ್ಕ್ ವ್ಯವಸ್ಥೆಯ ಮೂಲಕ ರೋಗಿಗಳಿಗೆ ಸೇವೆ ಸಲ್ಲಿಸಲು ನಮ್ಮ ಆರೋಗ್ಯ ರಕ್ಷಣಾ ನೆಟ್ವರ್ಕ್ಗೆ ಸೇರಿಕೊಳ್ಳಿ',
        'back_to_patient': 'ರೋಗಿ ಪೋರ್ಟಲ್ಗೆ ಹಿಂತಿರುಗಿ',
        'registered_doctors': 'ನೋಂದಾಯಿತ ವೈದ್ಯರು',
        'patients_served': 'ಸೇವೆ ಸಲ್ಲಿಸಿದ ರೋಗಿಗಳು',
        'available': 'ಲಭ್ಯವಿದೆ',
        
        # Queue
        'your_turn': 'ನಿಮ್ಮ ಸರದಿ',
        'you_are_next': 'ನೀವು ಮುಂದಿನವರು',
        'please_wait': 'ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ',
        'patients_ahead': 'ರೋಗಿಗಳು ನಿಮ್ಮ ಮುಂದಿದ್ದಾರೆ',
        
        # Chat
        'send_message': 'ಸಂದೇಶ ಕಳುಹಿಸಿ',
        'type_message': 'ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ...',
        'take_photo': 'ಫೋಟೋ ತೆಗೆಯಿರಿ',
        'attach_photo': 'ಫೋಟೋ ಅಟ್ಯಾಚ್ ಮಾಡಿ',
        'select_doctor': 'ಡಾಕ್ಟರ್ ಆಯ್ಕೆಮಾಡಿ',
        'write_prescription': 'ಪರ್ಚಿ ಬರೆಯಿರಿ',
        'prescription_saved': 'ಪರ್ಚಿ ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ',
        
        # Prescription
        'prescription': 'ಪರ್ಚಿ',
        'download_prescription': 'ಪರ್ಚಿ ಡೌನ್ಲೋಡ್ ಮಾಡಿ',
        'print_prescription': 'ಪರ್ಚಿ ಮುದ್ರಿಸಿ',
        'prescribed_by': 'ಇವರಿಂದ ನಿರ್ದೇಶಿಸಲಾಗಿದೆ',
        'prescription_date': 'ಪರ್ಚಿ ದಿನಾಂಕ',
        'pending_prescription': 'ಬಾಕಿ ಇರುವ ಪರ್ಚಿ',
        'prescription_arrived': 'ಪರ್ಚಿ ಬಂದಿದೆ',
        
        # Status
        'pending': 'ಬಾಕಿ',
        'prescribed': 'ನಿರ್ದೇಶಿಸಲಾಗಿದೆ',
        'emergency': 'ಅತ್ಯಾಹಿತ',
        
        # NEW TRANSLATION KEYS ADDED
        'logout': 'ಲಾಗ್ ಔಟ್',
        'chat_with_patients': 'ರೋಗಿಗಳೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ',
        'select_patient': 'ರೋಗಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'select_patient_to_chat': 'ಚಾಟಿಂಗ್ ಪ್ರಾರಂಭಿಸಲು ರೋಗಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'no_chat_selected': 'ಯಾವುದೇ ಚಾಟ್ ಆಯ್ಕೆ ಮಾಡಲಾಗಿಲ್ಲ',
        'select_patient_to_start_chat': 'ಚಾಟಿಂಗ್ ಪ್ರಾರಂಭಿಸಲು ಪಟ್ಟಿಯಿಂದ ರೋಗಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'capture': 'ಕ್ಯಾಪ್ಚರ್ ಮಾಡಿ',
        'no_patients_available': 'ಚಾಟ್ ಗಾಗಿ ಯಾವುದೇ ರೋಗಿಗಳು ಲಭ್ಯವಿಲ್ಲ',
        'chat_with_vet': 'ಪಶುವೈದ್ಯರೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ'
    }
}

def get_translation(lang, key):
    return translations.get(lang, translations['en']).get(key, key)

# Safety Monitor Class
class SafetyMonitor:
    def __init__(self, app):
        self.app = app
        self.last_health_check = datetime.now()
        self.system_status = {
            'online': True,
            'hardware_errors': [],
            'network_status': 'connected',
            'last_sync': datetime.now(),
            'start_time': datetime.now()
        }
    
    def validate_vitals(self, vitals_data):
        limits = {
            'bpSystolic': (50, 250),
            'bpDiastolic': (30, 180),
            'temperature': (35, 42),
            'pulse': (30, 200),
            'sugar': (50, 500),
            'oxygen': (70, 100)
        }
        
        for vital, value in vitals_data.items():
            if vital in limits and value is not None:
                min_val, max_val = limits[vital]
                if not (min_val <= value <= max_val):
                    return False
        return True
    
    def check_emergency_conditions(self, vitals_data):
        emergencies = []
        if vitals_data.get('bpSystolic', 0) > 180 or vitals_data.get('bpDiastolic', 0) > 120:
            emergencies.append("Hypertensive Crisis")
        if vitals_data.get('bpSystolic', 0) < 90 or vitals_data.get('bpDiastolic', 0) < 60:
            emergencies.append("Hypotensive Emergency")
        if vitals_data.get('oxygen', 0) < 90:
            emergencies.append("Low Oxygen Emergency")
        if vitals_data.get('sugar', 0) > 400:
            emergencies.append("Hyperglycemia Emergency")
        if vitals_data.get('sugar', 0) < 70:
            emergencies.append("Hypoglycemia Emergency")
        if vitals_data.get('temperature', 0) > 39.5:
            emergencies.append("High Fever Emergency")
        return emergencies
    
    def send_emergency_alert(self, emergency_data):
        logging.info(f"EMERGENCY ALERT SENT: {emergency_data}")
        return True
    
    def is_online(self):
        return True
    
    def get_system_status(self):
        return {
            **self.system_status,
            'uptime': str(datetime.now() - self.system_status['start_time']).split('.')[0],
            'last_health_check': self.last_health_check.isoformat()
        }
    
    def run_health_check(self):
        self.last_health_check = datetime.now()
        return {
            'sensors': {'healthy': True, 'message': 'All sensors OK'},
            'network': {'healthy': True, 'message': 'Network connected'},
            'storage': {'healthy': True, 'message': 'Storage OK'},
            'temperature': {'healthy': True, 'message': 'Temperature normal'},
            'power': {'healthy': True, 'message': 'Power OK'}
        }

# AI Analytics Class
class AIAnalytics:
    def __init__(self):
        self.disease_patterns = self._load_disease_patterns()
    
    def _load_disease_patterns(self):
        return {
            'common_cold': {
                'symptoms': ['cough', 'fever', 'headache', 'runny nose', 'sore throat'],
                'urgency': 'low'
            },
            'flu': {
                'symptoms': ['fever', 'body ache', 'headache', 'cough', 'fatigue'],
                'urgency': 'medium'
            },
            'hypertension': {
                'symptoms': ['headache', 'dizziness', 'chest pain'],
                'vitals': ['high_bp'],
                'urgency': 'high'
            },
            'diabetes': {
                'symptoms': ['frequent urination', 'thirst', 'fatigue'],
                'vitals': ['high_sugar'],
                'urgency': 'medium'
            }
        }
    
    def analyze_symptoms(self, patient_data):
        try:
            symptoms = patient_data.get('symptoms', '').lower()
            vitals = self._extract_vitals_status(patient_data)
            matched_conditions = self._match_conditions(symptoms, vitals)
            confidence = self._calculate_confidence(matched_conditions)
            recommendations = self._generate_recommendations(matched_conditions, vitals)
            
            return {
                'matched_conditions': matched_conditions,
                'confidence': confidence,
                'recommendations': recommendations,
                'urgency': self._determine_urgency(matched_conditions),
                'disclaimer': 'AI suggestions are supportive, not diagnostic. Please consult doctor.'
            }
        except Exception as e:
            return self._get_fallback_suggestions()
    
    def _extract_vitals_status(self, patient_data):
        status = {}
        if patient_data.get('bpSystolic', 0) > 140 or patient_data.get('bpDiastolic', 0) > 90:
            status['high_bp'] = True
        if patient_data.get('sugar', 0) > 200:
            status['high_sugar'] = True
        if patient_data.get('oxygen', 0) < 95:
            status['low_oxygen'] = True
        return status
    
    def _match_conditions(self, symptoms_text, vitals_status):
        matched = []
        for condition, pattern in self.disease_patterns.items():
            score = 0
            symptom_matches = sum(1 for symptom in pattern['symptoms'] if symptom in symptoms_text)
            if symptom_matches > 0:
                score += symptom_matches / len(pattern['symptoms'])
            if 'vitals' in pattern:
                vital_matches = sum(1 for vital in pattern['vitals'] if vital in vitals_status)
                if vital_matches > 0:
                    score += vital_matches / len(pattern['vitals'])
            if score > 0.3:
                matched.append({
                    'condition': condition.replace('_', ' ').title(),
                    'confidence': min(score, 0.95),
                    'urgency': pattern['urgency']
                })
        return sorted(matched, key=lambda x: x['confidence'], reverse=True)[:3]
    
    def _calculate_confidence(self, matched_conditions):
        if not matched_conditions:
            return 0.0
        return matched_conditions[0]['confidence']
    
    def _generate_recommendations(self, matched_conditions, vitals_status):
        recommendations = ["Rest and maintain proper hydration", "Monitor your symptoms regularly"]
        
        for condition in matched_conditions:
            condition_name = condition['condition'].lower()
            if 'cold' in condition_name:
                recommendations.append("Take rest and use steam inhalation")
            elif 'flu' in condition_name:
                recommendations.append("Get adequate rest and stay hydrated")
            elif 'hypertension' in condition_name or 'high_bp' in vitals_status:
                recommendations.append("Monitor blood pressure regularly")
                recommendations.append("Reduce salt intake and avoid stress")
            elif 'diabetes' in condition_name or 'high_sugar' in vitals_status:
                recommendations.append("Monitor blood sugar levels")
                recommendations.append("Follow diabetic diet plan")
        
        if any(cond['urgency'] == 'high' for cond in matched_conditions):
            recommendations.append("🚨 SEEK IMMEDIATE MEDICAL ATTENTION")
        
        return recommendations
    
    def _determine_urgency(self, matched_conditions):
        if not matched_conditions:
            return 'low'
        urgencies = [cond['urgency'] for cond in matched_conditions]
        if 'high' in urgencies:
            return 'high'
        elif 'medium' in urgencies:
            return 'medium'
        else:
            return 'low'
    
    def _get_fallback_suggestions(self):
        return {
            'matched_conditions': [],
            'confidence': 0.0,
            'recommendations': [
                "Please consult with a healthcare provider",
                "Monitor your symptoms",
                "Rest and maintain hydration"
            ],
            'urgency': 'low',
            'disclaimer': 'Basic assessment only. Please consult doctor for proper diagnosis.'
        }
    
    def get_trends_analytics(self):
        conn = get_db_connection()
        
        total_patients = conn.execute("SELECT COUNT(*) FROM patient_records").fetchone()[0]
        emergency_cases = conn.execute("SELECT COUNT(*) FROM patient_records WHERE emergency_flag = 1").fetchone()[0]
        
        # Generate disease frequency
        disease_frequency = {}
        records = conn.execute("SELECT symptoms, bp_systolic, sugar FROM patient_records").fetchall()
        
        for record in records:
            symptoms = record['symptoms'] or ''
            symptoms_lower = symptoms.lower()
            
            if any(symptom in symptoms_lower for symptom in ['cough', 'cold', 'runny nose']):
                disease_frequency['Common Cold'] = disease_frequency.get('Common Cold', 0) + 1
            if any(symptom in symptoms_lower for symptom in ['fever', 'body ache', 'fatigue']):
                disease_frequency['Flu'] = disease_frequency.get('Flu', 0) + 1
            if record['bp_systolic'] and record['bp_systolic'] > 140:
                disease_frequency['Hypertension'] = disease_frequency.get('Hypertension', 0) + 1
            if record['sugar'] and record['sugar'] > 200:
                disease_frequency['Diabetes'] = disease_frequency.get('Diabetes', 0) + 1
        
        conn.close()
        
        return {
            'disease_frequency': disease_frequency,
            'total_patients': total_patients,
            'emergency_cases': emergency_cases
        }

# Initialize components
safety_monitor = SafetyMonitor(app)
ai_analytics = AIAnalytics()

# Setup logging
logging.basicConfig(level=logging.INFO)

def generate_patient_id():
    return f"PAT{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

def generate_animal_id():
    return f"ANI{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

def get_language():
    return session.get('language', 'en')

# Helper function for getting last message time
def get_last_message_time(conn, patient_id, doctor_id):
    last_message = conn.execute('''
        SELECT timestamp 
        FROM messages 
        WHERE patient_id = ? AND doctor_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''', (patient_id, doctor_id)).fetchone()
    
    if last_message:
        return last_message['timestamp']
    return None

# Routes
@app.route('/')
def welcome():
    lang = get_language()
    return render_template('patient_welcome.html', lang=lang, t=get_translation)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'hi', 'kn']:
        session['language'] = lang
    return redirect(request.referrer or '/')

@app.route('/patient/form')
def patient_form():
    lang = get_language()
    return render_template('patient_form.html', lang=lang, t=get_translation)

@app.route('/animal/form')
def animal_form():
    lang = get_language()
    return render_template('animal_form.html', lang=lang, t=get_translation)

@app.route('/patient/history')
def patient_history():
    lang = get_language()
    return render_template('patient_history.html', lang=lang, t=get_translation)

@app.route('/patient/queue')
def patient_queue():
    lang = get_language()
    return render_template('patient_queue.html', lang=lang, t=get_translation)

@app.route('/patient/chat')
def patient_chat():
    lang = get_language()
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors WHERE doctor_type = "human"').fetchall()
    conn.close()
    return render_template('patient_chat.html', lang=lang, t=get_translation, doctors=doctors)

@app.route('/animal/chat')
def animal_chat():
    lang = get_language()
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors WHERE doctor_type = "animal"').fetchall()
    conn.close()
    return render_template('animal_chat.html', lang=lang, t=get_translation, doctors=doctors)

@app.route('/doctor/welcome')
def doctor_welcome():
    lang = get_language()
    return render_template('doctor_welcome.html', lang=lang, t=get_translation)

@app.route('/doctor/register', methods=['GET', 'POST'])
def doctor_register():
    lang = get_language()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        email = request.form.get('email')
        doctor_type = request.form.get('doctor_type', 'human')
        
        # Validate required fields
        if not all([username, password, name, specialization, email, doctor_type]):
            return render_template('doctor_register.html', 
                                 lang=lang, 
                                 t=get_translation, 
                                 error='All fields are required')
        
        conn = get_db_connection()
        existing_doctor = conn.execute(
            'SELECT * FROM doctors WHERE username = ?', (username,)
        ).fetchone()
        
        if existing_doctor:
            conn.close()
            return render_template('doctor_register.html', 
                                 lang=lang, 
                                 t=get_translation, 
                                 error='Username already exists')
        
        conn.execute(
            'INSERT INTO doctors (username, password, name, specialization, email, doctor_type) VALUES (?, ?, ?, ?, ?, ?)',
            (username, password, name, specialization, email, doctor_type)
        )
        conn.commit()
        conn.close()
        
        return redirect('/doctor/login?message=Registration successful. Please login.')
    
    return render_template('doctor_register.html', lang=lang, t=get_translation)

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    lang = get_language()
    message = request.args.get('message', '')
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            error = 'Username and password are required'
        else:
            conn = get_db_connection()
            doctor = conn.execute(
                'SELECT * FROM doctors WHERE username = ? AND password = ?', (username, password)
            ).fetchone()
            conn.close()
            
            if doctor:
                session['doctor_logged_in'] = True
                session['doctor_name'] = doctor['name']
                session['doctor_id'] = doctor['id']
                session['doctor_type'] = doctor['doctor_type']
                return redirect('/doctor/dashboard')
            else:
                error = 'Invalid credentials'
    
    return render_template('doctor_login.html', 
                         lang=lang, 
                         t=get_translation, 
                         error=error, 
                         message=message)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    lang = get_language()
    doctor_type = session.get('doctor_type', 'human')
    
    conn = get_db_connection()
    if doctor_type == 'human':
        patients = conn.execute(
            'SELECT * FROM patient_records ORDER BY timestamp DESC LIMIT 20'
        ).fetchall()
    else:
        patients = conn.execute(
            'SELECT * FROM animal_records ORDER BY timestamp DESC LIMIT 20'
        ).fetchall()
    conn.close()
    
    return render_template('doctor_dashboard.html', lang=lang, t=get_translation, 
                         doctor_name=session.get('doctor_name'), patients=patients, doctor_type=doctor_type)

@app.route('/doctor/chat')
def doctor_chat():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    lang = get_language()
    doctor_id = session.get('doctor_id')
    
    conn = get_db_connection()
    messages = conn.execute(
        'SELECT * FROM messages WHERE doctor_id = ? ORDER BY timestamp DESC LIMIT 50',
        (doctor_id,)
    ).fetchall()
    conn.close()
    
    return render_template('doctor_chat.html', lang=lang, t=get_translation, 
                         doctor_name=session.get('doctor_name'), messages=messages)

# NEW ROUTE: Get chat patients for doctors
@app.route('/api/doctor/chat-patients')
def get_chat_patients():
    try:
        if not session.get('doctor_logged_in'):
            return jsonify({'error': 'Not authorized'}), 401
        
        doctor_id = session.get('doctor_id')
        doctor_type = session.get('doctor_type', 'human')
        
        conn = get_db_connection()
        
        # Get unique patients who have sent messages to this doctor
        messages = conn.execute('''
            SELECT DISTINCT patient_id 
            FROM messages 
            WHERE doctor_id = ? 
            ORDER BY timestamp DESC
        ''', (doctor_id,)).fetchall()
        
        patients = []
        for msg in messages:
            patient_id = msg['patient_id']
            if patient_id.startswith('PAT'):
                # Human patient
                patient_record = conn.execute(
                    'SELECT * FROM patient_records WHERE patient_id = ?', 
                    (patient_id,)
                ).fetchone()
                if patient_record:
                    patients.append({
                        'patient_id': patient_id,
                        'name': f"Patient {patient_id}",
                        'type': 'human',
                        'village': patient_record['village'],
                        'last_message_time': get_last_message_time(conn, patient_id, doctor_id)
                    })
            else:
                # Animal patient
                animal_record = conn.execute(
                    'SELECT * FROM animal_records WHERE animal_id = ?', 
                    (patient_id,)
                ).fetchone()
                if animal_record:
                    patients.append({
                        'patient_id': patient_id,
                        'name': f"{animal_record['animal_type']} - {animal_record['animal_breed']}",
                        'type': 'animal',
                        'owner': animal_record['owner_name'],
                        'last_message_time': get_last_message_time(conn, patient_id, doctor_id)
                    })
        
        conn.close()
        return jsonify(patients)
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/doctor/logout')
def doctor_logout():
    session.pop('doctor_logged_in', None)
    session.pop('doctor_name', None)
    session.pop('doctor_id', None)
    session.pop('doctor_type', None)
    return redirect('/doctor/welcome')

# API Routes
@app.route('/api/patient/vitals', methods=['POST'])
def submit_vitals():
    try:
        data = request.get_json()
        
        if not safety_monitor.validate_vitals(data):
            return jsonify({'error': 'Invalid vital readings detected'}), 400
        
        emergency_conditions = safety_monitor.check_emergency_conditions(data)
        emergency_flag = len(emergency_conditions) > 0
        
        patient_id = generate_patient_id()
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO patient_records 
            (patient_id, village, age, gender, bp_systolic, bp_diastolic, temperature, pulse, sugar, oxygen, symptoms, emergency_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            data.get('village', 'Unknown'),
            data.get('age'),
            data.get('gender', 'Unknown'),
            data.get('bpSystolic'),
            data.get('bpDiastolic'),
            data.get('temperature'),
            data.get('pulse'),
            data.get('sugar'),
            data.get('oxygen'),
            data.get('symptoms', ''),
            emergency_flag
        ))
        conn.commit()
        conn.close()
        
        suggestions = ai_analytics.analyze_symptoms(data)
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'suggestions': suggestions,
            'emergency_conditions': emergency_conditions,
            'emergency_flag': emergency_flag
        })
        
    except Exception as e:
        logging.error(f"Error submitting vitals: {str(e)}")
        return jsonify({'error': 'System error'}), 500

@app.route('/api/animal/health', methods=['POST'])
def submit_animal_health():
    try:
        data = request.get_json()
        
        animal_id = generate_animal_id()
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO animal_records 
            (animal_id, owner_name, owner_phone, animal_type, animal_breed, animal_age, animal_gender, symptoms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            animal_id,
            data.get('ownerName', 'Unknown'),
            data.get('ownerPhone', 'Unknown'),
            data.get('animalType', 'Unknown'),
            data.get('animalBreed', 'Unknown'),
            data.get('animalAge', 'Unknown'),
            data.get('animalGender', 'Unknown'),
            data.get('symptoms', '')
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'animal_id': animal_id,
            'message': 'Animal health assessment submitted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error submitting animal health: {str(e)}")
        return jsonify({'error': 'System error'}), 500

@app.route('/api/patient/emergency', methods=['POST'])
def emergency_sos():
    try:
        data = request.get_json()
        safety_monitor.send_emergency_alert(data)
        
        return jsonify({
            'success': True, 
            'message': 'Emergency alert sent to medical services! Help is on the way.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': 'Emergency alert failed'}), 500

@app.route('/api/patient/history/<patient_id>')
def get_patient_history(patient_id):
    try:
        conn = get_db_connection()
        records = conn.execute(
            'SELECT * FROM patient_records WHERE patient_id = ? ORDER BY timestamp DESC', (patient_id,)
        ).fetchall()
        conn.close()
        
        if not records:
            return jsonify({'success': False, 'error': 'No records found for this Patient ID'}), 404
        
        history = []
        for record in records:
            history.append({
                'patient_id': record['patient_id'],
                'village': record['village'],
                'age': record['age'],
                'gender': record['gender'],
                'bp_systolic': record['bp_systolic'],
                'bp_diastolic': record['bp_diastolic'],
                'temperature': record['temperature'],
                'pulse': record['pulse'],
                'sugar': record['sugar'],
                'oxygen': record['oxygen'],
                'symptoms': record['symptoms'],
                'emergency_flag': bool(record['emergency_flag']),
                'prescription': record['prescription'],
                'prescribed_by': record['prescribed_by'],
                'prescription_date': record['prescription_date'],
                'status': record['status'],
                'timestamp': record['timestamp']
            })
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'System error'}), 500

@app.route('/api/patient/queue')
def get_patient_queue_status():
    try:
        conn = get_db_connection()
        total_patients = conn.execute("SELECT COUNT(*) FROM patient_records").fetchone()[0]
        conn.close()
        
        # Simulate queue position (in real app, this would be based on actual queue)
        position = random.randint(1, 10) if total_patients > 0 else 0
        
        return jsonify({
            'total_patients': total_patients,
            'your_position': position,
            'wait_time': position * 5  # 5 minutes per patient
        })
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/doctor/queue')
def get_patient_queue():
    try:
        doctor_type = session.get('doctor_type', 'human')
        conn = get_db_connection()
        
        if doctor_type == 'human':
            records = conn.execute(
                'SELECT * FROM patient_records ORDER BY timestamp DESC LIMIT 20'
            ).fetchall()
        else:
            records = conn.execute(
                'SELECT * FROM animal_records ORDER BY timestamp DESC LIMIT 20'
            ).fetchall()
        conn.close()
        
        queue_data = []
        for record in records:
            if doctor_type == 'human':
                queue_data.append({
                    'id': record['patient_id'],
                    'type': 'human',
                    'name': f"Patient {record['patient_id']}",
                    'village': record['village'],
                    'age': record['age'],
                    'gender': record['gender'],
                    'symptoms': record['symptoms'],
                    'emergency_flag': bool(record['emergency_flag']),
                    'prescription': record['prescription'],
                    'status': record['status'],
                    'timestamp': record['timestamp']
                })
            else:
                queue_data.append({
                    'id': record['animal_id'],
                    'type': 'animal',
                    'name': f"{record['animal_type']} - {record['animal_breed']}",
                    'owner': record['owner_name'],
                    'phone': record['owner_phone'],
                    'symptoms': record['symptoms'],
                    'emergency_flag': bool(record['emergency_flag']),
                    'prescription': record['prescription'],
                    'status': record['status'],
                    'timestamp': record['timestamp']
                })
        
        return jsonify(queue_data)
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/doctor/prescribe', methods=['POST'])
def prescribe_medication():
    try:
        if not session.get('doctor_logged_in'):
            return jsonify({'error': 'Not authorized'}), 401
            
        data = request.get_json()
        record_id = data.get('record_id')
        record_type = data.get('record_type', 'human')
        prescription = data.get('prescription')
        
        conn = get_db_connection()
        
        if record_type == 'human':
            conn.execute('''
                UPDATE patient_records 
                SET prescription = ?, prescribed_by = ?, prescription_date = CURRENT_TIMESTAMP, status = 'prescribed'
                WHERE patient_id = ?
            ''', (prescription, session.get('doctor_name'), record_id))
        else:
            conn.execute('''
                UPDATE animal_records 
                SET prescription = ?, prescribed_by = ?, prescription_date = CURRENT_TIMESTAMP, status = 'prescribed'
                WHERE animal_id = ?
            ''', (prescription, session.get('doctor_name'), record_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Prescription saved successfully'})
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        message = data.get('message')
        image_data = data.get('image_data')
        sender_type = data.get('sender_type', 'patient')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO messages (patient_id, doctor_id, message_type, content, sender_type, image_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, 'text', message, sender_type, image_data))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/chat/messages/<patient_id>/<doctor_id>')
def get_chat_messages(patient_id, doctor_id):
    try:
        conn = get_db_connection()
        messages = conn.execute('''
            SELECT * FROM messages 
            WHERE patient_id = ? AND doctor_id = ? 
            ORDER BY timestamp ASC
        ''', (patient_id, doctor_id)).fetchall()
        conn.close()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg['id'],
                'patient_id': msg['patient_id'],
                'doctor_id': msg['doctor_id'],
                'message_type': msg['message_type'],
                'content': msg['content'],
                'timestamp': msg['timestamp'],
                'sender_type': msg['sender_type'],
                'image_data': msg['image_data']
            })
        
        return jsonify({'success': True, 'messages': message_list})
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/doctor/analytics')
def get_analytics():
    try:
        analytics = ai_analytics.get_trends_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/doctor/patient/<patient_id>')
def get_patient_details(patient_id):
    try:
        if not session.get('doctor_logged_in'):
            return jsonify({'error': 'Not authorized'}), 401
        
        conn = get_db_connection()
        
        if patient_id.startswith('PAT'):
            patient = conn.execute(
                'SELECT * FROM patient_records WHERE patient_id = ?', (patient_id,)
            ).fetchone()
        else:
            patient = conn.execute(
                'SELECT * FROM animal_records WHERE animal_id = ?', (patient_id,)
            ).fetchone()
        
        conn.close()
        
        if patient:
            return jsonify({
                'success': True,
                'patient': dict(patient)
            })
        else:
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
            
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("🚀 Healthcare Kiosk System Starting...")
    print("📍 Welcome Page: http://localhost:5000")
    print("👨‍⚕️ Doctor Welcome: http://localhost:5000/doctor/welcome")
    print("🔧 Doctor Login: http://localhost:5000/doctor/login")
    print("💬 Doctor Chat Patients API: http://localhost:5000/api/doctor/chat-patients")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)