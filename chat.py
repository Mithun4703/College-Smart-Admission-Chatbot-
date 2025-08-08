import random
import json
import torch
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
from rapidfuzz import process
from io import BytesIO
from textblob import TextBlob 
from neural_net import NeuralNet
from flask_server.university.nlp_utils import bag_of_words, tokenize
from flask_server import db
from flask_server.university.models import Student, Holidays, Teacher, Course  # Import DB models

# Load intents.json
INTENTS_FILE = "intents.json"
with open(INTENTS_FILE, 'r') as json_data:
    intents = json.load(json_data)

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load trained model
MODEL_FILE = "data.pth"
data = torch.load(MODEL_FILE, map_location=device)

input_size = data['input_size']
output_size = data['output_size']
hidden_size = data['hidden_size']
all_words = data['all_words']
tags = data['tags']
model_state = data['model_state']

model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(model_state)
model.eval()
model.to(device)

# Define a list of known departments
DEPARTMENTS = ["CSBS", "IT", "CSE", "ECE", "EEE", "MECH", "AIDS", "AIML"]

def get_best_match(user_input, intents):
    """
    Finds the closest matching intent using exact matching first, then fuzzy matching.
    Returns the best match if similarity is above 70% for fuzzy match.
    """
    # First, check for an exact match in the patterns
    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            if user_input.lower().strip() == pattern.lower().strip():
                return intent["tag"]  # Exact match found

    # If no exact match, proceed with fuzzy matching
    best_match_score = 0
    best_match_tag = None

    # Iterate through intents for fuzzy matching
    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            score = process.extractOne(user_input, [pattern], score_cutoff=70)  # Fuzzy matching

            if score and score[1] > best_match_score:
                best_match_score = score[1]
                best_match_tag = intent["tag"]

    # Return the best match if fuzzy score is above threshold
    if best_match_score >= 70:
        return best_match_tag
    else:
        return None  # No suitable match found


def fetch_data_from_db(tag, user_input):
    """
    Retrieves data from the database based on the predicted tag.
    Returns plain text responses along with full download links.
    """
    BASE_URL = "http://127.0.0.1:5000"

    # ===========================  
    # STUDENT DETAILS HANDLING  
    # ===========================  
    if tag == "students":
        user_input_lower = user_input.lower().strip()

        if user_input_lower == "all students":
            students = Student.query.all()
            return "\n".join([
                f"{i+1}. *{s.name}* ({s.course.name if s.course else 'No Course'})"
                for i, s in enumerate(students)
            ]) or "No students found.", tag

        # Extract course name from user input
        if "student details of" in user_input_lower:
            user_course_name = user_input_lower.replace("student details of", "").strip()
            course = Course.query.filter(Course.name.ilike(f"%{user_course_name}%")).first()

            if course:
                students = Student.query.filter_by(course_id=course.course_id).all()
                if students:
                    response = f"📌 *Student details of {course.name}:*\n"
                    response += format_students_response(course.name, students)
                    return response, tag
                return f"❌ No students found for *{course.name}*.", tag

            available_courses = ", ".join(c.name for c in Course.query.all())
            return (
                f"⚠ *Course '{user_course_name}' not found.*\n\n"
                f"📚 Available courses:\n{available_courses}\n\n"
                f"➡ Type: *Student details of [course name]*",
                tag
            )

        available_courses = ", ".join(c.name for c in Course.query.all())
        return (
            f"Please specify a course.\n"
            f"📚 Available Courses: {available_courses}\n\n"
            f"➡ Type: *Student details of [course name]*",
            tag
        )
    # ===========================  
    # HOLIDAY LIST HANDLING  
    # ===========================  
    elif tag == "holidays":
        holidays = Holidays.query.all()
        if holidays:
            return "\n".join([
                f"📅 {h.year}: {h.file_name}\n"
                f"🔗 Download: {BASE_URL}/download/holiday/{h.id}"
                for h in holidays
            ]), tag
        return "No holiday records available.", tag

    # ===========================  
    # FACULTY DETAILS HANDLING  
    # ===========================  
    elif tag == "faculty":
        if "all faculty" in user_input.lower():
            teachers = Teacher.query.all()
            return "\n".join([
                f"{i+1}. *{t.first_name} {t.last_name}* ({t.department})"
                for i, t in enumerate(teachers)
            ]) or "No faculty found.", tag

        # Extract department name from user input
        department = next((dept for dept in DEPARTMENTS if dept.lower() in user_input.lower()), None)
        
        if department:
            teachers = Teacher.query.filter_by(department=department).all()
            if teachers:
                response = f"📌 *Faculty details of {department}:*\n"
                response += "\n".join([
                    f"{i+1}. *{t.first_name} {t.last_name}*"
                    for i, t in enumerate(teachers)
                ])
                return response, tag
            return f"❌ No faculty found for *{department}* department.", tag

        return (
            "Which department's faculty list do you want?\n"
            f"👤 Available Departments: {', '.join(DEPARTMENTS)}\n\n"
            "➡ Type: *[Department Name] faculty*",
            tag
        )
    
    # ===========================  
    # COURSE DETAILS HANDLING  
    # ===========================  
    elif tag == "courses":
        courses = Course.query.all()
        return "\n".join([
            f"{i+1}. *{c.name}* ({c.duration})"
            for i, c in enumerate(courses)
        ]) or "No courses available.", tag

    # ===========================  
    # COURSE SYLLABUS HANDLING  
    # ===========================  
    elif tag == "course_syllabus":
        courses = Course.query.filter(Course.syllabus.isnot(None)).all()
        if courses:
            return "\n".join([
                f"📚 *{c.name}* ({c.duration})\n🔗 Download: {BASE_URL}/download/syllabus/{c.course_id}"
                for c in courses
            ]), tag
        return "No syllabus files available.", tag

    return None, tag

def format_students_response(course_name, students):
    """Formats the response for student queries."""
    if students:
        return "\n".join([
           f"{i+1}. *{s.name}* (ID: {s.id}) - CGPA: {s.cgpa if s.cgpa else 'N/A'}"
            for i, s in enumerate(students)
        ])
    else:
        return f"❌ No students found for *{course_name}*."

def get_bot_response(sentence):
    """
    Processes the user input and returns a chatbot response.
    """
    print(f"🟢 Processing input: {sentence}")

    # ✅ Auto-correct spelling mistakes before processing
    corrected_sentence = str(TextBlob(sentence).correct())

    # ✅ Tokenize the corrected sentence
    tokenized_sentence = tokenize(corrected_sentence)

    # ✅ Convert to bag of words
    X = bag_of_words(tokenized_sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    # ✅ Get model prediction
    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    # ✅ Calculate confidence score
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    # ✅ If confidence is high, fetch database response
    if prob.item() > 0.80:
        db_response, tag = fetch_data_from_db(tag, sentence)
        if db_response:
            print(f"🟢 Database Response: {db_response}")
            return db_response, tag

    # ✅ Use fuzzy matching if confidence is low
    tag = get_best_match(sentence, intents)

    if tag:
        for intent in intents["intents"]:
            if tag == intent["tag"]:
                response = random.choice(intent["responses"])
                print(f"🟢 Response: {response} | Intent: {tag}")
                return response, tag

    # ✅ Fallback response if no confident match is found
    print("⚠️ No confident match found. Returning fallback response.")
    return "I'm sorry, but I couldn't understand your query. Please verify your question and try again.", "unknown"

app = Flask(__name__)
CORS(app)  

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    response, tag = get_bot_response(user_input)
    return jsonify({"response": response, "tag": tag})

if __name__ == "__main__":
    print("✅ Chatbot is ready!")
    app.run(debug=True)