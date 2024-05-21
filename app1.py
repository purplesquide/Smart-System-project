import sqlite3
from flask import flash
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np
from NLP import extract_disease_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
db = SQLAlchemy(app)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __init__(self, email, password, name):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.name = name

def create_initial_admin():
    admin_count = Admin.query.count()
    if admin_count == 0:
        admin = Admin(email='admin@mail.com', password='123456789', name='wassim')
        db.session.add(admin)
        db.session.commit()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    appointments = db.relationship('Appointment', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def __init__(self, first_name, last_name, email, password, phone):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.phone = phone

class EHR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, doctor_id, content):
        self.user_id = user_id
        self.doctor_id = doctor_id
        self.content = content

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unread')
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)  # New field
    diagnosis_id = db.Column(db.Integer, db.ForeignKey('diagnosis.id'), nullable=True)  # New field

    def __init__(self, user_id, message, appointment_id=None, diagnosis_id=None):
        self.user_id = user_id
        self.message = message
        self.appointment_id = appointment_id
        self.diagnosis_id = diagnosis_id




class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    speciality = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')

    def __init__(self, name, email, speciality, phone, password):
        self.name = name
        self.email = email
        self.speciality = speciality
        self.phone = phone
        self.password_hash = generate_password_hash(password)


class Diagnosis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False) 
    filename = db.Column(db.String(120), nullable=False)
    disease_name = db.Column(db.String(80), nullable=False)
    prediction_result = db.Column(db.String(120), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, doctor_id, filename, disease_name, prediction_result, note=None):
        self.user_id = user_id  
        self.doctor_id = doctor_id 
        self.filename = filename
        self.disease_name = disease_name
        self.prediction_result = prediction_result
        self.note = note



class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False)
    suggested_time = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.String(255), nullable=True)  # New field for doctor's note
    notifications = db.relationship('Notification', backref='appointment', lazy='dynamic')  # New relationship

    def __init__(self, user_id, doctor_id, date, time, phone, address, note=None):
        self.user_id = user_id
        self.doctor_id = doctor_id
        self.date = date
        self.time = time
        self.phone = phone
        self.address = address
        self.note = note





# Rest of the code remains the same...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return 'Email already registered'

        new_user = User(first_name=first_name, last_name=last_name, email=email, password=password, phone=phone)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard', page='home'))
        else:
            return 'Invalid email or password'
    return render_template('admin_login.html')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    admin_id = session['admin_id']
    admin = db.session.get(Admin, admin_id)

    if admin is None:
        return redirect(url_for('admin_login'))
    
    if request.method == 'GET':
        return render_template('admin.html', admin=admin)
    
    return render_template('admin.html', admin=admin)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        patient = User.query.filter_by(email=email).first()
        if patient and check_password_hash(patient.password_hash, password):
            session['user_id'] = patient.id
            return redirect(url_for('patient_dashboard'))
        else:
            return 'Invalid email or password'

    return render_template('login.html', role='patient')

@app.route('/patient-dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    if user is None:
        return redirect(url_for('login'))

    return render_template('patient.html', user=user)

@app.route('/make_appointment', methods=['GET', 'POST'])
def make_appointment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        doctor_id = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if not doctor_id or not date or not time or not phone or not address:
            flash('All fields are required.', 'error')
        else:
            appointment = Appointment(
                user_id=user_id,
                doctor_id=doctor_id,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                time=datetime.strptime(time, '%H:%M').time(),
                phone=phone,
                address=address
            )

            try:
                db.session.add(appointment)
                db.session.commit()
                flash('Appointment scheduled successfully!', 'success')
                return redirect(url_for('patient_dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error scheduling appointment: {e}', 'error')

    doctors = Doctor.query.all()
    return render_template('make-appointment.html', doctors=doctors)


@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)

    if user is None:
        return redirect(url_for('login'))

    notifications = Notification.query.filter_by(user_id=user_id).all()

    notification_details = []

    for notification in notifications:
        detail = {
            'id': notification.id,  # Ensure ID is passed
            'message': notification.message,
            'date': notification.date,
            'status': notification.status
        }
        if notification.appointment_id:
            appointment = Appointment.query.get(notification.appointment_id)
            if appointment:
                detail['appointment'] = {
                    'date': appointment.date,
                    'time': appointment.time,
                    'phone': appointment.phone,
                    'address': appointment.address,
                    'status': appointment.status,
                    'suggested_time': appointment.suggested_time,
                    'note': appointment.note
                }
        if notification.diagnosis_id:
            diagnosis = Diagnosis.query.get(notification.diagnosis_id)
            if diagnosis:
                detail['diagnosis'] = {
                    'disease_name': diagnosis.disease_name,
                    'prediction_result': diagnosis.prediction_result,
                    'note': diagnosis.note
                }

        notification_details.append(detail)

    return render_template('notifications.html', notifications=notification_details)


@app.route('/delete_notification/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    notification = Notification.query.get(notification_id)

    if notification and notification.user_id == user_id:
        db.session.delete(notification)
        db.session.commit()
        flash('Notification deleted successfully!', 'success')
    else:
        flash('Notification not found or you do not have permission to delete it.', 'error')

    return redirect(url_for('notifications'))


@app.route('/view_health_analysis')
def view_health_analysis():
    if 'user_id' not in session:
        flash('You need to be logged in to view your health analysis', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)

    if user is None:
        flash('Invalid user session', 'error')
        return redirect(url_for('login'))

    ehr = EHR.query.filter_by(user_id=user_id).first()

    if ehr is None:
        flash('No health analysis found for this user', 'error')
        return redirect(url_for('patient_dashboard'))

    return render_template('view_health_analysis.html', user=user, ehr=ehr)


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('You need to be logged in to edit your profile', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash('Invalid user session', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if the current password is correct
        if not check_password_hash(user.password_hash, current_password):
            flash('Incorrect current password', 'error')
            return redirect(url_for('edit_profile'))

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            flash('New password and confirm password do not match', 'error')
            return redirect(url_for('edit_profile'))

        # Update the user's information in the database
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_dashboard'))

    return render_template('edit-profile.html', user=user)


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    admin_id = session['admin_id']
    admin = db.session.get(Admin, admin_id)

    if admin is None:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        doctor_name = request.form['name']
        email = request.form['email']
        speciality = request.form['speciality']
        phone = request.form['phone']
        password = request.form.get('password')

        if not doctor_name or not email or not speciality or not phone or not password:
           
            return render_template('add-doctor.html', admin=admin)
        elif speciality not in ['endocrinology', 'cardiology']:
          
            return render_template('add-doctor.html', admin=admin)
        else:
            existing_doctor = Doctor.query.filter_by(email=email).first()
            if existing_doctor:
                
                return render_template('add-doctor.html', admin=admin)
            else:
                new_doctor = Doctor(name=doctor_name, email=email, speciality=speciality, phone=phone, password=password)
                try:
                    db.session.add(new_doctor)
                except Exception as e:
                    db.session.rollback()
                    
                    return render_template('add-doctor.html', admin=admin)
                else:
                    db.session.commit()
                    flash('Doctor added successfully!', 'success')
                    return redirect(url_for('admin_dashboard'))

    return render_template('add-doctor.html', admin=admin)

@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        doctor = Doctor.query.filter_by(email=email).first()
        if doctor and check_password_hash(doctor.password_hash, password):
            session['doctor_id'] = doctor.id
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('doctor_login.html')

@app.route('/doctor_dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = db.session.get(Doctor, doctor_id)
    
    if doctor is None:
        return redirect(url_for('doctor_login'))

    appointments = doctor.appointments.all()
    return render_template('doctor.html', doctor=doctor, appointments=appointments)

@app.route('/doctor_dashboard/patients')
def doctor_patients():
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = db.session.get(Doctor, doctor_id)

    if doctor is None:
        return redirect(url_for('doctor_login'))

    patients = User.query.join(Appointment, Appointment.user_id == User.id).filter(Appointment.doctor_id == doctor.id).all()
    return render_template('doctor_patients.html', doctor=doctor, patients=patients)

from werkzeug.utils import secure_filename


@app.route('/doctor_dashboard/user/<int:user_id>', methods=['GET', 'POST'])
def manage_ehr(user_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = db.session.get(Doctor, doctor_id)
    user = db.session.get(User, user_id)

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.txt'):
                filename = secure_filename(file.filename)
                file_contents = file.read().decode('utf-8')

                existing_ehr = EHR.query.filter_by(user_id=user.id).first()
                if existing_ehr:
                    existing_ehr.content = file_contents
                else:
                    new_ehr = EHR(user_id=user.id, doctor_id=doctor.id, content=file_contents)
                    db.session.add(new_ehr)
                db.session.commit()
                flash('EHR updated successfully!', 'success')
            else:
                flash('Invalid file type. Only .txt files are allowed.', 'error')

    ehr = EHR.query.filter_by(user_id=user.id).first()
    return render_template('manage_ehr.html', doctor=doctor, user=user, ehr=ehr)

@app.route('/update_ehr/<int:user_id>', methods=['POST'])
def update_ehr(user_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = db.session.get(Doctor, doctor_id)
    user = db.session.get(User, user_id)

    if not doctor or not user:
        flash('Invalid request', 'error')
        return redirect(url_for('doctor_dashboard'))

    ehr = EHR.query.filter_by(user_id=user_id).first()
    if not ehr:
        flash('No EHR found for this user', 'error')
        return redirect(url_for('manage_ehr', user_id=user_id))

    new_content = request.form.get('content')
    if not new_content:
        flash('No new content provided', 'error')
        return redirect(url_for('manage_ehr', user_id=user_id))

    ehr.content = new_content
    db.session.commit()
    flash('EHR updated successfully!', 'success')

    return redirect(url_for('manage_ehr', user_id=user_id))

# Diagnosis Route


heart_model = joblib.load('heartmodel.pkl')
heart_scaler = joblib.load('scaler1.pkl')
diabetes_model = joblib.load('diabetesmodel.pkl')
diabetes_scaler = joblib.load('scaler.pkl')

@app.route('/diagnosis', methods=['GET', 'POST'])
def diagnosis():
    if 'doctor_id' not in session:
        flash('You need to be logged in as a doctor to make a diagnosis', 'error')
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = Doctor.query.get(doctor_id)

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        note = request.form.get('note')
        user = User.query.get(user_id)

        # Ensure the selected user has an appointment with the logged-in doctor
        appointment = Appointment.query.filter_by(user_id=user_id, doctor_id=doctor_id).first()
        if not appointment:
            flash('You do not have permission to diagnose this user', 'error')
            return redirect(url_for('diagnosis'))

        ehr = EHR.query.filter_by(user_id=user.id).first()

        if not ehr:
            flash('No EHR found for this user', 'error')
            return redirect(url_for('diagnosis'))

        file_contents = ehr.content

        specialty_disease_map = {
            'endocrinology': 'diabetes',
            'cardiology': 'heart'
        }

        disease_name = specialty_disease_map.get(doctor.speciality.lower())
        if not disease_name:
            return render_template('diagnosis.html', prediction=f"Doctor with specialty {doctor.speciality} cannot diagnose diseases.")

        if disease_name == 'heart':
            heart_data = extract_disease_data('heart', file_contents)
            if heart_data:
                ind_nparr = np.asarray(heart_data)
                ind_reshaped = ind_nparr.reshape(1, -1)
                std_data = heart_scaler.transform(ind_reshaped)
                prediction = heart_model.predict(std_data)[0]
                prediction_message = "The user has heart disease." if prediction == 1 else "The user does not have heart disease."
            else:
                prediction_message = "No numeric heart disease data found in the clinical note."
        elif disease_name == 'diabetes':
            diabetes_data = extract_disease_data('diabetes', file_contents)
            if diabetes_data:
                ind_nparr = np.asarray(diabetes_data)
                ind_reshaped = ind_nparr.reshape(1, -1)
                std_data = diabetes_scaler.transform(ind_reshaped)
                prediction = diabetes_model.predict(std_data)[0]
                prediction_message = "The user is diabetic." if prediction == 1 else "The user is not diabetic."
            else:
                prediction_message = "No numeric diabetes data found in the clinical note."
        else:
            prediction_message = "No matching disease found for the doctor's specialty."

        # Assuming 'filename' is required but not used for now
        # Use a placeholder filename or generate a unique filename
        filename = f'{user_id}_ehr.txt'

        diagnosis = Diagnosis(
            doctor_id=doctor_id,
            user_id=user.id,
            filename=filename,  # Add the filename argument here
            disease_name=disease_name,
            prediction_result=prediction_message,
            note=note
        )

        db.session.add(diagnosis)
        db.session.commit()

        notification = Notification(user_id=user.id, message=f'You have a new diagnosis: {prediction_message}. Note: {note}', diagnosis_id=diagnosis.id)
        db.session.add(notification)
        db.session.commit()

        return render_template('diagnosis.html', prediction=prediction_message)

    users = User.query.join(Appointment, User.id == Appointment.user_id).filter(Appointment.doctor_id == doctor_id).all()
    return render_template('diagnosis.html', users=users)





@app.route('/doctor_patients')
def list_doctor_patients():
    if 'doctor_id' not in session:
        flash('You need to be logged in as a doctor to view your patients', 'error')
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = Doctor.query.get(doctor_id)
    
    if not doctor:
        return redirect(url_for('doctor_login'))

    # Get the doctor's appointments to find the patients
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()
    patients = {appointment.user for appointment in appointments}

    return render_template('doctor_patients.html', doctor=doctor, patients=patients)

@app.route('/manage_appointments', methods=['GET', 'POST'])
def manage_appointments():

    if 'doctor_id' not in session:
        flash('You need to be logged in as a doctor to view your patients', 'error')
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = Doctor.query.get(doctor_id)
    
    if not doctor:
        return redirect(url_for('doctor_login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        appointment_id = request.form.get('appointment_id')
        appointment = Appointment.query.get(appointment_id)
        note = request.form.get('note')

        if action == 'accept':
            appointment.status = 'Accepted'
            message = f'Your appointment on {appointment.date} at {appointment.time} has been accepted.'
        elif action == 'suggest':
            suggested_time = request.form.get('suggested_time')
            appointment.suggested_time = datetime.fromisoformat(suggested_time)
            appointment.status = 'Suggested'
            appointment.note = note  # Save doctor's note
            message = f'New suggested time for your appointment: {suggested_time}. Note: {note}'
        elif action == 'delete':
            db.session.delete(appointment)
            db.session.commit()
            return redirect(url_for('manage_appointments'))

        db.session.commit()

        # Create a notification for the user
        notification = Notification(user_id=appointment.user_id, message=message, appointment_id=appointment.id)
        db.session.add(notification)
        db.session.commit()

  # Filter appointments for the logged-in doctor
    pending_appointments = Appointment.query.filter_by(status='Pending', doctor=doctor).all()
    managed_appointments = Appointment.query.filter(Appointment.status.in_(['Accepted', 'Suggested']), Appointment.doctor == doctor).all()

    return render_template('manage-appointments.html', pending_appointments=pending_appointments, managed_appointments=managed_appointments)

@app.route('/edit-doctor-profile', methods=['GET', 'POST'])
def edit_doctor_profile():
    if 'doctor_id' not in session:
        flash('You need to be logged in as a doctor to edit your profile', 'error')
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        flash('Invalid doctor session', 'error')
        return redirect(url_for('doctor_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if the current password is correct
        if not check_password_hash(doctor.password_hash, current_password):
            flash('Incorrect current password', 'error')
            return redirect(url_for('edit_profile'))

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            flash('New password and confirm password do not match', 'error')
            return redirect(url_for('edit_profile'))

        # Update the doctor's information in the database
        doctor.name = name
        doctor.email = email
        doctor.phone = phone
        if new_password:
            doctor.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))

    return render_template('edit-doctor-profile.html', doctor=doctor)




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/doctor_logout')
def doctor_logout():
    session.clear()
    return redirect(url_for('doctor_login'))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_initial_admin()
    app.run(debug=True)