from flask_server import db

class Teacher(db.Model):
    id = db.Column('faculty_id', db.Integer, primary_key=True)
    first_name = db.Column(db.String(123), nullable=False)
    last_name = db.Column(db.String(123), nullable=False)
    department = db.Column(db.String(123), nullable=False)

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

class Holidays(db.Model):
    id = db.Column('holiday_id', db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(123), nullable=False)
    data = db.Column(db.LargeBinary)

    def __repr__(self):
        return f"Holidays ID: {self.id} for Year: {self.year}"

class Course(db.Model):  # ✅ Defined before Student to avoid reference issues
    course_id = db.Column(db.Integer, primary_key=True)  # ✅ Ensures correct PK
    name = db.Column(db.String(123), nullable=False, unique=True)  # ✅ Ensures unique course names
    syllabus = db.Column(db.LargeBinary)
    duration = db.Column(db.String(123), nullable=False)

    # ✅ Relationship to Student (Fixing backref issues)
    students = db.relationship('Student', back_populates="course", lazy=True)

    def __repr__(self):
        return f"{self.name} - {self.duration}"

class Student(db.Model):
    __tablename__ = 'student'  # ✅ Ensure correct table naming

    id = db.Column('student_id', db.String(20), primary_key=True, nullable=False)  # ✅ Student ID as String
    name = db.Column(db.String(123), nullable=False)
    cgpa = db.Column(db.Float, default=0.0, nullable=False)  # ✅ Ensure CGPA is not NULL
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)

    course = db.relationship('Course', back_populates="students", lazy=True)  # ✅ Relationship Fix

    
class AdmissionForm(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(123), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(123), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    permanent_address = db.Column(db.Text, nullable=False)
    current_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    qualification = db.Column(db.String(123), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)  # ✅ Changed to Float
    school_college = db.Column(db.String(123), nullable=False)
    board_university = db.Column(db.String(123), nullable=False)
    
    # ✅ Use Foreign Key for Course instead of String
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    mode = db.Column(db.String(50), nullable=False)

    marksheet = db.Column(db.String(255), nullable=True)  # ✅ File path
    id_proof = db.Column(db.String(255), nullable=True)  # ✅ File path

    father_name = db.Column(db.String(123), nullable=False)
    mother_name = db.Column(db.String(123), nullable=True)
    guardian_contact = db.Column(db.String(15), nullable=True)

    submission_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    # ✅ Relationship with Course table
    course = db.relationship('Course', backref='admission_forms')

    def __repr__(self):
        return f"AdmissionForm({self.full_name}, {self.email}, {self.course.name if self.course else 'No Course'})"
