import io
import csv
import time
from flask import Response, Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import base64
from PIL import Image
import face_recognition
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face_recognition.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

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

# --- Helper Functions ---
def load_known_faces():
    global known_face_encodings, known_face_data
    known_face_encodings, known_face_data = [], []
    try:
        students = Student.query.all()
        for student in students:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
            if os.path.exists(photo_path):
                try:
                    student_image = face_recognition.load_image_file(photo_path)
                    face_encodings = face_recognition.face_encodings(student_image)
                    if face_encodings:
                        known_face_encodings.append(face_encodings[0])
                        known_face_data.append({
                            "id": student.id, "student_id": student.student_id,
                            "name": student.name, "roll": student.roll,
                            "department": student.department
                        })
                except Exception as e:
                    print(f"Error processing {student.photo}: {e}")
    except Exception as e:
        print(f"Error loading faces from DB: {e}")

# --- Main Routes ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'], session['user_name'] = user.id, f"{user.fname} {user.lname}"
            session['is_admin'] = user.is_admin
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        new_user = User(
            fname=request.form['fname'], lname=request.form['lname'],
            contact=request.form['contact'], email=request.form['email'],
            securityQ=request.form['securityQ'], securityA=request.form['securityA'],
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    total_students = Student.query.count()
    return render_template('dashboard.html', total_students=total_students)

@app.route('/students')
def students():
    if 'user_id' not in session: return redirect(url_for('login'))
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files.get('photo')
        
        if not file or file.filename == '':
            flash('No photo was selected for upload.', 'error')
            return redirect(request.url)
        
        original_filename = secure_filename(file.filename)
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
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
            photo=unique_filename
        )
        db.session.add(new_student)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('students'))
        
    return render_template('add_student.html')

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            original_filename = secure_filename(file.filename)
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            if student.photo and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], student.photo)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], student.photo))
            
            student.photo = unique_filename
        
        student.student_id = request.form['student_id']
        student.name = request.form['name']
        student.roll = request.form['roll']
        student.department = request.form['department']
        student.course = request.form['course']
        student.year = request.form['year']
        student.semester = request.form['semester']
        student.division = request.form['division']
        student.gender = request.form['gender']
        student.dob = request.form['dob']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.address = request.form['address']
        student.teacher = request.form['teacher']

        db.session.commit()
        
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('students'))
        
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    student = Student.query.get_or_404(student_id)
    if student.photo:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
        if os.path.exists(photo_path): os.remove(photo_path)
    Attendance.query.filter_by(student_id=student.student_id).delete()
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} deleted.', 'success')
    return redirect(url_for('students'))

@app.route('/face_recognition_page')
def face_recognition_page():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('face_recognition.html')

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    selected_date = request.args.get('date', datetime.now().strftime('%d/%m/%Y'))

    all_students = Student.query.all()
    attendance_records = Attendance.query.filter_by(date=selected_date).all()
    attendance_status = {rec.student_id: {'status': rec.status, 'time': rec.time} for rec in attendance_records}

    student_attendance_data = []
    for student in all_students:
        status_info = attendance_status.get(student.student_id)
        if status_info:
            student_attendance_data.append({
                'student': student,
                'status': status_info['status'],
                'time': status_info['time'],
                'date': selected_date
            })
        else:
            student_attendance_data.append({
                'student': student,
                'status': 'Absent',
                'time': 'N/A',
                'date': selected_date
            })

    available_dates = [r[0] for r in db.session.query(Attendance.date).distinct().order_by(Attendance.date.desc()).all()]
    if selected_date not in available_dates:
        available_dates.insert(0, selected_date)

    return render_template(
        'attendance.html', 
        student_attendance_data=student_attendance_data, 
        selected_date=selected_date,
        available_dates=available_dates
    )

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session: return redirect(url_for('login'))
    student_id, date, status = request.form.get('student_id'), request.form.get('date'), request.form.get('status')
    student = Student.query.filter_by(student_id=student_id).first()
    if student:
        mark_attendance_for_student(student, date=date, status=status)
        flash(f"Attendance for {student.name} marked as {status}.", 'success')
    else:
        flash('Student not found.', 'error')
    return redirect(url_for('attendance', date=date))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def mark_attendance_for_student(student, date=None, status=None):
    try:
        mark_date = date or datetime.now().strftime('%d/%m/%Y')
        mark_status = status or 'Present'
        
        existing = Attendance.query.filter_by(student_id=student.student_id, date=mark_date).first()
        if existing:
            existing.status = mark_status
            existing.time = datetime.now().strftime('%H:%M:%S') if mark_status == 'Present' else 'N/A'
        else:
            new_attendance = Attendance(
                student_id=student.student_id, roll=student.roll, name=student.name,
                department=student.department, date=mark_date, status=mark_status,
                time=datetime.now().strftime('%H:%M:%S') if mark_status == 'Present' else 'N/A'
            )
            db.session.add(new_attendance)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error marking attendance: {str(e)}")


@app.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    date_to_export = request.args.get('date')
    if not date_to_export:
        flash('No date selected for export.', 'error')
        return redirect(url_for('attendance'))

    all_students = Student.query.all()
    attendance_records = Attendance.query.filter_by(date=date_to_export).all()
    attendance_status = {rec.student_id: {'status': rec.status, 'time': rec.time} for rec in attendance_records}

    output = io.StringIO()
    writer = csv.writer(output)
    
    header = ['Student ID', 'Name', 'Roll Number', 'Department', 'Date', 'Status', 'Time']
    writer.writerow(header)
    
    for student in all_students:
        status_info = attendance_status.get(student.student_id)
        if status_info:
            row = [student.student_id, student.name, student.roll, student.department, date_to_export, status_info['status'], status_info['time']]
        else:
            row = [student.student_id, student.name, student.roll, student.department, date_to_export, 'Absent', 'N/A']
        writer.writerow(row)
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{date_to_export.replace('/', '-')}.csv"}
    )

# --- API Routes ---
@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    if 'user_id' not in session: return jsonify({'error': 'Not authenticated'}), 401
    try:
        image_data = request.json.get('image').split(',')[1]
        rgb_image = np.array(Image.open(io.BytesIO(base64.b64decode(image_data)).convert("RGB")))
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            return jsonify({'message': 'No face detected'})

        recognized_students = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    student_data = known_face_data[best_match_index]
                    student_obj = Student.query.get(student_data['id'])
                    mark_attendance_for_student(student_obj)
                    recognized_students.append({'student': student_data})
        
        if recognized_students:
            return jsonify({'message': 'Recognition successful', 'recognized_students': recognized_students})
        else:
            return jsonify({'message': 'Face detected but not recognized'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
def retrain_faces():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    load_known_faces()
    return jsonify({'message': 'Face data reloaded!'})

# --- App Initialization ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@admin.com').first():
            admin_user = User(
                fname='Admin', lname='User', contact='1234567890',
                email='admin@admin.com', securityQ='Admin', securityA='Admin',
                password=generate_password_hash('admin123'), is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
        load_known_faces()
    app.run(debug=True, host='0.0.0.0', port=5000)