from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, json
from datetime import datetime
import sqlite3
import logging
import random
import base64

app = Flask(__name__)
app.secret_key = "healthkiosk_secret_key_2024"
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading',
                   logger=True,
                   engineio_logger=True)

# Data storage
PATIENTS_FILE = "patients_data.json"
ANIMALS_FILE = "animals_data.json"
BALANCE_DIET_FILE = "balance_diet_data.json"

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

def load_animals():
    try:
        if os.path.exists(ANIMALS_FILE):
            with open(ANIMALS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_animals(animals_data):
    try:
        with open(ANIMALS_FILE, 'w') as f:
            json.dump(animals_data, f, indent=2)
        return True
    except:
        return False

def load_balance_diet():
    try:
        if os.path.exists(BALANCE_DIET_FILE):
            with open(BALANCE_DIET_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_balance_diet(diet_data):
    try:
        with open(BALANCE_DIET_FILE, 'w') as f:
            json.dump(diet_data, f, indent=2)
        return True
    except:
        return False

# Multi-language support
LANGUAGES = {
    'en': {
        'health_kiosk': 'Health Kiosk',
        'welcome': 'Welcome to Health Kiosk',
        'complete_form': 'Complete your health form and get instant prescription',
        'health_assessment': 'Health Assessment',
        'animal_health': 'Animal Health',
        'view_history': 'View History',
        'patient_queue': 'Patient Queue',
        'chat_with_doctor': 'Chat with Doctor',
        'emergency_sos': 'Emergency SOS',
        'your_health_priority': 'Your Health is Our Priority',
        'english': 'English',
        'hindi': 'Hindi',
        'kannada': 'Kannada',
        # Patient Form
        'patient_form': 'Patient Health Form',
        'name': 'Name',
        'city': 'City',
        'age': 'Age',
        'weight': 'Weight (kg)',
        'bp': 'Blood Pressure',
        'sugar': 'Sugar Level',
        'oxygen': 'Oxygen Level',
        'blood_group': 'Blood Group',
        'symptoms': 'Symptoms',
        'submit': 'Submit',
        'fill_all_fields': 'Please fill all fields!',
        'submitted_success': 'Submitted successfully!',
        # Animal Form
        'animal_form': 'Animal Health Form',
        'owner_name': 'Owner Name',
        'animal_type': 'Animal Type',
        'animal_name': 'Animal Name',
        'gender': 'Gender',
        'breed': 'Breed',
        'condition': 'Condition',
        'village': 'Village',
        'contact': 'Contact Number',
        'describe_symptoms': 'Describe the animal\'s symptoms in detail...',
        'submit_animal_form': 'Submit Animal Health Form',
        'check_prescription_status': 'Check Prescription Status',
        'back_to_home': 'Back to Home',
        'male': 'Male',
        'female': 'Female',
        'other': 'Other',
        'select_animal_type': 'Select Animal Type',
        'select_gender': 'Select Gender',
        'select_condition': 'Select Condition',
        # Doctor/Veterinarian
        'doctor_dashboard': 'Doctor Dashboard',
        'veterinarian_dashboard': 'Veterinarian Dashboard',
        'welcome_doctor': 'Welcome, Dr. {}',
        'animal_patients': 'Animal Patients',
        'search_placeholder': 'Search by Animal ID, Name, Owner...',
        'search': 'Search',
        'clear': 'Clear',
        'total_animals': 'Total Animals',
        'write_prescription': 'Write Prescription',
        'update_prescription': 'Update Prescription',
        'prescription_details': 'Prescription Details',
        'submit_prescription': 'Submit Prescription',
        'back_to_dashboard': 'Back to Dashboard',
        # Login
        'doctor_login': 'Doctor Login',
        'access_medical_dashboard': 'Access Medical Dashboard',
        'login_instructions': 'Login Instructions',
        'human_doctor_access': 'Access human patient dashboard',
        'veterinarian_access': 'Access animal patient dashboard',
        'username': 'Username',
        'password': 'Password',
        'login': 'Login',
        'back_to_patient_portal': 'Back to Patient Portal',
        'language': 'Language',
        'manage_all_animals': 'Manage all animals',
        'view_all_records': 'View all records',
        'chat_with_owners': 'Chat with owners',
        'end_session': 'End session',
        'owner': 'Owner',
        'no_animal_patients': 'No Animal Patients Found',
        'no_matching_animals': 'No animal patients match your search criteria.',
        'no_animals_waiting': 'There are no animal patients waiting for consultation yet.',
        'view_all_animals': 'View All Animals',
        'print': 'Print',
        # Chat & Queue
        'patient_chat': 'Patient Chat',
        'chat_with_doctors': 'Chat with Doctors',
        'type_message': 'Type your message...',
        'send': 'Send',
        'patient_queue': 'Patient Queue',
        'waiting_patients': 'Waiting Patients',
        'patient_id': 'Patient ID',
        'patient_name': 'Patient Name',
        'submission_time': 'Submission Time',
        'status': 'Status',
        'waiting': 'Waiting',
        'prescribed': 'Prescribed',
        'no_patients_waiting': 'No patients currently waiting',
        'your_chat_id': 'Your Chat ID',
        'start_chat': 'Start Chat',
        'no_chat_selected': 'No chat selected',
        # Chat specific translations
        'chat_with_vet': 'Chat with Veterinarian',
        'chat_with_doctor': 'Chat with Doctor',
        'chat_with_patient': 'Chat with Patient',
        'select_vet': 'Select Veterinarian',
        'select_doctor': 'Select Doctor',
        'enter_animal_id': 'Enter Animal ID',
        'enter_patient_id': 'Enter Patient ID',
        'select_vet_and_animal': 'Select a veterinarian and enter animal ID to start chatting',
        'select_doctor_and_patient': 'Select a doctor and enter patient ID to start chatting',
        'select_patient_to_chat': 'Select a patient from the list to start chatting',
        'send_message': 'Send',
        'take_photo': 'Take Photo',
        'retake': 'Retake',
        'send_photo': 'Send Photo',
        'cancel': 'Cancel',
        'capture': 'Capture',
        'photo_attached': 'Photo attached',
        'photo_sent': 'Photo sent',
        'camera_error': 'Camera access denied or not available',
        'error_sending_message': 'Error sending message',
        'error_sending_photo': 'Error sending photo',
        'network_error': 'Network error',
        'no_messages': 'No messages yet',
        'back': 'Back',
        'patients': 'Patients',
        'loading': 'Loading',
        'refresh': 'Refresh',
        'select_patient': 'Select Patient',
        'human_patient': 'Human Patient',
        'animal_patient': 'Animal Patient',
        'new_message': 'New message',
        'no_patients': 'No patients available',
        'you': 'You',
        'patient': 'Patient',
        'error_sending': 'Error sending message',
        'write_prescription': 'Write Prescription',
        'prescription_placeholder': 'Enter prescription details...',
        'send_prescription': 'Send Prescription',
        'prescription_sent': 'Prescription sent successfully',
        # New translations for balance diet
        'view_prescription': 'View Prescription',
        'balance_diet': 'Balance Diet',
        'diet_type': 'Diet Type',
        'select_diet_type': 'Select Diet Type',
        'vegetarian': 'Vegetarian',
        'eggitarian': 'Eggitarian',
        'non_vegetarian': 'Non Vegetarian',
        'occupation': 'Occupation',
        'select_occupation': 'Select Occupation',
        'school': 'School',
        'college': 'College',
        'job': 'Job',
        'housewife': 'Housewife',
        'disease': 'Disease',
        'select_disease': 'Select Disease',
        'no_disease': 'No Disease',
        'diabetes': 'Diabetes',
        'blood_pressure': 'Blood Pressure',
        'thyroid': 'Thyroid',
        'cholesterol': 'Cholesterol',
        'finish': 'Finish',
        'next': 'Next',
        'previous': 'Previous',
        'generate_diet': 'Generate Diet',
        'five_day_diet_plan': '5-Day Diet Plan',
        'day': 'Day',
        'breakfast': 'Breakfast',
        'lunch': 'Lunch',
        'dinner': 'Dinner',
        'snacks': 'Snacks',
        'print_diet': 'Print Diet',
    },
    'hi': {
        'health_kiosk': 'स्वास्थ्य कियोस्क',
        'welcome': 'स्वास्थ्य कियोस्क में आपका स्वागत है',
        'complete_form': 'अपना स्वास्थ्य फॉर्म पूरा करें और तुरंत प्रिस्क्रिप्शन प्राप्त करें',
        'health_assessment': 'स्वास्थ्य मूल्यांकन',
        'animal_health': 'पशु स्वास्थ्य',
        'view_history': 'इतिहास देखें',
        'patient_queue': 'रोगी कतार',
        'chat_with_doctor': 'डॉक्टर से चैट करें',
        'emergency_sos': 'आपातकालीन एसओएस',
        'your_health_priority': 'आपका स्वास्थ्य हमारी प्राथमिकता है',
        'english': 'अंग्रेजी',
        'hindi': 'हिंदी',
        'kannada': 'कन्नड़',
        # Patient Form
        'patient_form': 'रोगी स्वास्थ्य फॉर्म',
        'name': 'नाम',
        'city': 'शहर',
        'age': 'उम्र',
        'weight': 'वजन (किलो)',
        'bp': 'ब्लड प्रेशर',
        'sugar': 'शुगर लेवल',
        'oxygen': 'ऑक्सीजन लेवल',
        'blood_group': 'ब्लड ग्रुप',
        'symptoms': 'लक्षण',
        'submit': 'जमा करें',
        'fill_all_fields': 'कृपया सभी फ़ील्ड भरें!',
        'submitted_success': 'सफलतापूर्वक जमा किया गया!',
        # Animal Form
        'animal_form': 'पशु स्वास्थ्य फॉर्म',
        'owner_name': 'मालिक का नाम',
        'animal_type': 'पशु प्रकार',
        'animal_name': 'पशु का नाम',
        'gender': 'लिंग',
        'breed': 'नस्ल',
        'condition': 'स्थिति',
        'village': 'गाँव',
        'contact': 'संपर्क नंबर',
        'describe_symptoms': 'पशु के लक्षणों का विस्तार से वर्णन करें...',
        'submit_animal_form': 'पशु स्वास्थ्य फॉर्म जमा करें',
        'check_prescription_status': 'प्रिस्क्रिप्शन स्थिति जांचें',
        'back_to_home': 'होम पर वापस जाएं',
        'male': 'नर',
        'female': 'मादा',
        'other': 'अन्य',
        'select_animal_type': 'पशु प्रकार चुनें',
        'select_gender': 'लिंग चुनें',
        'select_condition': 'स्थिति चुनें',
        # Doctor/Veterinarian
        'doctor_dashboard': 'डॉक्टर डैशबोर्ड',
        'veterinarian_dashboard': 'पशु चिकित्सक डैशबोर्ड',
        'welcome_doctor': 'स्वागत है, डॉ. {}',
        'animal_patients': 'पशु रोगी',
        'search_placeholder': 'पशु आईडी, नाम, मालिक से खोजें...',
        'search': 'खोजें',
        'clear': 'साफ़ करें',
        'total_animals': 'कुल पशु',
        'write_prescription': 'प्रिस्क्रिप्शन लिखें',
        'update_prescription': 'प्रिस्क्रिप्शन अपडेट करें',
        'prescription_details': 'प्रिस्क्रिप्शन विवरण',
        'submit_prescription': 'प्रिस्क्रिप्शन जमा करें',
        'back_to_dashboard': 'डैशबोर्ड पर वापस जाएं',
        # Login
        'doctor_login': 'डॉक्टर लॉगिन',
        'access_medical_dashboard': 'मेडिकल डैशबोर्ड एक्सेस करें',
        'login_instructions': 'लॉगिन निर्देश',
        'human_doctor_access': 'मानव रोगी डैशबोर्ड एक्सेस करें',
        'veterinarian_access': 'पशु रोगी डैशबोर्ड एक्सेस करें',
        'username': 'यूजरनेम',
        'password': 'पासवर्ड',
        'login': 'लॉगिन',
        'back_to_patient_portal': 'रोगी पोर्टल पर वापस जाएं',
        'language': 'भाषा',
        'manage_all_animals': 'सभी पशुओं को प्रबंधित करें',
        'view_all_records': 'सभी रिकॉर्ड देखें',
        'chat_with_owners': 'मालिकों से चैट करें',
        'end_session': 'सत्र समाप्त करें',
        'owner': 'मालिक',
        'no_animal_patients': 'कोई पशु रोगी नहीं मिले',
        'no_matching_animals': 'आपकी खोज मानदंड से कोई पशु रोगी मेल नहीं खाते।',
        'no_animals_waiting': 'अभी तक कोई पशु रोगी परामर्श की प्रतीक्षा में नहीं हैं।',
        'view_all_animals': 'सभी पशु देखें',
        'print': 'प्रिंट',
        # Chat & Queue
        'patient_chat': 'रोगी चैट',
        'chat_with_doctors': 'डॉक्टरों से चैट करें',
        'type_message': 'अपना संदेश टाइप करें...',
        'send': 'भेजें',
        'patient_queue': 'रोगी कतार',
        'waiting_patients': 'प्रतीक्षारत रोगी',
        'patient_id': 'रोगी आईडी',
        'patient_name': 'रोगी का नाम',
        'submission_time': 'जमा करने का समय',
        'status': 'स्थिति',
        'waiting': 'प्रतीक्षा',
        'prescribed': 'निर्धारित',
        'no_patients_waiting': 'वर्तमान में कोई रोगी प्रतीक्षा में नहीं है',
        'your_chat_id': 'आपकी चैट आईडी',
        'start_chat': 'चैट शुरू करें',
        'no_chat_selected': 'कोई चैट चयनित नहीं',
        # Chat specific translations
        'chat_with_vet': 'पशु चिकित्सक से चैट करें',
        'chat_with_doctor': 'डॉक्टर से चैट करें',
        'chat_with_patient': 'रोगी से चैट करें',
        'select_vet': 'पशु चिकित्सक चुनें',
        'select_doctor': 'डॉक्टर चुनें',
        'enter_animal_id': 'पशु आईडी दर्ज करें',
        'enter_patient_id': 'रोगी आईडी दर्ज करें',
        'select_vet_and_animal': 'चैट शुरू करने के लिए पशु चिकित्सक चुनें और पशु आईडी दर्ज करें',
        'select_doctor_and_patient': 'चैट शुरू करने के लिए डॉक्टर चुनें और रोगी आईडी दर्ज करें',
        'select_patient_to_chat': 'चैट शुरू करने के लिए सूची से रोगी चुनें',
        'send_message': 'भेजें',
        'take_photo': 'फोटो लें',
        'retake': 'फिर से लें',
        'send_photo': 'फोटो भेजें',
        'cancel': 'रद्द करें',
        'capture': 'कैप्चर करें',
        'photo_attached': 'फोटो संलग्न',
        'photo_sent': 'फोटो भेज दी गई',
        'camera_error': 'कैमरा एक्सेस अस्वीकृत या उपलब्ध नहीं',
        'error_sending_message': 'संदेश भेजने में त्रुटि',
        'error_sending_photo': 'फोटो भेजने में त्रुटि',
        'network_error': 'नेटवर्क त्रुटि',
        'no_messages': 'अभी तक कोई संदेश नहीं',
        'back': 'वापस',
        'patients': 'रोगी',
        'loading': 'लोड हो रहा है',
        'refresh': 'ताज़ा करें',
        'select_patient': 'रोगी चुनें',
        'human_patient': 'मानव रोगी',
        'animal_patient': 'पशु रोगी',
        'new_message': 'नया संदेश',
        'no_patients': 'कोई रोगी उपलब्ध नहीं',
        'you': 'आप',
        'patient': 'रोगी',
        'error_sending': 'संदेश भेजने में त्रुटि',
        'write_prescription': 'प्रिस्क्रिप्शन लिखें',
        'prescription_placeholder': 'प्रिस्क्रिप्शन विवरण दर्ज करें...',
        'send_prescription': 'प्रिस्क्रिप्शन भेजें',
        'prescription_sent': 'प्रिस्क्रिप्शन सफलतापूर्वक भेज दिया गया',
        # New translations for balance diet
        'view_prescription': 'प्रिस्क्रिप्शन देखें',
        'balance_diet': 'संतुलित आहार',
        'diet_type': 'आहार प्रकार',
        'select_diet_type': 'आहार प्रकार चुनें',
        'vegetarian': 'शाकाहारी',
        'eggitarian': 'अंडा खाने वाले',
        'non_vegetarian': 'मांसाहारी',
        'occupation': 'व्यवसाय',
        'select_occupation': 'व्यवसाय चुनें',
        'school': 'स्कूल',
        'college': 'कॉलेज',
        'job': 'नौकरी',
        'housewife': 'गृहिणी',
        'disease': 'बीमारी',
        'select_disease': 'बीमारी चुनें',
        'no_disease': 'कोई बीमारी नहीं',
        'diabetes': 'मधुमेह',
        'blood_pressure': 'ब्लड प्रेशर',
        'thyroid': 'थायराइड',
        'cholesterol': 'कोलेस्ट्रॉल',
        'finish': 'समाप्त',
        'next': 'अगला',
        'previous': 'पिछला',
        'generate_diet': 'आहार जनरेट करें',
        'five_day_diet_plan': '5-दिवसीय आहार योजना',
        'day': 'दिन',
        'breakfast': 'नाश्ता',
        'lunch': 'दोपहर का भोजन',
        'dinner': 'रात का भोजन',
        'snacks': 'स्नैक्स',
        'print_diet': 'आहार प्रिंट करें',
    },
    'kn': {
        'health_kiosk': 'ಹೆಲ್ತ್ ಕಿಯೋಸ್ಕ್',
        'welcome': 'ಹೆಲ್ತ್ ಕಿಯೋಸ್ಕ್ ಗೆ ಸ್ವಾಗತ',
        'complete_form': 'ನಿಮ್ಮ ಆರೋಗ್ಯ ಫಾರ್ಮ್ ಪೂರ್ಣಗೊಳಿಸಿ ಮತ್ತು ತಕ್ಷಣ ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಪಡೆಯಿರಿ',
        'health_assessment': 'ಆರೋಗ್ಯ ಮೌಲ್ಯಮಾಪನ',
        'animal_health': 'ಪಶು ಆರೋಗ್ಯ',
        'view_history': 'ಇತಿಹಾಸ ನೋಡಿ',
        'patient_queue': 'ರೋಗಿ ಕ್ಯೂ',
        'chat_with_doctor': 'ಡಾಕ್ಟರ್ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ',
        'emergency_sos': 'ಅತ್ಯಾಹತ ಎಸ್ಒಎಸ್',
        'your_health_priority': 'ನಿಮ್ಮ ಆರೋಗ್ಯ ನಮ್ಮ ಪ್ರಾಮುಖ್ಯತೆ',
        'english': 'ಇಂಗ್ಲಿಷ್',
        'hindi': 'ಹಿಂದಿ',
        'kannada': 'ಕನ್ನಡ',
        # Patient Form
        'patient_form': 'ರೋಗಿ ಆರೋಗ್ಯ ಫಾರ್ಮ್',
        'name': 'ಹೆಸರು',
        'city': 'ನಗರ',
        'age': 'ವಯಸ್ಸು',
        'weight': 'ತೂಕ (ಕೆಜಿ)',
        'bp': 'ಬ್ಲಡ್ ಪ್ರೆಶರ್',
        'sugar': 'ಶುಗರ್ ಲೆವೆಲ್',
        'oxygen': 'ಆಕ್ಸಿಜನ್ ಲೆವೆಲ್',
        'blood_group': 'ಬ್ಲಡ್ ಗ್ರೂಪ್',
        'symptoms': 'ಲಕ್ಷಣಗಳು',
        'submit': 'ಸಬ್ಮಿಟ್ ಮಾಡಿ',
        'fill_all_fields': 'ದಯವಿಟ್ಟು ಎಲ್ಲಾ ಫೀಲ್ಡ್‌ಗಳನ್ನು ಪೂರೈಸಿ!',
        'submitted_success': 'ಯಶಸ್ವಿಯಾಗಿ ಸಬ್ಮಿಟ್ ಆಯಿತು!',
        # Animal Form
        'animal_form': 'ಪಶು ಆರೋಗ್ಯ ಫಾರ್ಮ್',
        'owner_name': 'ಮಾಲೀಕರ ಹೆಸರು',
        'animal_type': 'ಪಶು ಪ್ರಕಾರ',
        'animal_name': 'ಪಶುವಿನ ಹೆಸರು',
        'gender': 'ಲಿಂಗ',
        'breed': 'ಬ್ರೀಡ್',
        'condition': 'ಸ್ಥಿತಿ',
        'village': 'ಗ್ರಾಮ',
        'contact': 'ಸಂಪರ್ಕ ಸಂಖ್ಯೆ',
        'describe_symptoms': 'ಪಶುವಿನ ಲಕ್ಷಣಗಳನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ...',
        'submit_animal_form': 'ಪಶು ಆರೋಗ್ಯ ಫಾರ್ಮ್ ಸಬ್ಮಿಟ್ ಮಾಡಿ',
        'check_prescription_status': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸಿ',
        'back_to_home': 'ಹೋಮ್‌ಗೆ ಹಿಂತಿರುಗಿ',
        'male': 'ಪುರುಷ',
        'female': 'ಸ್ತ್ರೀ',
        'other': 'ಇತರೆ',
        'select_animal_type': 'ಪಶು ಪ್ರಕಾರ ಆಯ್ಕೆಮಾಡಿ',
        'select_gender': 'ಲಿಂಗ ಆಯ್ಕೆಮಾಡಿ',
        'select_condition': 'ಸ್ಥಿತಿ ಆಯ್ಕೆಮಾಡಿ',
        # Doctor/Veterinarian
        'doctor_dashboard': 'ಡಾಕ್ಟರ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
        'veterinarian_dashboard': 'ವೆಟರ್ನರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
        'welcome_doctor': 'ಸ್ವಾಗತ, ಡಾ. {}',
        'animal_patients': 'ಪಶು ರೋಗಿಗಳು',
        'search_placeholder': 'ಪಶು ಐಡಿ, ಹೆಸರು, ಮಾಲೀಕರಿಂದ ಹುಡುಕಿ...',
        'search': 'ಹುಡುಕಿ',
        'clear': 'ಕ್ಲಿಯರ್',
        'total_animals': 'ಒಟ್ಟು ಪಶುಗಳು',
        'write_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಬರೆಯಿರಿ',
        'update_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಪ್ಡೇಟ್ ಮಾಡಿ',
        'prescription_details': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ವಿವರಗಳು',
        'submit_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಸಬ್ಮಿಟ್ ಮಾಡಿ',
        'back_to_dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ',
        # Login
        'doctor_login': 'ಡಾಕ್ಟರ್ ಲಾಗಿನ್',
        'access_medical_dashboard': 'ಮೆಡಿಕಲ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಪ್ರವೇಶಿಸಿ',
        'login_instructions': 'ಲಾಗಿನ್ ಸೂಚನೆಗಳು',
        'human_doctor_access': 'ಮಾನವ ರೋಗಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಪ್ರವೇಶಿಸಿ',
        'veterinarian_access': 'ಪಶು ರೋಗಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಪ್ರವೇಶಿಸಿ',
        'username': 'ಬಳಕೆದಾರಹೆಸರು',
        'password': 'ಪಾಸ್ವರ್ಡ್',
        'login': 'ಲಾಗಿನ್',
        'back_to_patient_portal': 'ರೋಗಿ ಪೋರ್ಟಲ್‌ಗೆ ಹಿಂತಿರುಗಿ',
        'language': 'ಭಾಷೆ',
        'manage_all_animals': 'ಎಲ್ಲಾ ಪಶುಗಳನ್ನು ನಿರ್ವಹಿಸಿ',
        'view_all_records': 'ಎಲ್ಲಾ ದಾಖಲೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
        'chat_with_owners': 'ಮಾಲೀಕರೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ',
        'end_session': 'ಅಧಿವೇಶನ ಮುಕ್ತಾಯಗೊಳಿಸಿ',
        'owner': 'ಮಾಲೀಕ',
        'no_animal_patients': 'ಯಾವುದೇ ಪಶು ರೋಗಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ',
        'no_matching_animals': 'ನಿಮ್ಮ ಹುಡುಕಾಟ ಮಾನದಂಡಕ್ಕೆ ಹೊಂದಿಕೆಯಾಗುವ ಯಾವುದೇ ಪಶು ರೋಗಿಗಳು ಇಲ್ಲ.',
        'no_animals_waiting': 'ಇನ್ನೂ ಯಾವುದೇ ಪಶು ರೋಗಿಗಳು ಸಲಹೆಗಾಗಿ ಕಾಯುತ್ತಿಲ್ಲ.',
        'view_all_animals': 'ಎಲ್ಲಾ ಪಶುಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
        'print': 'ಮುದ್ರಣ',
        # Chat & Queue
        'patient_chat': 'ರೋಗಿ ಚಾಟ್',
        'chat_with_doctors': 'ಡಾಕ್ಟರ್‌ಗಳೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ',
        'type_message': 'ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ...',
        'send': 'ಕಳುಹಿಸಿ',
        'patient_queue': 'ರೋಗಿ ಕ್ಯೂ',
        'waiting_patients': 'ಕಾಯುತ್ತಿರುವ ರೋಗಿಗಳು',
        'patient_id': 'ರೋಗಿ ಐಡಿ',
        'patient_name': 'ರೋಗಿಯ ಹೆಸರು',
        'submission_time': 'ಸಲ್ಲಿಕೆ ಸಮಯ',
        'status': 'ಸ್ಥಿತಿ',
        'waiting': 'ಕಾಯುತ್ತಿದೆ',
        'prescribed': 'ನಿರ್ದೇಶಿಸಲಾಗಿದೆ',
        'no_patients_waiting': 'ಪ್ರಸ್ತುತ ಯಾವುದೇ ರೋಗಿಗಳು ಕಾಯುತ್ತಿಲ್ಲ',
        'your_chat_id': 'ನಿಮ್ಮ ಚಾಟ್ ಐಡಿ',
        'start_chat': 'ಚಾಟ್ ಪ್ರಾರಂಭಿಸಿ',
        'no_chat_selected': 'ಯಾವುದೇ ಚಾಟ್ ಆಯ್ಕೆ ಮಾಡಲಾಗಿಲ್ಲ',
        # Chat specific translations
        'chat_with_vet': 'ವೆಟರ್ನರಿಯನ್ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ',
        'chat_with_doctor': 'ಡಾಕ್ಟರ್ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ',
        'chat_with_patient': 'ರೋಗಿಯೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ',
        'select_vet': 'ವೆಟರ್ನರಿಯನ್ ಆಯ್ಕೆಮಾಡಿ',
        'select_doctor': 'ಡಾಕ್ಟರ್ ಆಯ್ಕೆಮಾಡಿ',
        'enter_animal_id': 'ಪಶು ಐಡಿ ನಮೂದಿಸಿ',
        'enter_patient_id': 'ರೋಗಿ ಐಡಿ ನಮೂದಿಸಿ',
        'select_vet_and_animal': 'ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ವೆಟರ್ನರಿಯನ್ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತು ಪಶು ಐಡಿ ನಮೂದಿಸಿ',
        'select_doctor_and_patient': 'ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ಡಾಕ್ಟರ್ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತು ರೋಗಿ ಐಡಿ ನಮೂದಿಸಿ',
        'select_patient_to_chat': 'ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ಪಟ್ಟಿಯಿಂದ ರೋಗಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'send_message': 'ಕಳುಹಿಸಿ',
        'take_photo': 'ಫೋಟೋ ತೆಗೆಯಿರಿ',
        'retake': 'ಮರುತೆಗೆದುಕೊಳ್ಳಿ',
        'send_photo': 'ಫೋಟೋ ಕಳುಹಿಸಿ',
        'cancel': 'ರದ್ದುಮಾಡಿ',
        'capture': 'ಕ್ಯಾಪ್ಚರ್ ಮಾಡಿ',
        'photo_attached': 'ಫೋಟೋ ಲಗತ್ತಿಸಲಾಗಿದೆ',
        'photo_sent': 'ಫೋಟೋ ಕಳುಹಿಸಲಾಗಿದೆ',
        'camera_error': 'ಕ್ಯಾಮೆರಾ ಪ್ರವೇಶ ನಿರಾಕರಿಸಲಾಗಿದೆ ಅಥವಾ ಲಭ್ಯವಿಲ್ಲ',
        'error_sending_message': 'ಸಂದೇಶ ಕಳುಹಿಸುವಲ್ಲಿ ದೋಷ',
        'error_sending_photo': 'ಫೋಟೋ ಕಳುಹಿಸುವಲ್ಲಿ ದೋಷ',
        'network_error': 'ನೆಟ್ವರ್ಕ್ ದೋಷ',
        'no_messages': 'ಇನ್ನೂ ಯಾವುದೇ ಸಂದೇಶಗಳಿಲ್ಲ',
        'back': 'ಹಿಂದೆ',
        'patients': 'ರೋಗಿಗಳು',
        'loading': 'ಲೋಡ್ ಆಗುತ್ತಿದೆ',
        'refresh': 'ರಿಫ್ರೆಶ್ ಮಾಡಿ',
        'select_patient': 'ರೋಗಿ ಆಯ್ಕೆಮಾಡಿ',
        'human_patient': 'ಮಾನವ ರೋಗಿ',
        'animal_patient': 'ಪಶು ರೋಗಿ',
        'new_message': 'ಹೊಸ ಸಂದೇಶ',
        'no_patients': 'ಯಾವುದೇ ರೋಗಿಗಳು ಲಭ್ಯವಿಲ್ಲ',
        'you': 'ನೀವು',
        'patient': 'ರೋಗಿ',
        'error_sending': 'ಸಂದೇಶ ಕಳುಹಿಸುವಲ್ಲಿ ದೋಷ',
        'write_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಬರೆಯಿರಿ',
        'prescription_placeholder': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ...',
        'send_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಕಳುಹಿಸಿ',
        'prescription_sent': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಯಶಸ್ವಿಯಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ',
        # New translations for balance diet
        'view_prescription': 'ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ವೀಕ್ಷಿಸಿ',
        'balance_diet': 'ಸಮತೋಲಿತ ಆಹಾರ',
        'diet_type': 'ಆಹಾರ ಪ್ರಕಾರ',
        'select_diet_type': 'ಆಹಾರ ಪ್ರಕಾರ ಆಯ್ಕೆಮಾಡಿ',
        'vegetarian': 'ಶಾಕಾಹಾರಿ',
        'eggitarian': 'ಮೊಟ್ಟೆ ತಿನ್ನುವವರು',
        'non_vegetarian': 'ಮಾಂಸಾಹಾರಿ',
        'occupation': 'ವೃತ್ತಿ',
        'select_occupation': 'ವೃತ್ತಿ ಆಯ್ಕೆಮಾಡಿ',
        'school': 'ಶಾಲೆ',
        'college': 'ಕಾಲೇಜು',
        'job': 'ಉದ್ಯೋಗ',
        'housewife': 'ಗೃಹಿಣಿ',
        'disease': 'ರೋಗ',
        'select_disease': 'ರೋಗ ಆಯ್ಕೆಮಾಡಿ',
        'no_disease': 'ಯಾವುದೇ ರೋಗ ಇಲ್ಲ',
        'diabetes': 'ಮಧುಮೇಹ',
        'blood_pressure': 'ರಕ್ತದೊತ್ತಡ',
        'thyroid': 'ಥೈರಾಯ್ಡ್',
        'cholesterol': 'ಕೊಲೆಸ್ಟ್ರಾಲ್',
        'finish': 'ಮುಗಿಸು',
        'next': 'ಮುಂದೆ',
        'previous': 'ಹಿಂದೆ',
        'generate_diet': 'ಆಹಾರ ಉತ್ಪಾದಿಸಿ',
        'five_day_diet_plan': '5-ದಿನದ ಆಹಾರ ಯೋಜನೆ',
        'day': 'ದಿನ',
        'breakfast': 'ಉಪಹಾರ',
        'lunch': 'ಮಧ್ಯಾಹ್ನದ ಊಟ',
        'dinner': 'ರಾತ್ರಿ ಊಟ',
        'snacks': 'ಲಘು ಆಹಾರ',
        'print_diet': 'ಆಹಾರ ಮುದ್ರಿಸಿ',
    }
}

# Helper function for translations in routes
def get_translation(key, lang=None):
    if lang is None:
        lang = session.get('lang', 'en')
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

# Context processor for multi-language support
@app.context_processor
def utility_processor():
    def get_current_language():
        return session.get('lang', 'en')
    
    def t(key, *args):
        lang = get_current_language()
        translation = LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)
        # Format string if arguments are provided
        if args:
            try:
                return translation.format(*args)
            except:
                return translation
        return translation
    
    return dict(t=t, current_language=get_current_language)

# Database setup for chat and records
def init_db():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    
    # Create messages table for chat functionality
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender_type TEXT NOT NULL,
            image_data TEXT
        )
    ''')
    
    # Create doctor records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            patient_name TEXT,
            village TEXT,
            prescription TEXT,
            prescription_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'prescribed'
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('healthcare.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
init_db()

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

# Language route
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['lang'] = lang
    return redirect(request.referrer or '/patient/welcome')

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
            return render_template("patient.html", error=get_translation('fill_all_fields'))

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

        return render_template("patient.html", message=get_translation('submitted_success'), pid=pid)

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

# Doctor Routes - Fixed Login Credentials
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Fixed login credentials
        if username == "Pratik" and password == "1714":
            session['doctor_logged_in'] = True
            session['doctor_name'] = "Pratik"
            session['doctor_id'] = "doc_pratik"
            session['doctor_username'] = "Pratik"
            session['doctor_type'] = "human"
            return redirect('/doctor/dashboard')
        
        elif username == "Shreyas" and password == "2025":
            session['doctor_logged_in'] = True
            session['doctor_name'] = "Shreyas"
            session['doctor_id'] = "doc_shreyas"
            session['doctor_username'] = "Shreyas"
            session['doctor_type'] = "veterinarian"
            return redirect('/veterinarian/dashboard')
        
        else:
            return render_template("doctor_login.html", error="❌ Invalid username or password. Access denied!")

    return render_template("doctor_login.html")

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    patients_data = load_patients()
    search_query = request.args.get('search', '')
    
    if search_query:
        filtered_patients = {}
        for pid, pdata in patients_data.items():
            if (search_query.lower() in pid.lower() or 
                search_query.lower() in pdata.get('name', '').lower() or
                search_query.lower() in pdata.get('city', '').lower()):
                filtered_patients[pid] = pdata
        patients_data = filtered_patients
    
    return render_template("doctor.html", 
                         patients=patients_data, 
                         search_query=search_query,
                         doctor_name=session.get('doctor_name'))

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
        doctor_name = session.get('doctor_name')
        doctor_id = session.get('doctor_id')
        
        if not prescription:
            return render_template("doctor_patient.html", pdata=pdata, error="Please write a prescription!")
        
        prescription_with_info = f"Patient ID: {pid}\nPatient Name: {pdata['name']}\nPrescribed by: Dr. {doctor_name}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n--- PRESCRIPTION ---\n{prescription}"
        
        pdata["prescription"] = prescription_with_info
        pdata["status"] = "prescribed"
        pdata["doctor_name"] = doctor_name
        pdata["prescription_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        patients_data[pid] = pdata
        
        save_patients(patients_data)
        
        # Save to doctor records
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO doctor_records (doctor_id, patient_id, patient_name, village, prescription)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_id, pid, pdata['name'], pdata.get('city', ''), prescription))
        conn.commit()
        conn.close()

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

# Animal Health Routes
@app.route('/animal/health')
def animal_health():
    return render_template('animal_form.html')

@app.route('/animal/health/submit', methods=['POST'])
def animal_health_submit():
    try:
        # Load existing animal data
        animals_data = load_animals()
        
        # Get form data
        owner_name = request.form.get("owner_name", "").strip()
        animal_type = request.form.get("animal_type", "").strip()
        animal_name = request.form.get("animal_name", "").strip()
        gender = request.form.get("gender", "").strip()
        breed = request.form.get("breed", "").strip()
        condition = request.form.get("condition", "").strip()
        age = request.form.get("age", "").strip()
        weight = request.form.get("weight", "").strip()
        symptoms = request.form.get("symptoms", "").strip()
        village = request.form.get("village", "").strip()
        contact = request.form.get("contact", "").strip()
        
        if not all([owner_name, animal_type, animal_name, gender, breed, condition, age, weight, symptoms, village]):
            error_message = get_translation('fill_all_fields')
            return render_template("animal_form.html", error=error_message)
        
        # Generate animal ID
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        animal_id = f"animal_{animal_type}_{ts}"
        
        # Save animal data
        animals_data[animal_id] = {
            "animal_id": animal_id,
            "owner_name": owner_name,
            "animal_type": animal_type,
            "animal_name": animal_name,
            "gender": gender,
            "breed": breed,
            "condition": condition,
            "age": age,
            "weight": weight,
            "symptoms": symptoms,
            "village": village,
            "contact": contact,
            "status": "waiting",
            "prescription": "",
            "veterinarian_name": "",
            "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prescription_date": ""
        }
        
        save_animals(animals_data)
        
        # Notify veterinarians via socket
        socketio.emit('new_animal_patient_notification', {
            'animal_id': animal_id,
            'animal_name': animal_name,
            'animal_type': animal_type,
            'owner_name': owner_name,
            'message': f'New animal patient {animal_name} ({animal_type}) submitted form'
        })
        
        success_message = get_translation('submitted_success')
        return render_template("animal_form.html", 
                             message=success_message, 
                             animal_id=animal_id)
    
    except Exception as e:
        return render_template("animal_form.html", error=f"Error submitting form: {str(e)}")

@app.route('/animal/health/status', methods=['GET', 'POST'])
def animal_health_status():
    animals_data = load_animals()
    search_results = {}
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get("animal_id", "").strip()
        if search_query:
            for animal_id, animal_data in animals_data.items():
                if (search_query.lower() in animal_id.lower() or 
                    search_query.lower() in animal_data.get('animal_name', '').lower() or
                    search_query.lower() in animal_data.get('owner_name', '').lower()):
                    search_results[animal_id] = animal_data
    
    return render_template("animal_prescription.html", 
                         animals=search_results, 
                         search_query=search_query)

@app.route('/animal/health/view/<animal_id>')
def animal_health_view(animal_id):
    animals_data = load_animals()
    animal_data = animals_data.get(animal_id)
    if not animal_data:
        return "No animal record found for ID: " + animal_id, 404
    return render_template("animal_view.html", animal_data=animal_data)

# Chat Routes
@app.route('/patient/chat')
def patient_chat():
    # Get available doctors
    doctors = [
        {"id": "doc_pratik", "name": "Pratik", "specialization": "General Physician"},
        {"id": "doc_shreyas", "name": "Shreyas", "specialization": "Veterinarian"}
    ]
    return render_template('patient_chat.html', doctors=doctors, lang=session.get('lang', 'en'))

@app.route('/animal/chat')
def animal_chat():
    # Get available veterinarians
    vets = [
        {"id": "doc_shreyas", "name": "Shreyas", "specialization": "Veterinary Medicine"}
    ]
    return render_template('animal_chat.html', doctors=vets, lang=session.get('lang', 'en'))

@app.route('/doctor/chat')
def doctor_chat():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    return render_template('doctor_chat.html', 
                         doctor_name=session.get('doctor_name'),
                         lang=session.get('lang', 'en'))

# Veterinarian-specific routes
@app.route('/veterinarian/dashboard')
def veterinarian_dashboard():
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    # Check if doctor is a veterinarian
    if session.get('doctor_type') != 'veterinarian':
        return redirect('/doctor/dashboard')
    
    animals_data = load_animals()
    search_query = request.args.get('search', '')
    
    if search_query:
        filtered_animals = {}
        for animal_id, animal_data in animals_data.items():
            if (search_query.lower() in animal_id.lower() or 
                search_query.lower() in animal_data.get('animal_name', '').lower() or
                search_query.lower() in animal_data.get('owner_name', '').lower() or
                search_query.lower() in animal_data.get('village', '').lower()):
                filtered_animals[animal_id] = animal_data
        animals_data = filtered_animals
    
    return render_template("veterinarian_dashboard.html", 
                         animals=animals_data, 
                         search_query=search_query,
                         doctor_name=session.get('doctor_name'))

@app.route('/veterinarian/animal/<animal_id>', methods=['GET', 'POST'])
def veterinarian_animal(animal_id):
    if not session.get('doctor_logged_in'):
        return redirect('/doctor/login')
    
    # Check if doctor is a veterinarian
    if session.get('doctor_type') != 'veterinarian':
        return redirect('/doctor/dashboard')
    
    animals_data = load_animals()
    animal_data = animals_data.get(animal_id)
    if not animal_data:
        return "Animal patient not found: " + animal_id, 404

    if request.method == 'POST':
        prescription = request.form.get("prescription", "").strip()
        veterinarian_name = session.get('doctor_name')
        doctor_id = session.get('doctor_id')
        
        if not prescription:
            return render_template("veterinarian_animal.html", 
                                 animal_data=animal_data, 
                                 error="Please write a prescription!")
        
        prescription_with_info = f"Animal ID: {animal_id}\nAnimal Name: {animal_data['animal_name']}\nAnimal Type: {animal_data['animal_type']}\nGender: {animal_data['gender']}\nBreed: {animal_data['breed']}\nCondition: {animal_data['condition']}\nOwner: {animal_data['owner_name']}\nPrescribed by: Dr. {veterinarian_name} (Veterinarian)\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n--- PRESCRIPTION ---\n{prescription}"
        
        animal_data["prescription"] = prescription_with_info
        animal_data["status"] = "prescribed"
        animal_data["veterinarian_name"] = veterinarian_name
        animal_data["prescription_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        animals_data[animal_id] = animal_data
        
        save_animals(animals_data)
        
        # Save to doctor records
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO doctor_records (doctor_id, patient_id, patient_name, village, prescription)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_id, animal_id, f"{animal_data['animal_name']} ({animal_data['animal_type']})", animal_data.get('village', ''), prescription))
        conn.commit()
        conn.close()

        socketio.emit('animal_prescription_notification', {
            'animal_id': animal_id,
            'animal_name': animal_data['animal_name'],
            'owner_name': animal_data['owner_name'],
            'veterinarian_name': veterinarian_name,
            'message': f'Prescription ready from Dr. {veterinarian_name} for {animal_data["animal_name"]}'
        })

        return redirect('/veterinarian/dashboard')

    return render_template("veterinarian_animal.html", animal_data=animal_data)

# Balance Diet Routes
@app.route('/balance_diet')
def balance_diet():
    return render_template('balance_diet.html')

@app.route('/balance_diet/generate', methods=['POST'])
def generate_balance_diet():
    try:
        # Get form data
        diet_type = request.form.get("diet_type", "").strip()
        occupation = request.form.get("occupation", "").strip()
        age = request.form.get("age", "").strip()
        weight = request.form.get("weight", "").strip()
        disease = request.form.get("disease", "").strip()
        
        if not all([diet_type, occupation, age, weight, disease]):
            return render_template("balance_diet.html", error="Please fill all fields!")
        
        # Generate diet plan based on inputs
        diet_plan = generate_diet_plan(diet_type, occupation, age, weight, disease)
        
        # Save diet data
        diet_data = load_balance_diet()
        diet_id = f"diet_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        diet_data[diet_id] = {
            "diet_id": diet_id,
            "diet_type": diet_type,
            "occupation": occupation,
            "age": age,
            "weight": weight,
            "disease": disease,
            "diet_plan": diet_plan,
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_balance_diet(diet_data)
        
        return render_template("balance_diet_result.html", 
                             diet_plan=diet_plan,
                             diet_type=diet_type,
                             occupation=occupation,
                             age=age,
                             weight=weight,
                             disease=disease,
                             diet_id=diet_id)
    
    except Exception as e:
        return render_template("balance_diet.html", error=f"Error generating diet plan: {str(e)}")

def generate_diet_plan(diet_type, occupation, age, weight, disease):
    """Generate a 5-day diet plan based on user inputs"""
    
    # Base meals structure
    days = []
    
    for day in range(1, 6):
        day_plan = {
            "day": day,
            "breakfast": generate_breakfast(diet_type, occupation, disease),
            "lunch": generate_lunch(diet_type, occupation, disease),
            "snacks": generate_snacks(diet_type, occupation, disease),
            "dinner": generate_dinner(diet_type, occupation, disease)
        }
        days.append(day_plan)
    
    return days

def generate_breakfast(diet_type, occupation, disease):
    """Generate breakfast based on diet type and occupation"""
    breakfast_options = {
        "vegetarian": [
            "2 Roti + Vegetable Sabji + 1 bowl Dal + Salad",
            "Poha with vegetables + 1 glass milk",
            "Upma with vegetables + 1 bowl curd",
            "2 Idli + Sambar + Chutney",
            "Vegetable Paratha + 1 bowl curd"
        ],
        "eggitarian": [
            "2 Roti + Vegetable Sabji + 1 boiled egg + Salad",
            "Poha with vegetables + 1 boiled egg",
            "2 Egg Paratha + 1 glass milk",
            "2 Idli + Sambar + 1 boiled egg",
            "Vegetable Paratha + 1 boiled egg"
        ],
        "non_vegetarian": [
            "2 Roti + Chicken Curry + Salad",
            "Chicken Poha + 1 glass milk",
            "2 Egg Paratha + Chicken Curry",
            "Chicken Upma + 1 bowl curd",
            "2 Roti + Fish Curry + Salad"
        ]
    }
    
    return random.choice(breakfast_options.get(diet_type, breakfast_options["vegetarian"]))

def generate_lunch(diet_type, occupation, disease):
    """Generate lunch based on diet type and occupation"""
    lunch_options = {
        "vegetarian": [
            "1 cup Rice + 2 Roti + Dal + Vegetable Sabji + Salad + 1 bowl Curd",
            "1 cup Rice + Sambar + 2 Roti + Vegetable Sabji + Buttermilk",
            "1 cup Rice + Dal + 2 Roti + Mix Vegetable + Raita",
            "1 cup Rice + Rajma + 2 Roti + Salad + Curd",
            "1 cup Rice + Chole + 2 Roti + Salad + Buttermilk"
        ],
        "eggitarian": [
            "1 cup Rice + 2 Roti + Egg Curry + Vegetable Sabji + Salad",
            "1 cup Rice + 2 Roti + Chicken Curry + Dal + Salad",
            "1 cup Rice + Egg Biryani + Raita + Salad",
            "1 cup Rice + 2 Roti + Fish Curry + Vegetable Sabji",
            "1 cup Rice + 2 Roti + Mutton Curry + Dal + Salad"
        ],
        "non_vegetarian": [
            "1 cup Rice + 2 Roti + Chicken Curry + Dal + Salad",
            "1 cup Rice + 2 Roti + Fish Curry + Vegetable Sabji + Curd",
            "1 cup Rice + Mutton Curry + 2 Roti + Salad",
            "1 cup Rice + 2 Roti + Prawn Curry + Dal + Salad",
            "1 cup Rice + Chicken Biryani + Raita + Salad"
        ]
    }
    
    return random.choice(lunch_options.get(diet_type, lunch_options["vegetarian"]))

def generate_snacks(diet_type, occupation, disease):
    """Generate snacks based on diet type and occupation"""
    snacks_options = {
        "vegetarian": [
            "1 cup Tea/Coffee + 2 biscuits",
            "Fruit salad + 1 handful nuts",
            "1 cup milk + 2 dates",
            "1 bowl sprouts salad",
            "1 cup green tea + 1 fruit"
        ],
        "eggitarian": [
            "1 cup Tea/Coffee + 2 biscuits",
            "Fruit salad + 1 boiled egg",
            "1 cup milk + 2 dates + 1 boiled egg",
            "1 bowl sprouts salad + 1 boiled egg",
            "1 cup green tea + 1 fruit + handful nuts"
        ],
        "non_vegetarian": [
            "1 cup Tea/Coffee + 2 biscuits",
            "Fruit salad + handful nuts",
            "1 cup milk + 2 dates",
            "1 bowl chicken soup",
            "1 cup green tea + 1 fruit"
        ]
    }
    
    return random.choice(snacks_options.get(diet_type, snacks_options["vegetarian"]))

def generate_dinner(diet_type, occupation, disease):
    """Generate dinner based on diet type and occupation"""
    dinner_options = {
        "vegetarian": [
            "2 Roti + Vegetable Sabji + Dal + Salad",
            "1 cup Khichdi + 1 bowl Curd + Salad",
            "2 Roti + Paneer Sabji + Salad",
            "1 cup Rice + Dal + Vegetable Sabji + Salad",
            "2 Roti + Mix Vegetable + Dal + Salad"
        ],
        "eggitarian": [
            "2 Roti + Egg Curry + Vegetable Sabji + Salad",
            "2 Roti + Chicken Curry + Dal + Salad",
            "1 cup Rice + Egg Curry + Vegetable Sabji",
            "2 Roti + Fish Curry + Salad",
            "2 Roti + Mutton Curry + Vegetable Sabji"
        ],
        "non_vegetarian": [
            "2 Roti + Chicken Curry + Vegetable Sabji + Salad",
            "2 Roti + Fish Curry + Dal + Salad",
            "1 cup Rice + Mutton Curry + Salad",
            "2 Roti + Prawn Curry + Vegetable Sabji",
            "2 Roti + Chicken Curry + Dal + Salad"
        ]
    }
    
    return random.choice(dinner_options.get(diet_type, dinner_options["vegetarian"]))

# Additional Routes for Patient Welcome Page
@app.route('/patient/form')
def patient_form():
    return redirect('/patient')

@app.route('/animal/form')
def animal_form():
    return redirect('/animal/health')

@app.route('/patient/queue')
def patient_queue():
    patients_data = load_patients()
    waiting_patients = {pid: pdata for pid, pdata in patients_data.items() if pdata.get('status') == 'waiting'}
    return render_template("patient_queue.html", patients=waiting_patients)

@app.route('/api/patient/emergency', methods=['POST'])
def patient_emergency():
    # Handle emergency SOS
    return jsonify({'success': True, 'message': 'Emergency alert sent to nearby hospitals'})

# API Routes for Chat and Records
@app.route('/api/doctor/records')
def get_doctor_records():
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    doctor_id = session.get('doctor_id')
    conn = get_db_connection()
    records = conn.execute('''
        SELECT * FROM doctor_records 
        WHERE doctor_id = ? 
        ORDER BY prescription_date DESC
    ''', (doctor_id,)).fetchall()
    conn.close()
    
    records_list = []
    for record in records:
        records_list.append({
            'id': record['id'],
            'patient_id': record['patient_id'],
            'patient_name': record['patient_name'],
            'village': record['village'],
            'prescription': record['prescription'],
            'prescription_date': record['prescription_date'],
            'status': record['status']
        })
    
    return jsonify(records_list)

@app.route('/api/doctor/chat-patients')
def get_chat_patients():
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    doctor_id = session.get('doctor_id')
    conn = get_db_connection()
    
    # Get unique patients who have sent messages to this doctor
    messages = conn.execute('''
        SELECT DISTINCT patient_id 
        FROM messages 
        WHERE doctor_id = ? 
        ORDER BY timestamp DESC
    ''', (doctor_id,)).fetchall()
    
    patients = []
    patients_data = load_patients()
    animals_data = load_animals()
    
    for msg in messages:
        patient_id = msg['patient_id']
        
        # Check if it's a human patient
        if patient_id in patients_data:
            pdata = patients_data[patient_id]
            # Get last message
            last_message = conn.execute(
                'SELECT content FROM messages WHERE patient_id = ? AND doctor_id = ? ORDER BY timestamp DESC LIMIT 1',
                (patient_id, doctor_id)
            ).fetchone()
            
            patients.append({
                'id': patient_id,
                'name': pdata['name'],
                'type': 'human',
                'village': pdata.get('city', ''),
                'last_message': last_message['content'] if last_message else 'New patient'
            })
        
        # Check if it's an animal patient
        elif patient_id in animals_data:
            animal_data = animals_data[patient_id]
            # Get last message
            last_message = conn.execute(
                'SELECT content FROM messages WHERE patient_id = ? AND doctor_id = ? ORDER BY timestamp DESC LIMIT 1',
                (patient_id, doctor_id)
            ).fetchone()
            
            patients.append({
                'id': patient_id,
                'name': f"{animal_data['animal_name']} ({animal_data['animal_type']})",
                'type': 'animal',
                'village': animal_data.get('village', ''),
                'last_message': last_message['content'] if last_message else 'New animal patient'
            })
    
    conn.close()
    return jsonify(patients)

@app.route('/api/veterinarian/chat-animals')
def get_chat_animals():
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    # Check if doctor is a veterinarian
    if session.get('doctor_type') != 'veterinarian':
        return jsonify({'error': 'Not a veterinarian'}), 403
    
    doctor_id = session.get('doctor_id')
    
    # Get unique animals who have sent messages to this veterinarian
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT DISTINCT patient_id 
        FROM messages 
        WHERE doctor_id = ? 
        ORDER BY timestamp DESC
    ''', (doctor_id,)).fetchall()
    
    animals = []
    animals_data = load_animals()
    
    for msg in messages:
        animal_id = msg['patient_id']
        if animal_id.startswith('animal_') and animal_id in animals_data:
            animal_data = animals_data[animal_id]
            # Get last message time
            last_message = conn.execute(
                'SELECT content FROM messages WHERE patient_id = ? AND doctor_id = ? ORDER BY timestamp DESC LIMIT 1',
                (animal_id, doctor_id)
            ).fetchone()
            
            animals.append({
                'id': animal_id,
                'name': f"{animal_data['animal_name']} ({animal_data['animal_type']})",
                'type': 'animal',
                'village': animal_data.get('village', ''),
                'last_message': last_message['content'] if last_message else 'New animal patient'
            })
    
    conn.close()
    return jsonify(animals)

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

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        message = data.get('message')
        sender_type = data.get('sender_type', 'doctor')
        image_data = data.get('image_data')
        
        if not message and not image_data:
            return jsonify({'error': 'Message or image required'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO messages (patient_id, doctor_id, message_type, content, sender_type, image_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, 'text', message or 'Image message', sender_type, image_data))
        conn.commit()
        conn.close()
        
        # Emit socket event for real-time updates
        socketio.emit('new_message', {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'message': message,
            'sender_type': sender_type,
            'image_data': image_data,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/animal/chat/send', methods=['POST'])
def send_animal_chat_message():
    try:
        data = request.get_json()
        animal_id = data.get('animal_id')
        doctor_id = data.get('doctor_id')
        message = data.get('message')
        sender_type = data.get('sender_type', 'animal_owner')
        image_data = data.get('image_data')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO messages (patient_id, doctor_id, message_type, content, sender_type, image_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (animal_id, doctor_id, 'text', message or 'Image message', sender_type, image_data))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        return jsonify({'error': 'System error'}), 500

@app.route('/api/doctor/clear', methods=['POST'])
def clear_all_patients():
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    patients_data = {}
    save_patients(patients_data)
    return jsonify({'success': True})

# Socket.IO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'🔌 Client connected: {request.sid}')
    emit('connection_established', {'message': 'Connected to server', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'❌ Client disconnected: {request.sid}')

@socketio.on('join_patient_room')
def handle_join_patient_room(data):
    """Patient joins their specific room"""
    patient_id = data.get('patient_id')
    if patient_id:
        join_room(f"patient_{patient_id}")
        print(f'👤 Patient {patient_id} joined room')

@socketio.on('join_doctor_room')
def handle_join_doctor_room(data):
    """Doctor joins their specific room"""
    doctor_id = data.get('doctor_id')
    if doctor_id:
        join_room(f"doctor_{doctor_id}")
        print(f'👨‍⚕️ Doctor {doctor_id} joined room')

@socketio.on('join_chat_room')
def handle_join_chat_room(data):
    """Join a specific chat room for patient-doctor conversation"""
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    room_id = f"chat_{patient_id}_{doctor_id}"
    join_room(room_id)
    print(f'💬 User joined chat room: {room_id}')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending messages in real-time"""
    try:
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        message = data.get('message')
        sender_type = data.get('sender_type')
        image_data = data.get('image_data')
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO messages (patient_id, doctor_id, message_type, content, sender_type, image_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, 'text', message or 'Image message', sender_type, image_data))
        conn.commit()
        
        # Get the saved message with ID
        saved_message = conn.execute(
            'SELECT * FROM messages WHERE id = last_insert_rowid()'
        ).fetchone()
        conn.close()
        
        # Prepare message data for broadcasting
        message_data = {
            'id': saved_message['id'],
            'patient_id': saved_message['patient_id'],
            'doctor_id': saved_message['doctor_id'],
            'content': saved_message['content'],
            'sender_type': saved_message['sender_type'],
            'image_data': saved_message['image_data'],
            'timestamp': saved_message['timestamp'],
            'message_type': saved_message['message_type']
        }
        
        # Broadcast to specific chat room
        room_id = f"chat_{patient_id}_{doctor_id}"
        emit('new_message', message_data, room=room_id)
        
        # Also notify both participants in their personal rooms
        emit('message_notification', {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'message': message,
            'sender_type': sender_type,
            'timestamp': datetime.now().isoformat()
        }, room=f"patient_{patient_id}")
        
        emit('message_notification', {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'message': message,
            'sender_type': sender_type,
            'timestamp': datetime.now().isoformat()
        }, room=f"doctor_{doctor_id}")
        
        print(f'💬 Message sent in room {room_id}: {message[:50]}...')
        
    except Exception as e:
        print(f'❌ Error sending message: {str(e)}')
        emit('message_error', {'error': 'Failed to send message'})

@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicators"""
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    sender_type = data.get('sender_type')
    
    room_id = f"chat_{patient_id}_{doctor_id}"
    emit('user_typing', {
        'patient_id': patient_id,
        'doctor_id': doctor_id,
        'sender_type': sender_type,
        'typing': True
    }, room=room_id)

@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle typing stop indicators"""
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    sender_type = data.get('sender_type')
    
    room_id = f"chat_{patient_id}_{doctor_id}"
    emit('user_typing', {
        'patient_id': patient_id,
        'doctor_id': doctor_id,
        'sender_type': sender_type,
        'typing': False
    }, room=room_id)

# Enhanced notification handlers
@socketio.on('new_patient_notification')
def handle_new_patient_notification(data):
    """Notify doctors about new patients"""
    emit('new_patient_alert', data, room='doctors')
    print(f'🆕 New patient notification: {data}')

@socketio.on('new_animal_patient_notification')
def handle_new_animal_patient(data):
    """Notify veterinarians about new animal patients"""
    emit('new_animal_patient_alert', data, room='veterinarians')
    print(f'🐾 New animal patient: {data}')

@socketio.on('prescription_notification')
def handle_prescription_notification(data):
    """Notify patients about new prescriptions"""
    patient_id = data.get('patient_id')
    emit('prescription_ready', data, room=f"patient_{patient_id}")
    print(f'📝 Prescription ready for patient: {patient_id}')

@socketio.on('animal_prescription_notification')
def handle_animal_prescription(data):
    """Notify animal owners about prescriptions"""
    animal_id = data.get('animal_id')
    emit('animal_prescription_ready', data, room=f"animal_{animal_id}")
    print(f'🐾 Animal prescription ready: {animal_id}')

# Join specific notification rooms
@socketio.on('join_doctors_room')
def handle_join_doctors_room():
    """Doctors join the general doctors room for notifications"""
    join_room('doctors')
    print(f'👨‍⚕️ Doctor joined doctors room: {request.sid}')

@socketio.on('join_veterinarians_room')
def handle_join_veterinarians_room():
    """Veterinarians join their notification room"""
    join_room('veterinarians')
    print(f'🐾 Veterinarian joined room: {request.sid}')

if __name__ == '__main__':
    print("🚀 Health Kiosk Server Starting with Socket.IO...")
    print("📍 Patient Portal: http://127.0.0.1:5000/patient/welcome")
    print("📍 Doctor Portal:  http://127.0.0.1:5000/doctor/welcome")
    print("📍 Doctor Login: http://127.0.0.1:5000/doctor/login")
    print("📍 Animal Health: http://127.0.0.1:5000/animal/health")
    print("📍 Veterinarian Dashboard: http://127.0.0.1:5000/veterinarian/dashboard")
    print("📍 Balance Diet: http://127.0.0.1:5000/balance_diet")
    print("📍 Patient Chat: http://127.0.0.1:5000/patient/chat")
    print("📍 Animal Chat: http://127.0.0.1:5000/animal/chat")
    print("📍 Doctor Chat: http://127.0.0.1:5000/doctor/chat")
    print("\n🔐 Fixed Login Credentials:")
    print("   Human Doctor: Username: Pratik, Password: 1714")
    print("   Veterinarian: Username: Shreyas, Password: 2025")
    print("\n🔌 Socket.IO running on: ws://127.0.0.1:5000/socket.io/")
    
    socketio.run(app, 
                host="0.0.0.0", 
                port=5000, 
                debug=True, 
                allow_unsafe_werkzeug=True)