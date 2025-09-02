from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from datetime import datetime
import base64
from PIL import Image
import io
import face_recognition # New import for accurate face recognition

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face_recognition.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# --- Globals for Face Recognition Data ---
# These will hold the face encodings and corresponding student data in memory
known_face_encodings = []
known_face_data = []


# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    securityQ = db.Column(db.String(100), nullable=False)
    securityA = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    division = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    roll = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Present')


# --- Face Recognition Helper Functions ---
def load_known_faces():
    """
    Load face encodings and student data from the database and photos.
    This function is called on startup and can be re-called to refresh data.
    """
    global known_face_encodings, known_face_data
    
    # Clear existing data
    known_face_encodings = []
    known_face_data = []

    try:
        students = Student.query.all()
        print(f"Loading {len(students)} student(s) for face recognition...")
        
        for student in students:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
            if os.path.exists(photo_path):
                try:
                    # Load image using face_recognition library
                    student_image = face_recognition.load_image_file(photo_path)
                    
                    # Get face encodings. We assume one face per photo.
                    # The model might not find a face if the image is unclear.
                    face_encodings = face_recognition.face_encodings(student_image)
                    
                    if face_encodings:
                        student_encoding = face_encodings[0]
                        known_face_encodings.append(student_encoding)
                        known_face_data.append({
                            "id": student.id,
                            "student_id": student.student_id,
                            "name": student.name,
                            "roll": student.roll,
                            "department": student.department
                        })
                    else:
                        print(f"Warning: No face found in photo for student {student.name} ({student.photo})")

                except Exception as e:
                    print(f"Error processing photo {student.photo} for {student.name}: {e}")
            else:
                print(f"Warning: Photo not found for student {student.name} at path: {photo_path}")

        print(f"Successfully loaded {len(known_face_encodings)} known faces.")
    except Exception as e:
        print(f"Error loading known faces from database: {e}")

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = f"{user.fname} {user.lname}"
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... (Your existing registration code is fine, no changes needed here) ...
        fname = request.form['fname']
        lname = request.form['lname']
        contact = request.form['contact']
        email = request.form['email']
        securityQ = request.form['securityQ']
        securityA = request.form['securityA']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            fname=fname, lname=lname, contact=contact, email=email,
            securityQ=securityQ, securityA=securityA, password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    total_students = Student.query.count()
    total_attendance = Attendance.query.count()
    today_attendance = Attendance.query.filter_by(date=datetime.now().strftime('%d/%m/%Y')).count()
    return render_template('dashboard.html', 
                         total_students=total_students,
                         total_attendance=total_attendance,
                         today_attendance=today_attendance)

@app.route('/students')
def students():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # ... (Your existing add_student code is fine, no changes needed here) ...
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('add_student.html')
        
        file = request.files['photo']
        if file.filename == '':
            flash('No photo selected', 'error')
            return render_template('add_student.html')
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            new_student = Student(
                student_id=request.form['student_id'],
                name=request.form['name'],
                roll=request.form['roll'],
                department=request.form['department'],
                course=request.form['course'],
                year=request.form['year'],
                semester=request.form['semester'],
                division=request.form['division'],
                gender=request.form['gender'],
                dob=request.form['dob'],
                email=request.form['email'],
                phone=request.form['phone'],
                address=request.form['address'],
                teacher=request.form['teacher'],
                photo=filename
            )
            db.session.add(new_student)
            db.session.commit()
            flash('Student added successfully! Consider reloading faces.', 'success')
            return redirect(url_for('students'))
    return render_template('add_student.html')

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # ... (Your existing delete_student code is fine, no changes needed here) ...
    try:
        student = Student.query.get_or_404(student_id)
        if student.photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        Attendance.query.filter_by(student_id=student.student_id).delete()
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('students'))

@app.route('/face_recognition')
@app.route('/face_recognition_page')
def face_recognition_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('face_recognition.html')

@app.route('/attendance')
def attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    attendance_records = Attendance.query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    return render_template('attendance.html', attendance_records=attendance_records)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


# --- API Routes for AJAX ---

@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    """
    This is the new, improved face recognition endpoint.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Convert to numpy array for face_recognition library
        rgb_image = np.array(image)

        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            return jsonify({'message': 'No face detected', 'faces_count': 0})

        recognized_students = []

        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            
            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    recognized_student_data = known_face_data[best_match_index]
                    
                    # Mark attendance and add to our list for the response
                    attendance_result = mark_attendance_for_student(recognized_student_data)
                    
                    recognized_students.append({
                        'student': recognized_student_data,
                        'attendance': attendance_result
                    })

        if recognized_students:
            return jsonify({
                'message': 'Face(s) recognized successfully!',
                'faces_count': len(face_locations),
                'recognized_students': recognized_students
            })
        else:
            return jsonify({
                'message': 'Face detected but not recognized',
                'faces_count': len(face_locations),
                'suggestion': 'Student may not be registered or photo is unclear.'
            })

    except Exception as e:
        print(f"Error in /api/recognize_face: {e}")
        return jsonify({'error': str(e)}), 500


def mark_attendance_for_student(student_data):
    """
    Mark attendance for a recognized student using their data dictionary.
    """
    try:
        today = datetime.now().strftime('%d/%m/%Y')
        existing = Attendance.query.filter_by(
            student_id=student_data['student_id'], 
            date=today
        ).first()
        
        if existing:
            return {
                'status': 'already_marked',
                'message': f"Attendance already marked for {student_data['name']} today at {existing.time}"
            }
        
        new_attendance = Attendance(
            student_id=student_data['student_id'],
            roll=student_data['roll'],
            name=student_data['name'],
            department=student_data['department'],
            time=datetime.now().strftime('%H:%M:%S'),
            date=today,
            status='Present'
        )
        db.session.add(new_attendance)
        db.session.commit()
        
        return {
            'status': 'marked',
            'message': f"Attendance marked for {student_data['name']} at {new_attendance.time}",
            'time': new_attendance.time
        }
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': f'Error marking attendance: {str(e)}'}

@app.route('/api/retrain', methods=['POST'])
def retrain_faces():
    """
    API endpoint to trigger reloading of known faces from the database.
    """
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    print("Retraining request received. Reloading faces...")
    load_known_faces()
    return jsonify({'message': 'Face data reloaded successfully!'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(email='admin@admin.com').first():
            admin_user = User(
                fname='Admin', lname='User', contact='1234567890',
                email='admin@admin.com', securityQ='Your Birth Place',
                securityA='Admin', password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
        
        # --- IMPORTANT: Load known faces on startup ---
        load_known_faces()
    
    app.run(debug=True, host='0.0.0.0', port=5000)