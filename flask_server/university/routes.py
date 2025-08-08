import os
import traceback
from flask_server import db, app
from datetime import datetime
from flask import send_from_directory
from flask import render_template, request, jsonify, redirect, url_for, send_file, abort
from chat import get_bot_response
from flask_server.university.models import Teacher, Holidays, Student, Course,AdmissionForm
from io import BytesIO
from werkzeug.utils import secure_filename

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB Limit

def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template('home.html')

# =============================
# CHATBOT ROUTE
# =============================
@app.route("/chat", methods=['POST'])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message received"}), 400

    user_message = data["message"]
    response, tag = get_bot_response(user_message)
    return jsonify({"response": response, "intent": tag})

# =============================
# HOLIDAYS
# =============================
@app.route("/holidays/", methods=['POST', 'GET'])
def holidays():
    if request.method == 'POST':
        year = request.form.get('year')
        file = request.files.get('file')

        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file! Only JPG, PNG, or PDF files are allowed."}), 400

        file_data = file.read()
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({"error": "File size exceeds the 20MB limit!"}), 400

        filename = secure_filename(file.filename)
        new_holiday = Holidays(year=year, file_name=filename, data=file_data)
        db.session.add(new_holiday)
        db.session.commit()

        return redirect(url_for('holidays'))

    holidays = Holidays.query.all()
    return render_template('holidays.html', holidays=holidays)

@app.route("/holidays/download/<int:id>/")
def holidays_download(id):
    holiday = Holidays.query.get(id)
    if not holiday:
        return jsonify({"error": "Holiday file not found"}), 404

    return send_file(BytesIO(holiday.data), download_name=holiday.file_name, as_attachment=True)

@app.route("/holidays/delete/<int:id>/", methods=['POST'])
def delete_holiday(id):
    holiday = Holidays.query.get(id)
    if holiday:
        db.session.delete(holiday)
        db.session.commit()
    return redirect(url_for('holidays'))


from flask import render_template, request, jsonify, redirect, url_for
from flask_server import app, db
from .models import Teacher  # ✅ Make sure the model is correctly imported

# =============================
# TEACHERS
# =============================

@app.route("/teachers/", methods=['POST', 'GET'])
def teachers():
    if request.method == 'POST':
        print("🔥 Form Data Received:", request.form)  # ✅ Debugging

        first_name = request.form.get('first_name', "").strip()
        last_name = request.form.get('last_name', "").strip()
        department = request.form.get('department', "").strip()

        if not first_name or not last_name or not department:
            print("❌ ERROR: Missing required fields!")
            return "Missing required fields!", 400  # ✅ Fix: Prevents empty data error

        # ✅ Save new teacher
        new_teacher = Teacher(first_name=first_name, last_name=last_name, department=department)
        db.session.add(new_teacher)
        db.session.commit()

        print("✅ SUCCESS: Teacher added successfully!")
        return redirect(url_for('teachers'))

    # ✅ Filtering Logic
    selected_department = request.args.get('department', "").strip()

    if selected_department:
        print(f"🔥 Debug: Filtering teachers by department: {selected_department}")  # ✅ Debugging
        teachers = Teacher.query.filter_by(department=selected_department).all()
    else:
        teachers = Teacher.query.all()

    # ✅ Get unique department names for filter dropdown
    departments = db.session.query(Teacher.department).distinct().all()
    departments = [d[0] for d in departments]  # Convert list of tuples to list of strings

    return render_template('teachers.html', teachers=teachers, departments=departments, selected_department=selected_department)


# ✅ DELETE TEACHER
@app.route("/teachers/delete/<int:id>/", methods=['POST'])
def teachers_delete(id):
    teacher = Teacher.query.get(id)
    if teacher:
        db.session.delete(teacher)
        db.session.commit()
        print(f"✅ SUCCESS: Teacher {teacher.first_name} {teacher.last_name} deleted successfully!")

    return redirect(url_for('teachers'))


# ✅ UPDATE TEACHER
@app.route("/teachers/update/<int:id>/", methods=['GET', 'POST'])
def update_teacher(id):
    teacher = Teacher.query.get(id)
    
    if not teacher:
        return "Teacher not found!", 404  # ✅ Fix: Prevent updating a non-existing teacher

    if request.method == 'POST':
        first_name = request.form.get('first_name', "").strip()
        last_name = request.form.get('last_name', "").strip()  # ✅ Corrected field name
        department = request.form.get('department', "").strip()

        print(f"🔥 Debug: Received Data - First Name: {first_name}, Last Name: {last_name}, Department: {department}")  # ✅ Debugging

        # ✅ Fix: Prevent empty fields
        if not first_name or not last_name or not department:
            print("❌ ERROR: Missing required fields!")
            return "Missing required fields!", 400

        # ✅ Update the teacher record
        teacher.first_name = first_name
        teacher.last_name = last_name  # ✅ Fix: Correct field name used
        teacher.department = department

        db.session.commit()
        print(f"✅ SUCCESS: Teacher {teacher.id} updated successfully!")
        return redirect(url_for('teachers'))

    return render_template('update_teacher.html', teacher=teacher)



# =============================
# STUDENTS
# =============================

@app.route("/students/", methods=['POST', 'GET'])
def students():
    if request.method == 'POST':
        print("🔥 Form Data Received:", request.form)  # ✅ Debugging Step

        student_id = request.form.get('id', "").strip()  # ✅ Get Student ID
        name = request.form.get('name', "").strip()
        course_id = request.form.get('course_id', "").strip()

        if not student_id or not name or not course_id:
            print("❌ ERROR: Missing required fields!")
            return "Missing required fields!", 400  # ✅ Prevent empty values

        # 🔹 Validate course ID
        try:
            course_id = int(course_id)  # ✅ Ensure course_id is an integer
        except ValueError:
            print("❌ ERROR: Invalid course ID format!")
            return "Invalid course ID!", 400

        course = Course.query.get(course_id)
        if not course:
            print("❌ ERROR: Course ID does not exist in the database!")
            return "Invalid course selected!", 400

        # 🔹 Save student with correct student_id, course_id, and CGPA
        new_student = Student(id=student_id, name=name, course_id=course_id, cgpa=0.0)  # ✅ Fix: Include Student ID
        db.session.add(new_student)
        db.session.commit()

        print("✅ SUCCESS: Student added successfully!")
        return redirect(url_for('students'))

    # ✅ FIXED Filtering Logic
    course_name = request.args.get('course_name', "").strip()

    if course_name:
        print(f"🔥 Debug: Filtering students by course: {course_name}")  # ✅ Debugging

        # ✅ Ensure case-insensitive filtering
        course = Course.query.filter(db.func.lower(Course.name) == course_name.lower()).first()
        if course:
            students = Student.query.filter_by(course_id=course.course_id).all()
            print(f"✅ Found {len(students)} students in {course_name}")
        else:
            students = []  # ✅ No students if course is invalid
            print("❌ No students found for this course!")
    else:
        students = Student.query.all()  # ✅ Show all students if no filter is applied

    courses = Course.query.all()

    # ✅ Debugging - Check if course data is sent to students.html
    print("🔥 DEBUG: Courses sent to students.html:", [(c.course_id, c.name) for c in courses])

    return render_template('students.html', students=students, courses=courses, selected_course=course_name)


# ✅ Route to Update Student Details (CGPA & Course)
@app.route("/students/update/<string:id>/", methods=['POST', 'GET'])
def students_update(id):
    student = Student.query.get(id)
    if not student:
        return "Student not found!", 404

    if request.method == 'POST':
        student.name = request.form.get('name', "").strip()

        # ✅ Validate CGPA input
        cgpa_value = request.form.get('cgpa', "").strip()
        try:
            student.cgpa = float(cgpa_value) if cgpa_value else 0.0
        except ValueError:
            print("❌ ERROR: Invalid CGPA value!")
            return "Invalid CGPA value! Please enter a valid number.", 400

        # ✅ Validate Course ID
        course_id = request.form.get('course_id', "").strip()
        if not course_id:
            return "Course ID is required!", 400

        try:
            course_id = int(course_id)
        except ValueError:
            return "Invalid course ID!", 400

        course = Course.query.get(course_id)
        if not course:
            return "Invalid course!", 400  # ✅ Fix: Ensure the course exists

        student.course_id = course_id  # ✅ Fix: Correctly update student.course_id
        db.session.commit()

        print("✅ SUCCESS: Student updated successfully!")
        return redirect(url_for('students'))

    courses = Course.query.all()
    return render_template('student_update.html', student=student, courses=courses)


# ✅ Route to Delete a Student
@app.route("/students/delete/<string:id>/", methods=['POST'])
def students_delete(id):
    student = Student.query.get(id)
    if not student:
        print("❌ ERROR: Student not found!")
        return "Student not found!", 404  # ✅ Prevent deleting non-existent student

    db.session.delete(student)
    db.session.commit()
    print("✅ SUCCESS: Student deleted successfully!")
    return redirect(url_for('students'))


# ✅ Route to Get Students by Course Name (Chatbot API)
@app.route("/students/api/<string:course_name>/", methods=["GET"])
def get_students_by_course(course_name):
    """Fetch students by course name (case-insensitive) for chatbot API."""
    
    course_name = course_name.strip().lower()  # ✅ Strip spaces & lowercase
    course = Course.query.filter(db.func.lower(Course.name) == course_name).first()

    if not course:
        return jsonify({"error": "Course not found"}), 404  # ✅ Return immediately if no course

    students = Student.query.filter_by(course_id=course.course_id).all()  # ✅ Fix: Use `course.course_id` instead of `course.id`

    if not students:
        return jsonify({"message": "No students found for this course"}), 404  # ✅ Better error message

    student_list = [{"id": s.id, "name": s.name, "cgpa": s.cgpa} for s in students]

    return jsonify(student_list)


if __name__ == "__main__":
    app.run(debug=True)

# =============================
# COURSE MANAGEMENT
# =============================

# ✅ Route to View and Add Courses
@app.route("/courses/", methods=['POST', 'GET'])
def courses():
    if request.method == 'POST':
        name = request.form['name']
        duration = request.form['duration']

        # ✅ Prevent duplicate courses
        existing_course = Course.query.filter_by(name=name).first()
        if not existing_course:
            new_course = Course(name=name, duration=duration)
            db.session.add(new_course)
            db.session.commit()

        return redirect(url_for('courses'))

    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

# ✅ Route to Delete a Course
@app.route("/courses/delete/<int:course_id>/", methods=['POST'])
def courses_delete(course_id):
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
    return redirect(url_for('courses'))

# ✅ Route to Get All Available Course Names (JSON API)
@app.route("/courses/names", methods=["GET"])
def get_course_names():
    courses = Course.query.all()
    
    if not courses:
        return jsonify({"message": "No courses found"}), 404

    course_list = [course.name for course in courses]
    
    return jsonify({"courses": course_list})

# =============================
# SYLLABUS MANAGEMENT
# =============================

# ✅ Route to Upload Syllabus for a Course
@app.route("/courses/syllabus/upload/<int:course_id>", methods=["POST"])
def upload_syllabus(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if "syllabus" not in request.files:
        return jsonify({"error": "No syllabus file provided"}), 400

    file = request.files["syllabus"]
    course.syllabus = file.read()  # Store syllabus as binary data
    db.session.commit()

    return jsonify({"message": f"Syllabus uploaded for {course.name}"}), 200

# ✅ Route to Update Course Name and Syllabus
@app.route("/courses/update/<int:course_id>", methods=["GET", "POST"])
def update_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if request.method == "POST":
        name = request.form.get("name")
        syllabus = request.files.get("syllabus")

        if name:
            # ✅ Prevent duplicate course names (excluding the same course)
            existing_course = Course.query.filter_by(name=name).first()
            if existing_course and existing_course.course_id != course_id:
                return jsonify({"error": "Course name already exists"}), 400
            course.name = name

        if syllabus:
            course.syllabus = syllabus.read()

        db.session.commit()
        return redirect(url_for('courses'))  # ✅ Redirect after update

    # ✅ Render the update form with course details
    return render_template("update_course.html", course=course)


# ✅ Route to Download Course Syllabus
@app.route("/download/syllabus/<int:course_id>")
def download_syllabus(course_id):
    course = Course.query.get(course_id)
    if not course or not course.syllabus:
        return jsonify({"error": "Syllabus not available for this course."}), 404

    return send_file(
        BytesIO(course.syllabus),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=f"{course.name}_syllabus.pdf"
    )

# ✅ Route to Retrieve Courses with Available Syllabus
@app.route("/courses/syllabus/list", methods=["GET"])
def list_courses_with_syllabus():
    BASE_URL = "http://127.0.0.1:5000"
    
    courses = Course.query.filter(Course.syllabus.isnot(None)).all()
    if not courses:
        return jsonify({"message": "No syllabus files available."}), 404

    syllabus_list = [
        {
            "course_name": course.name,
            "duration": course.duration,
            "syllabus_link": f"{BASE_URL}/download/syllabus/{course.course_id}"
        }
        for course in courses
    ]
    
    return jsonify({"courses": syllabus_list})

if __name__ == "__main__":
    print("✅ Course & Syllabus management routes are ready!")
    app.run(debug=True)
    
# =============================
# ADMISSION FORM ROUTES
# =============================

# ✅ Ensure Absolute Path for Uploads
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'admission_docs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Configure Upload Folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/admission-form/')
def admission_form():
    """Render the Admission Form Page with available courses."""
    courses = Course.query.all()
    return render_template('admission_form.html', courses=courses)

@app.route('/submit-admission', methods=['POST'])
def submit_admission():
    """Handles admission form submission."""
    full_name = request.form['full_name']

    # ✅ Convert DOB from String to Python Date Object
    dob_str = request.form['dob']
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid Date Format! Use YYYY-MM-DD.", 400

    gender = request.form['gender']
    email = request.form['email']
    phone = request.form['phone']
    permanent_address = request.form['permanent_address']
    current_address = request.form['current_address']
    city = request.form['city']
    state = request.form['state']
    pincode = request.form['pincode']
    qualification = request.form['qualification']
    school_college = request.form['school_college']
    board_university = request.form['board_university']
    mode = request.form['mode']
    father_name = request.form['father_name']
    mother_name = request.form.get('mother_name', 'N/A')
    guardian_contact = request.form['guardian_contact']

    # ✅ Validate and Convert CGPA
    try:
        cgpa = float(request.form.get('cgpa', "0").strip())
    except ValueError:
        return "Invalid CGPA value!", 400

    # ✅ Validate Course Selection
    course_id = request.form.get('course_id')
    if not course_id or not course_id.isdigit():
        return "Error: Course selection is required!", 400

    course_id = int(course_id)
    course = Course.query.get(course_id)
    if not course:
        return "Error: Selected Course Not Found!", 400

    # ✅ Handle File Uploads
    marksheet_filename = None
    id_proof_filename = None

    if 'marksheet' in request.files:
        marksheet_file = request.files['marksheet']
        if marksheet_file.filename:  # Ensure file is uploaded
            marksheet_filename = secure_filename(marksheet_file.filename)
            marksheet_file.save(os.path.join(app.config['UPLOAD_FOLDER'], marksheet_filename))

    if 'id_proof' in request.files:
        id_proof_file = request.files['id_proof']
        if id_proof_file.filename:
            id_proof_filename = secure_filename(id_proof_file.filename)
            id_proof_file.save(os.path.join(app.config['UPLOAD_FOLDER'], id_proof_filename))

    # ✅ Save Admission Form
    new_admission = AdmissionForm(
        full_name=full_name, dob=dob, gender=gender, email=email, phone=phone,
        permanent_address=permanent_address, current_address=current_address,
        city=city, state=state, pincode=pincode, qualification=qualification, cgpa=cgpa,
        school_college=school_college, board_university=board_university,
        course_id=course_id, mode=mode, father_name=father_name, mother_name=mother_name,
        guardian_contact=guardian_contact, marksheet=marksheet_filename, id_proof=id_proof_filename
    )

    try:
        db.session.add(new_admission)
        db.session.commit()
    except Exception as e:
        print("❌ Database Error:", e)
        print(traceback.format_exc())
        return "Internal Server Error. Check logs.", 500

    print(f"✅ Admission Form Submitted: {full_name}, Course ID: {course_id}")
    return render_template('success.html', name=full_name)

@app.route('/admissions/')
def view_admissions():
    """View all submitted admission forms (Admin Only)."""
    admissions = AdmissionForm.query.all()
    for admission in admissions:
        admission.course_name = "N/A" if not admission.course_id else Course.query.filter_by(course_id=admission.course_id).first().name
    return render_template('admissions.html', admissions=admissions)

@app.route('/admissions/delete/<int:id>/', methods=['POST'])
def delete_admission(id):
    """Delete an admission record."""
    admission = AdmissionForm.query.get(id)
    if admission:
        db.session.delete(admission)
        db.session.commit()
    return redirect(url_for('view_admissions'))

@app.route('/admin/admission-detail/<int:id>/')
def view_admission_detail(id):
    """View full details of a specific admission form."""
    record = AdmissionForm.query.get(id)
    if not record:
        return "Admission record not found!", 404

    course_name = "Not Assigned"
    if record.course_id:
        course = Course.query.get(record.course_id)
        if course:
            course_name = course.name

    return render_template('admission_detail.html', record=record, course_name=course_name)

# ✅ Corrected Route to Serve Uploaded Files
@app.route('/download/<filename>')
def download_file(filename):
    """Serve uploaded admission documents for download."""
    
    # ✅ Ensure Safe File Access
    safe_filename = secure_filename(filename)  # Prevent directory traversal attacks
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

    # ✅ Debugging Print Statements
    print(f"🔎 Checking for file: {file_path}")
    
    # ✅ Check if File Exists
    if not os.path.isfile(file_path):  # More precise check
        print("❌ File Not Found!")
        abort(404)

    # ✅ Serve File for Download
    return send_file(file_path, as_attachment=True)

# =============================
# ✅ END OF ADMISSION ROUTES
# =============================

if __name__ == "__main__":
    app.run(debug=True)

# =============================
# ATTACHMENT ROUTE
# =============================
@app.route('/download/holiday/<int:holiday_id>/')
def download_holiday(holiday_id):
    holiday = Holidays.query.get(holiday_id)
    if not holiday:
        return "Holiday file not found.", 404

    return send_file(
        BytesIO(holiday.data), 
        mimetype="application/octet-stream", 
        as_attachment=True, 
        download_name=holiday.file_name
    )

if __name__ == "__main__":
    app.run(debug=True)
