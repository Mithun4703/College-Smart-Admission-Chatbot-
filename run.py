from flask import request, jsonify
import requests
from flask_server import app, db
import flask_server.university
from flask_server.university.models import Holidays, Course, Student, Teacher
from chat import get_bot_response
from flask_server.university.nlp_utils import course_matcher

# Ensure database tables exist
with app.app_context():
    db.create_all()

@app.post("/chatbot_api/")
def normal_chat():
    msg = request.get_json().get('message', "").strip().lower()
    
    if not msg:
        return jsonify({'response': "Please provide a message.", 'tag': "error"}), 400

    try:
        response, tag = get_bot_response(msg)
    except Exception as e:
        print("❌ Error in chatbot_response:", e)
        return jsonify({'response': "An error occurred while processing the request.", 'tag': "error"}), 500

    if tag == 'result':
        return jsonify({'response': response, 'tag': tag, 'url': 'result/'})

    elif tag == 'courses':
        try:
            course = course_matcher(msg)
            print(f"🔍 Debug: Extracted Course Name -> {course}")
            if course:
                course_details = Course.query.filter_by(name=course).first()
                if course_details:
                    response = f"{course_details.name} takes {course_details.duration}"
                    link = f"http://127.0.0.1:5000/courses/syllabus/{course_details.id}/"
                    return jsonify({
                        'response': response, 'tag': tag,
                        "data": {
                            "filename": f"{course_details.name} syllabus",
                            "link": link
                        }
                    })
                else:
                    response = "Sorry, I couldn't find that course."
            else:
                courses = Course.query.all()
                response = "Available courses:\n" + "\n".join([course.name for course in courses])
        except Exception as e:
            print("❌ Error fetching course details:", e)
            response = "An error occurred while retrieving course details."

    elif tag == "holidays":
        try:
            holiday = Holidays.query.order_by(Holidays.year.desc()).first()
            if holiday:
                response = f"Holidays for the year {holiday.year} are available below."
                download_button = f'<button onclick="window.location.href=\'http://127.0.0.1:5000/holidays/download/{holiday.id}/\'" style="padding:8px 15px; background:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer;">📥 Download</button>'
                
                return jsonify({'response': response + "<br>" + download_button, 'tag': tag})

            else:
                response = "No holiday details found."
        except Exception as e:
            print("❌ Error fetching holiday details:", e)
            response = "An error occurred while retrieving holiday details."
            return jsonify({'response': response, 'tag': tag}), 500

    elif tag == 'faculty':
        department = None
        departments = ["csbs", "cse", "ece", "mech", "aids", "eee", "it", "aiml"]

        for dept in departments:
            if dept in msg:
                department = dept.upper()
                break

        if department:
            try:
                url = f'http://127.0.0.1:5000/teachers/api/{department.lower()}/'
                print(f"🔍 Debug: Fetching faculty data from {url}")

                data = requests.get(url=url)

                if data.status_code == 200:
                    teachers = data.json()

                    if isinstance(teachers, list) and teachers:
                        faculty_names = [f"{t['first_name']} {t['last_name']}".strip() for t in teachers]
                        response = f"👨‍🏫 Faculty in {department} Department:\n" + "\n".join(faculty_names)
                    else:
                        response = f"❌ No faculty found in {department}."
                else:
                    response = f"⚠ Unable to fetch faculty details for {department} (HTTP {data.status_code})."

            except requests.RequestException as e:
                print(f"❌ Error fetching faculty data: {e}")
                response = f"An error occurred while fetching faculty details for {department}. Please try again later."
        else:
            response = (
                "❓ Please specify a valid department:\n"
                "📚 Available: CSBS, CSE, ECE, MECH, AI&DS, AI&ML, EEE, IT...\n\n"
                "💡 Example: *csbs faculty*"
            )

    elif tag == 'students':
        try:
            if "student details of" in msg:
                user_course_name = msg.replace("student details of", "").strip().lower()

                # Fetch all courses and normalize names
                courses = {c.name.lower().strip(): c for c in Course.query.all()} 

                # 🔍 Debugging
                print(f"🔍 Debug: Available Courses -> {[c.name for c in courses.values()]}")
                print(f"🔍 Debug: User Entered Course -> '{user_course_name}'")

                # ✅ Try exact or partial match
                course = courses.get(user_course_name) or next((courses[c] for c in courses if user_course_name in c), None)

                if course:
                    url = f'http://127.0.0.1:5000/students/api/{course.name.lower()}/'
                    data = requests.get(url=url)

                    if data.status_code == 200:
                        students = data.json()

                        if isinstance(students, list) and students:
                            response = "<div style='background: #dff0d8; padding: 10px; border-radius: 5px;'>"
                            response += f"<b>🎓 Students in {course.name}:</b><br><br>"

                            for i, s in enumerate(students, start=1):
                                response += f"{i}. <b>{s['name']}</b> (CGPA: {s['cgpa'] if s['cgpa'] else 'N/A'})<br>"

                            response += "</div>"
                        else:
                            response = f"❌ No students found for <b>{course.name}</b>."
                    else:
                        response = f"⚠ Unable to fetch student details for {course.name}."

                else:
                    available_courses = ", ".join(c.name for c in courses.values())
                    response = (
                        f"⚠ *Course '{user_course_name}' not found.*<br><br>"
                        f"📚 Available courses:<br>{available_courses}<br><br>"
                        f"➡ Type: <b>Student details of [course name]</b>"
                    )

        except Exception as e:
            print(f"❌ Error fetching student data: {e}")
            response = "An error occurred while fetching student details. Please try again later."

        return jsonify({'response': response, 'tag': tag})

@app.post("/chatbot_api/result/")
def fetch_result():
    msg = request.get_json().get('message', "").strip()

    if not msg:
        return jsonify({'response': "Please provide a student ID.", 'url': ""}), 400

    try:
        studentID = msg.replace(' ', '')
        if not studentID.isdigit():
            return jsonify({'response': "Please use the correct format: \n434121010021", 'url': "result/"})

        student = Student.query.get(studentID)

        if student:
            response = f"Result of {studentID} is {student.cgpa}"
            url = ""
        else:
            response = "Student not found"
            url = ""

    except Exception as e:
        print("❌ Error fetching student result:", e)
        response = "An error occurred while retrieving the result."
        url = ""

    return jsonify({'response': response, 'url': url})
