from flask import Flask, render_template, request, redirect, url_for, flash
from controller.config import config
from controller.database import db
from flask import session
from controller.models import *
from google import genai # The new 2026 import
from google.genai import types
import json
import random
import re


app = Flask(__name__)

app.config.from_object(config)


# 1. Initialize the Client (replaces genai.configure)
client = genai.Client(api_key='AIzaSyA0rodqYcYOr_3gATn5H4-l1GmMTesGbeM')

# --- SMART MODEL SELECTION ---
try:
    # In the new SDK, the attribute is 'supported_methods' 
    # and the action is 'generate_content'
    generate_models = [
        m for m in client.models.list() 
        if 'generate_content' in (m.supported_methods or [])
    ]
    
    # Prioritize newest models (2.5 -> 2.0 -> Pro -> Flash)
    pref_order = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    model_name = "gemini-2.5-flash" # Default fallback
    
    for pref in pref_order:
        if any(pref in m.name for m in generate_models):
            model_name = pref
            break
            
    print(f"✅ AI Setup Success: Using {model_name}")
except Exception as e:
    # If listing fails, we hardcode the most reliable 2026 stable model
    model_name = "gemini-2.5-flash"
    print(f"⚠️ AI Setup Warning: Could not list models ({e}). Falling back to {model_name}")

# --- UPDATED CHAT FUNCTION ---
# Note: Use client.models.generate_content (not GenerativeModel)
def get_ai_response(user_input):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_input
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
    

db.init_app(app)


with app.app_context():
    db.create_all()

    # Ensure roles exist
    if not Role.query.first():
        roles = [
            Role(id=1, name="Admin"),
            Role(id=2, name="Teacher"),
            Role(id=3, name="Student")
        ]
        db.session.add_all(roles)
        db.session.commit()

    # Create sample users
    if not User.query.first():
        admin_user = User(username="admin", email="admin@example.com", password="admin123")
        
        db.session.add(admin_user)
        db.session.commit()

        # Assign roles to users
        admin_role = UserRole(user_id=admin_user.id, role_id=1)   # Admin
        db.session.add(admin_role)
        db.session.commit()

# --- HELPER FUNCTION ---
def get_gemini_fact():
    topics = ["science", "history", "space", "technology", "nature", "coding"]
    selected_topic = random.choice(topics)
    
    try:
        # We ask for a random topic each time to ensure variety
        response = client.generate_content(f"Tell me one short, interesting fact about {selected_topic}.")
        return response.text.strip()
    except Exception as e:
        print(f"Fact Error: {e}")
        return "Did you know? The Python programming language is named after Monty Python, not the snake."
#-----------------------routes-----------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    roles = Role.query.filter(Role.id != 1).all()
    if request.method == "POST":
        email = request.form.get("email")
        
        # CHECK IF EMAIL EXISTS BEFORE SAVING
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email is already registered. Please login.")
            return redirect(url_for('login'))

        # If it doesn't exist, proceed with saving
        new_user = User(
            username=request.form.get("username"), 
            email=email, 
            password=request.form.get("password")
        )
        db.session.add(new_user)
        db.session.commit()
        
        db.session.add(UserRole(user_id=new_user.id, role_id=request.form.get("role_id")))
        db.session.commit()
        
        flash("Registration successful!")
        return redirect(url_for('login'))
    return render_template("register.html", roles=roles)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and user.password == request.form.get("password"):
            session['user_id'] = user.id
            session['username'] = user.username
            role_entry = UserRole.query.filter_by(user_id=user.id).first()
            session['role_id'] = role_entry.role_id
            
            if role_entry.role_id == 1: return redirect(url_for('admin_dashboard'))
            if role_entry.role_id == 2: return redirect(url_for('staff_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash("Invalid Credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- 6. ADMIN DASHBOARD ---

@app.route("/admin/dashboard")
def admin_dashboard():
    # Security check: Ensure user is logged in and is Admin
    if 'user_id' not in session or session.get('role_id') != 1:
        return redirect(url_for('login'))

    # 1. Fetch Stats
    total_students = UserRole.query.filter_by(role_id=3).count()
    total_teachers = UserRole.query.filter_by(role_id=2).count()
    total_quizzes = Quiz.query.count()

    # 2. Fetch All Users with their Roles (Explicit Join)
    # This solves the InvalidRequestError by defining the exact path
    all_users = db.session.query(User, Role.name).\
        select_from(User).\
        join(UserRole, User.id == UserRole.user_id).\
        join(Role, UserRole.role_id == Role.id).\
        all()

    return render_template("admin_dashboard.html", 
                           username=session.get('username'),
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_quizzes=total_quizzes,
                           all_users=all_users)

# --- 7. STAFF ROUTES (CREATION & PERFORMANCE) ---

@app.route("/staff/dashboard")
def staff_dashboard():
    if session.get('role_id') != 2: 
        return redirect(url_for('login'))
    
    # Use db.session.get to avoid the LegacyWarning
    user = db.session.get(User, session['user_id'])
    
    # We fetch quizzes and 'join' the results so we can see student scores
    quizzes = Quiz.query.filter_by(creator_id=user.id).all()
    
    return render_template("staff_dashboard.html", user=user, quizzes=quizzes)

@app.route("/staff/profile/update", methods=["POST"])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    user.username = request.form.get("username")
    user.email = request.form.get("email")
    
    try:
        db.session.commit()
        flash("Profile updated successfully!")
    except Exception as e:
        db.session.rollback()
        flash("Error updating profile: Username or Email might already be taken.")
        
    return redirect("/staff/generate_quiz", methods=["POST"])


@app.route("/staff/generate_quiz", methods=["POST"])
def generate_quiz():
    topic = request.form.get("topic")
    num = request.form.get("num_questions", 5)
    
    prompt = (f"Generate a {num} question quiz about {topic} in valid JSON. "
              "Format: {'title': '...', 'questions': [{'text': '...', 'options': ['A','B','C','D'], 'correct_answer': '...'}]}")
    
    try:
        # NEW SYNTAX: Use client.models instead of model.generate
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt
        )

        import json, re
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not match:
            flash("AI returned invalid format. Please try again.")
            return redirect(url_for('staff_dashboard'))
            
        data = json.loads(match.group(0))
        
        # Database logic
        new_quiz = Quiz(title=data.get('title', topic), creator_id=session.get('user_id'))
        db.session.add(new_quiz)
        db.session.commit()

        for q in data['questions']:
            question_obj = Question(
                quiz_id=new_quiz.id,
                text=q['text'],
                options=json.dumps(q['options']), 
                correct_answer=q['correct_answer']
            )
            db.session.add(question_obj)
        db.session.commit()
        flash("Quiz generated successfully!")

    except Exception as e:  # <--- FIXES UnboundLocalError
        db.session.rollback()
        error_str = str(e)   # Now 'e' is defined, so this won't crash
        
        if "429" in error_str:
            flash("AI Quota Exceeded. Please wait 1 minute.")
        else:
            flash(f"AI Error: {error_str}")

    return redirect(url_for('staff_dashboard'))

@app.route("/staff/create_quiz")
def create_quiz_page():
    if session.get('role_id') != 2: 
        return redirect(url_for('login'))
    return render_template("create_quiz.html")

@app.route("/staff/quiz_results/<int:quiz_id>")
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    results = StudentResult.query.filter_by(quiz_id=quiz_id).all()
    return render_template("quiz_results.html", quiz=quiz, results=results)

# --- 8. STUDENT ROUTES (TAKING & HISTORY) ---

@app.route("/student/dashboard")
def student_dashboard():
    if session.get('role_id') != 3: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    history = StudentResult.query.filter_by(user_id=user.id).all()
    available = Quiz.query.all()
    return render_template("student_dashboard.html", user=user, daily_fact=get_gemini_fact(), history=history, available_quizzes=available)

@app.route("/student/profile_update", methods=["POST"])
def student_profile_update():
    user = User.query.get(session['user_id'])
    user.username = request.form.get("username")
    user.email = request.form.get("email")
    if request.form.get("password"): user.password = request.form.get("password")
    db.session.commit()
    flash("Profile Updated!")
    return redirect(url_for('student_dashboard'))

@app.route("/student/take_quiz/<int:quiz_id>")
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("take_quiz.html", quiz=quiz, questions=questions)

@app.route("/student/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    score = 0
    for q in questions:
        ans = request.form.get(f"question_{q.id}")
        is_correct = (ans == q.correct_answer)
        if is_correct: score += 1
        db.session.add(StudentAnswer(user_id=session['user_id'], quiz_id=quiz_id, question_id=q.id, selected_option=ans, is_correct=is_correct))
    
    percent = int((score / len(questions)) * 100) if questions else 0
    db.session.add(StudentResult(user_id=session['user_id'], quiz_id=quiz_id, score=percent, total_questions=len(questions)))
    db.session.commit()
    flash(f"Quiz Complete! You scored {percent}%")
    return redirect(url_for('student_dashboard'))

# --- 9. RUN APP ---
if __name__ == "__main__":
    app.run(debug=True)