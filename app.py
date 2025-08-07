from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime 
from datetime import datetime
from flask import send_from_directory
from sqlalchemy.orm import Session



# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ZUGWAI@localhost:5432/logbook'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define user_loader function
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id)) 

# Ensure the upload folder exists
upload_path = os.path.join(os.getcwd(), 'static', 'uploads')
if not os.path.exists(upload_path):
    os.makedirs(upload_path)

app.config['UPLOAD_FOLDER'] = upload_path


# Student Table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    matric_no = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Added password field
    course_of_study = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    placement = db.Column(db.String(200), nullable=False)
    industry_supervisor = db.Column(db.String(100), nullable=False)
    industry_supervisor_email = db.Column(db.String(100), nullable=False)
    coordinator_name = db.Column(db.String(100), nullable=False)
    coordinator_email = db.Column(db.String(100), nullable=False)
    form08_filename = db.Column(db.String(200), nullable=True)  # Add this field
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=True)  # Add this column
    coordinator_id = db.Column(db.Integer, db.ForeignKey('coordinator.id'), nullable=True)


    supervisor = db.relationship('Supervisor', backref='students', lazy=True)

#supervisor Table
class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    password_changed = db.Column(db.Boolean, default=False)
    assigned_students = db.Column(db.String(255))  # Comma-separated student IDs

# Coordinator Table
class Coordinator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    password_changed = db.Column(db.Boolean, default=False)
    assigned_students = db.Column(db.String(255))  # Comma-separated student IDs

    # Relationship with Student
    students = db.relationship('Student', backref='coordinator', lazy=True)

# Admin Table
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Logbook Table
class Logbook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.Text)
    reviewed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    attachment_path = db.Column(db.String(255), nullable=True)  # Path to uploaded


    student = db.relationship('Student', backref='logbooks', lazy=True)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    entry = db.Column(db.String(500), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    status = db.Column(db.String(20), default="Pending")
    feedback = db.Column(db.Text)
    
    student = db.relationship('Student', backref=db.backref('submissions', lazy=True))

# Feedback Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='feedbacks', lazy=True)
    supervisor = db.relationship('Supervisor', backref='feedbacks', lazy=True)

class WeekFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # ISO week number
    year = db.Column(db.Integer, nullable=False)  # To handle overlapping week numbers in different years
    feedback = db.Column(db.Text, nullable=True)  # Feedback from the supervisor
    reviewed = db.Column(db.Boolean, default=False)


# Create admin in the database
with app.app_context():
    db.create_all()  # Ensures the table exists

    # Check if the admin already exists
    existing_admin = Admin.query.filter_by(email="admin@gmail.com").first()
    if not existing_admin:
        hashed_password = generate_password_hash("Admin123", method="pbkdf2:sha256")  # Use the correct method
        print("Hashed Password:", hashed_password)
        admin = Admin(email="admin@gmail.com", password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")
        

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/students_register', methods=['GET', 'POST'])
def students_register():
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.form['full_name']
        matric_number = request.form['matric_number']
        email = request.form['email']
        course_of_study = request.form['course_of_study']
        level = request.form['level']
        faculty = request.form['faculty']
        department = request.form['department']
        phone_number = request.form['phone_number']
        sex = request.form['sex']
        placement = request.form['placement']
        industry_supervisor = request.form['industry_supervisor']
        industry_supervisor_email = request.form['industry_supervisor_email']
        coordinator_name = request.form['coordinator_name']
        coordinator_email = request.form['coordinator_email']
        password = request.form['password']

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new student object
        student = Student(
            full_name=full_name,
            matric_no=matric_number,
            email=email,
            password=hashed_password,
            course_of_study=course_of_study,
            level=level,
            faculty=faculty,
            department=department,
            phone_number=phone_number,
            sex=sex,
            placement=placement,
            industry_supervisor=industry_supervisor,
            industry_supervisor_email=industry_supervisor_email,
            coordinator_name=coordinator_name,
            coordinator_email=coordinator_email
        )

        # Save to the database
        db.session.add(student)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')

    return render_template('students_register.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"Attempting login for email: {email}")

        # Fetch users from the database
        admin = Admin.query.filter_by(email=email).first()
        coordinator = Coordinator.query.filter_by(email=email).first()
        supervisor = Supervisor.query.filter_by(email=email).first()
        student = Student.query.filter_by(email=email).first()  # Add student query

        # Debugging outputs
        print(f"Admin: {admin}")
        print(f"Coordinator: {coordinator}")
        print(f"Supervisor: {supervisor}")
        print(f"Student: {student}")

        # Admin login
        if admin and check_password_hash(admin.password, password):
            session['role'] = 'admin'
            session['email'] = admin.email
            print("Admin logged in successfully.")
            return redirect(url_for('admin_dashboard'))

        # Coordinator login
        elif coordinator and check_password_hash(coordinator.password, password):
            session['role'] = 'coordinator'
            session['email'] = coordinator.email

            if not coordinator.password_changed:
                print("Coordinator password not changed, redirecting...")
                return redirect(url_for('change_password'))

            print("Coordinator logged in successfully.")
            return redirect(url_for('coordinator_dashboard'))

                # Supervisor login
        elif supervisor and check_password_hash(supervisor.password, password):
            session['role'] = 'supervisor'
            session['email'] = supervisor.email
            session['supervisor_id'] = supervisor.id  # Store supervisor_id in session

            if not supervisor.password_changed:
                print("Supervisor password not changed, redirecting...")
                return redirect(url_for('change_password'))

            print("Supervisor logged in successfully.")
            return redirect(url_for('supervisor_dashboard'))

            # Student login
        elif student and check_password_hash(student.password, password):
            session['role'] = 'student'
            session['email'] = student.email
            session['student_id'] = student.id  # Store the student ID in the session
            print("Student logged in successfully.")
            return redirect(url_for('student_dashboard'))
    return render_template('login.html')


@app.route('/student_dashboard', methods=['GET'])
def student_dashboard():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch the student details
    student = Student.query.get(student_id)
    if not student:
        return redirect(url_for('login'))  # Redirect to login if student not found

    # Fetch submitted logbooks
    logbooks = Logbook.query.filter_by(student_id=student_id).order_by(Logbook.entry_date.desc()).all()

    return render_template(
        'student_dashboard.html',
        student=student,
        logbooks=logbooks
    )

@app.route('/upload_form08', methods=['POST'])
def upload_form08():
    if 'role' in session and session['role'] == 'student':
        student_id = session.get('student_id')
        if not student_id:
            flash('Unauthorized access. Please log in.', 'error')
            return redirect(url_for('login'))

        student = Student.query.get(student_id)
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('login'))

        if 'form08' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('student_dashboard'))

        file = request.files['form08']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('student_dashboard'))

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(f"{student.matric_no}_form08.pdf")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Save the filename in the database
            student.form08_filename = filename
            db.session.commit()

            flash('Form 08 uploaded successfully!', 'success')
        else:
            flash('Only PDF files are allowed!', 'error')

        return redirect(url_for('student_dashboard'))
    else:
        flash("Unauthorized access. Please log in.", 'error')
        return redirect(url_for('login'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)





@app.route('/view_feedback')
def view_feedback():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    # Fetch weekly feedback for the logged-in student
    feedbacks = WeekFeedback.query.filter_by(student_id=student_id).order_by(WeekFeedback.week_number).all()

    return render_template('view_feedback.html', feedbacks=feedbacks)


@app.route('/profile')
def profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    # Fetch the student's details from the database
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        return redirect(url_for('student_dashboard'))  # Redirect if student not found

    return render_template('profile.html', student=student)



@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        # Assume the user's email or ID is stored in session
        user_email = session.get('email')

        # Fetch the user (either Coordinator or Supervisor)
        user = Coordinator.query.filter_by(email=user_email).first() or Supervisor.query.filter_by(email=user_email).first()
        if not user:
            return "User not found", 404

        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "Passwords do not match", 400

        # Hash the new password and update the database
        user.password = generate_password_hash(new_password)
        user.password_changed = True  # Update the flag
        db.session.commit()

        return redirect(url_for('login'))  # Redirect to login after success

    return render_template('change_password.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    total_students = Student.query.count()  # Count total students
    total_coordinators = Coordinator.query.count()  # Count total coordinators

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_coordinators=total_coordinators
    )

@app.route('/manage_students', methods=['GET', 'POST'])
def manage_students():
        if request.method == 'POST':
            # Process adding a student
            full_name = request.form['full_name']
            email = request.form['email']
            matric_no = request.form['matric_no']
            course_of_study = request.form['course_of_study']
            level = request.form['level']
            faculty = request.form['faculty']
            department = request.form['department']
            phone_number = request.form['phone_number']
            sex = request.form['sex']
            placement = request.form['placement']
            industry_supervisor = request.form['industry_supervisor']
            industry_supervisor_email = request.form['industry_supervisor_email']
            coordinator_name = request.form['coordinator_name']
            coordinator_email = request.form['coordinator_email']
            password = request.form['password']

            # Hash the password
            # Hash the password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Add student to the database
            student = Student(
                full_name=full_name,
                email=email,
                matric_no=matric_no,
                course_of_study=course_of_study,
                level=level,
                faculty=faculty,
                department=department,
                phone_number=phone_number,
                sex=sex,
                placement=placement,
                industry_supervisor=industry_supervisor,
                industry_supervisor_email=industry_supervisor_email,
                coordinator_name=coordinator_name,
                coordinator_email=coordinator_email,
                password=hashed_password,
            )
            db.session.add(student)
            db.session.commit()

            flash("Student added successfully!", "success")
            return redirect(url_for('manage_students'))
            # Fetch existing students to display in the table
            
        students = Student.query.all()
        return render_template('manage_students.html', students=students)

@app.route('/manage_coordinators', methods=['GET', 'POST'])
def manage_coordinators():
    if 'role' not in session or session['role'] != 'admin':  # Ensure only admins can access
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Process adding a coordinator or assigning students
        full_name = request.form['full_name']
        email = request.form['email']
        staff_id = request.form['staff_id']
        department = request.form['department']
        password = request.form['password']
        assigned_students = request.form.get('assigned_students', '')

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create a new coordinator
        new_coordinator = Coordinator(
            full_name=full_name,
            email=email,
            staff_id=staff_id,
            department=department,
            password=hashed_password
        )
        db.session.add(new_coordinator)
        db.session.commit()

        # Assign students to the coordinator
        if assigned_students.strip():
            matric_nos = [matric_no.strip() for matric_no in assigned_students.split(',') if matric_no.strip()]
            for matric_no in matric_nos:
                student = Student.query.filter_by(matric_no=matric_no).first()
                if student:
                    student.coordinator_id = new_coordinator.id
            db.session.commit()

        flash("Coordinator added and students assigned successfully!", "success")
        return redirect(url_for('manage_coordinators'))

    # Fetch all coordinators and their assigned students
    coordinators = Coordinator.query.all()
    for coordinator in coordinators:
        coordinator.students = Student.query.filter_by(coordinator_id=coordinator.id).all()

    return render_template('manage_coordinators.html', coordinators=coordinators)

@app.route('/delete_coordinator/<int:coordinator_id>', methods=['POST'])
def delete_coordinator(coordinator_id):
    # Logic to delete the coordinator
    coordinator = Coordinator.query.get(coordinator_id)
    if coordinator:
        db.session.delete(coordinator)
        db.session.commit()
        flash("Coordinator deleted successfully.", "success")
    else:
        flash("Coordinator not found.", "danger")
    return redirect(url_for('manage_coordinators'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for('manage_students'))

@app.route('/coordinator_dashboard')
def coordinator_dashboard():
    if session.get('role') != 'coordinator':
        return redirect(url_for('login'))

    total_students = Student.query.count()  # Count total students
    #total_supervisor = supervisor.query.count()  # Count total coordinators
    # Fetch students assigned to this coordinator
    #assigned_students = Student.query.filter_by(coordinator_id=coordinator_id).all()
    #coordinator_id = session.get('coordinator_id')
    #if not coordinator_id:
       # return redirect(url_for('login'))

    # Fetch students assigned to the supervisor
    #students = Student.query.filter_by(coordinator_id=supervisor_id).all()

    #return render_template(
      #  'coordinator_dashboard.html',
        #students=students
   # )


    return render_template(
        'coordinator_dashboard.html',
        students=total_students,
       # total_supervisors=total_supervisors
    )



@app.route('/manage_supervisors', methods=['GET', 'POST'])
def manage_supervisors():
    if 'role' not in session or session['role'] != 'coordinator':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        staff_id = request.form['staff_id']
        industry = request.form['industry']
        password = request.form['password']
        assigned_students = request.form['assigned_students']

        # Create a new supervisor
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        supervisor = Supervisor(
            full_name=full_name,
            email=email,
            staff_id=staff_id,
            industry=industry,
            password=hashed_password
        )
        db.session.add(supervisor)
        db.session.commit()

        # Assign students to the supervisor using matric_no
        if assigned_students.strip():
            matric_nos = [matric_no.strip() for matric_no in assigned_students.split(',') if matric_no.strip()]
            for matric_no in matric_nos:
                student = Student.query.filter_by(matric_no=matric_no).first()
                if student:
                    student.supervisor_id = supervisor.id
            db.session.commit()

        flash("Supervisor added and students assigned successfully.", "success")
        return redirect(url_for('manage_supervisors'))

    # Fetch existing supervisors and their assigned students
    supervisors = Supervisor.query.all()
    for supervisor in supervisors:
        supervisor.students = Student.query.filter_by(supervisor_id=supervisor.id).all()

    return render_template('manage_supervisors.html', supervisors=supervisors)

@app.route('/edit_supervisor/<int:supervisor_id>', methods=['GET', 'POST'])
def edit_supervisor(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)

    if request.method == 'POST':
        try:
            supervisor.full_name = request.form['name']
            supervisor.email = request.form['email']
            
            # Process assigned_students
            assigned_students = request.form['assigned_students']
            matric_numbers = [matric.strip() for matric in assigned_students.split(',')]

            # Clear existing supervisor assignments for these students
            Student.query.filter(Student.supervisor_id == supervisor.id).update({'supervisor_id': None})

            # Update supervisor_id for the specified students
            for matric in matric_numbers:
                student = Student.query.filter_by(matric_no=matric).first()
                if student:
                    student.supervisor_id = supervisor.id

            db.session.commit()
            flash('Supervisor updated and students assigned successfully!', 'success')
            return redirect(url_for('manage_supervisors'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", 'danger')

    return render_template('edit_supervisor.html', supervisor=supervisor)

@app.route('/edit_coordinator/<int:coordinator_id>', methods=['GET', 'POST'])
def edit_coordinator(coordinator_id):
    coordinator = Coordinator.query.get_or_404(coordinator_id)

    if request.method == 'POST':
        try:
            # Update coordinator details
            coordinator.full_name = request.form['full_name']
            coordinator.email = request.form['email']
            
            # Process assigned students
            assigned_students = request.form.get('assigned_students', '')
            matric_numbers = [matric.strip() for matric in assigned_students.split(',') if matric.strip()]

            # Clear existing coordinator assignments for these students
            Student.query.filter(Student.coordinator_id == coordinator.id).update({'coordinator_id': None})

            # Update coordinator_id for the specified students
            for matric in matric_numbers:
                student = Student.query.filter_by(matric_no=matric).first()
                if student:
                    student.coordinator_id = coordinator.id

            # Update the assigned_students column in Coordinator table
            coordinator.assigned_students = ', '.join(matric_numbers)

            db.session.commit()
            flash('Coordinator updated and students assigned successfully!', 'success')
            return redirect(url_for('manage_coordinators'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", 'danger')

    return render_template('edit_coordinator.html', coordinator=coordinator)


@app.route('/delete_supervisor/<int:supervisor_id>', methods=['POST'])
def delete_supervisor(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    db.session.delete(supervisor)
    db.session.commit()
    flash('Supervisor deleted successfully!', 'success')
    return redirect(url_for('manage_supervisors'))

@app.route('/program_summary')
def program_summary():
    return render_template('program_summary.html')

@app.route('/supervisor_dashboard', methods=['GET'])
def supervisor_dashboard():
    if session.get('role') != 'supervisor':  # Check if the logged-in user is a supervisor
        return redirect(url_for('login'))  # Redirect to login if not

    supervisor_id = session.get('supervisor_id')
    if not supervisor_id:
        return redirect(url_for('login'))

    # Fetch students assigned to the supervisor
    students = Student.query.filter_by(supervisor_id=supervisor_id).all()

    return render_template(
        'supervisor_dashboard.html',
        students=students
    )

# Configure allowed file extensions and upload folder
UPLOAD_FOLDER = 'static/uploads'  # Define a folder to save attachments
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}  # Allowed file types
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_logbook', methods=['POST'])
def submit_logbook():
    student_id = session.get('student_id')
    print(f"Student ID from session: {student_id}")  # Debugging

    if not student_id:
        flash("You must be logged in to submit a logbook.", "error")
        return redirect(url_for('login'))

    # Retrieve the student
    student = db.session.get(Student, student_id)
    print(f"Retrieved Student: {student}")  # Debugging

    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('student_dashboard'))

    # Retrieve week number
    week_no = request.form.get('week_no')
    print(f"Week Number: {week_no}")  # Debugging

    if not week_no:
        flash("Week number is required.", "error")
        return redirect(url_for('student_dashboard'))

    # Handle file upload
    file = request.files.get('attachment')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved at: {filepath}")  # Debugging
    else:
        if file:
            flash("Invalid file type. Allowed types: PNG, JPG, JPEG, PDF.", "error")
        else:
            flash("No file uploaded.", "error")
        return redirect(url_for('student_dashboard'))

    # Process log entries for each day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    entries_saved = 0

    try:
        for day in days:
            date_field = f"{day}_date"
            entry_field = f"{day}_entry"
            entry_date = request.form.get(date_field)
            content = request.form.get(entry_field)
            print(f"Processing {day}: Date - {entry_date}, Content - {content}")  # Debugging

            if entry_date and content:
                # Save logbook entry
                new_logbook = Logbook(
                    student_id=student.id,
                    week_no=week_no,  # Save week number with log entry
                    entry_date=entry_date,
                    content=content,
                    attachment_path=filepath  # Save file path for reference
                )
                db.session.add(new_logbook)
                entries_saved += 1

        db.session.commit()
        flash(f"{entries_saved} logbook entries submitted successfully!", "success")
    except Exception as e:
        print(f"Error while saving log entries: {e}")  # Debugging
        flash("An error occurred while saving the log entries.", "error")

    return redirect(url_for('student_dashboard'))

@app.route('/review_logbook/<int:year>/<int:week>/<int:student_id>', methods=['POST'])
def review_logbook(year, week, student_id):
    if session.get('role') != 'supervisor':  # Authentication check
        return redirect(url_for('login'))

    feedback = request.form.get('feedback')
    if not feedback:
        flash("Feedback is required.", "error")
        return redirect(url_for('student_details', student_id=student_id))

    # Check if feedback for this week already exists
    week_feedback = WeekFeedback.query.filter_by(
        student_id=student_id, week_number=week, year=year
    ).first()
    if not week_feedback:
        week_feedback = WeekFeedback(student_id=student_id, week_number=week, year=year)

    week_feedback.feedback = feedback
    week_feedback.reviewed = True
    db.session.add(week_feedback)
    db.session.commit()

    flash("Feedback submitted successfully.", "success")
    return redirect(url_for('student_details', student_id=student_id))

@app.route('/student_details/<int:student_id>')
def student_details(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('supervisor_dashboard'))

    logbooks = Logbook.query.filter_by(student_id=student.id).order_by(Logbook.entry_date).all()

    # Group logs by week
    weeks = {}
    for log in logbooks:
        week = log.entry_date.isocalendar()[1]  # Get ISO week number
        year = log.entry_date.year  # Get year
        if (year, week) not in weeks:
            feedback = WeekFeedback.query.filter_by(
                student_id=student.id, week_number=week, year=year
            ).first()
            weeks[(year, week)] = {
                'week_ending': log.entry_date,
                'logs': [],
                'feedback': feedback.feedback if feedback else None,
                'reviewed': feedback.reviewed if feedback else False,
            }
        weeks[(year, week)]['logs'].append({
            'date': log.entry_date,
            'content': log.content,
            'attachment': log.attachment_path
        })

    return render_template('student_details.html', student=student, weeks=weeks)



@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))
    

if __name__ == '__main__':
    
    app.run(debug=True)
