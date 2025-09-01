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
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face_recognition.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
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

# Routes
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
    
    # Get counts for dashboard
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
        # Handle file upload
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
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
    
    return render_template('add_student.html')

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    try:
        # Find the student
        student = Student.query.get_or_404(student_id)
        
        # Delete the photo file if it exists
        if student.photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        # Delete attendance records for this student
        Attendance.query.filter_by(student_id=student.student_id).delete()
        
        # Delete the student
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Student {student.name} deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('students'))

@app.route('/face_recognition')
def face_recognition():
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

# API Routes for AJAX
@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get image data from request
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'No image data'}), 400
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Face detection using Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return jsonify({'message': 'No face detected', 'faces_count': 0})
        
        # For now, we'll use a simple approach: compare with stored student photos
        # In a production system, you'd use a trained face recognition model
        recognized_student = recognize_student_face(opencv_image, gray, faces)
        
        if recognized_student:
            # Mark attendance automatically
            attendance_result = mark_attendance_for_student(recognized_student)
            return jsonify({
                'message': 'Face recognized successfully!',
                'faces_count': len(faces),
                'student': {
                    'name': recognized_student.name,
                    'roll': recognized_student.roll,
                    'department': recognized_student.department,
                    'student_id': recognized_student.student_id
                },
                'attendance': attendance_result
            })
        else:
            return jsonify({
                'message': 'Face detected but not recognized',
                'faces_count': len(faces),
                'suggestion': 'Student may not be registered in the system'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def recognize_student_face(image, gray, faces):
    """
    Simple face recognition by comparing with stored student photos
    This is a basic implementation - in production, use a proper face recognition model
    """
    try:
        # Get all students with photos
        students = Student.query.filter(Student.photo.isnot(None)).all()
        
        if not students:
            return None
        
        # For each detected face, try to find a match
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size for comparison
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Compare with each student's photo
            best_match = None
            best_score = 0
            
            for student in students:
                if student.photo:
                    try:
                        # Load student photo
                        student_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
                        if os.path.exists(student_photo_path):
                            student_img = cv2.imread(student_photo_path, cv2.IMREAD_GRAYSCALE)
                            if student_img is not None:
                                # Resize student photo to same size
                                student_img = cv2.resize(student_img, (100, 100))
                                
                                # Multiple comparison methods for better accuracy
                                scores = []
                                
                                # Method 1: Template matching
                                result1 = cv2.matchTemplate(face_roi, student_img, cv2.TM_CCOEFF_NORMED)
                                scores.append(np.max(result1))
                                
                                # Method 2: Histogram comparison
                                hist1 = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
                                hist2 = cv2.calcHist([student_img], [0], None, [256], [0, 256])
                                hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                                scores.append(max(0, hist_score))  # Normalize to 0-1
                                
                                # Method 3: Structural similarity (if available)
                                try:
                                    from skimage.metrics import structural_similarity as ssim
                                    ssim_score = ssim(face_roi, student_img)
                                    scores.append(max(0, ssim_score))
                                except ImportError:
                                    # Fallback to basic correlation
                                    correlation = np.corrcoef(face_roi.flatten(), student_img.flatten())[0, 1]
                                    scores.append(max(0, correlation) if not np.isnan(correlation) else 0)
                                
                                # Calculate average score
                                avg_score = np.mean(scores)
                                
                                if avg_score > best_score and avg_score > 0.5:  # Lower threshold for better recognition
                                    best_score = avg_score
                                    best_match = student
                                    print(f"Student {student.name} matched with score: {avg_score:.3f}")
                                    
                    except Exception as e:
                        print(f"Error processing student photo {student.photo}: {e}")
                        continue
            
            if best_match:
                return best_match
        
        return None
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        return None

def mark_attendance_for_student(student):
    """
    Mark attendance for a recognized student
    """
    try:
        # Check if already marked today
        today = datetime.now().strftime('%d/%m/%Y')
        existing = Attendance.query.filter_by(
            student_id=student.student_id, 
            date=today
        ).first()
        
        if existing:
            return {
                'status': 'already_marked',
                'message': f'Attendance already marked for {student.name} today at {existing.time}'
            }
        
        # Mark attendance
        new_attendance = Attendance(
            student_id=student.student_id,
            roll=student.roll,
            name=student.name,
            department=student.department,
            time=datetime.now().strftime('%H:%M:%S'),
            date=today,
            status='Present'
        )
        
        db.session.add(new_attendance)
        db.session.commit()
        
        return {
            'status': 'marked',
            'message': f'Attendance marked for {student.name} at {new_attendance.time}',
            'time': new_attendance.time
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'status': 'error',
            'message': f'Error marking attendance: {str(e)}'
        }

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        student_id = data.get('student_id')
        roll = data.get('roll')
        name = data.get('name')
        department = data.get('department')
        
        # Check if already marked today
        today = datetime.now().strftime('%d/%m/%Y')
        existing = Attendance.query.filter_by(
            student_id=student_id, 
            date=today
        ).first()
        
        if existing:
            return jsonify({'message': 'Attendance already marked for today'})
        
        # Mark attendance
        new_attendance = Attendance(
            student_id=student_id,
            roll=roll,
            name=name,
            department=department,
            time=datetime.now().strftime('%H:%M:%S'),
            date=today,
            status='Present'
        )
        
        db.session.add(new_attendance)
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_face_recognition')
def test_face_recognition():
    """Test route to verify face recognition system"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get some sample students for testing
    students = Student.query.limit(5).all()
    return render_template('test_face_recognition.html', students=students)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(email='admin@admin.com').first()
        if not admin_user:
            admin_user = User(
                fname='Admin',
                lname='User',
                contact='1234567890',
                email='admin@admin.com',
                securityQ='Your Birth Place',
                securityA='Admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
