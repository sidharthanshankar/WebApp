from flask import Flask, render_template, request, redirect, url_for, flash
from controller.config import config
from controller.database import db
from flask import session
from controller.models import *

app = Flask(__name__)

app.config.from_object(config)

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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Filter out Admin (ID 1) so only Student and Teacher show up
    available_roles = Role.query.filter(Role.id != 1).all()
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role_id = request.form.get("role_id")

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Assign the selected role
        user_role = UserRole(user_id=new_user.id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        
        return redirect(url_for('login'))

    return render_template("register.html", roles=available_roles)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # 1. Find user by email
        user = User.query.filter_by(email=email).first()

        # 2. Check if user exists and password matches
        if user and user.password == password: # In production, use hashed passwords!
            
            # 3. Get the user's role ID from the UserRole table
            user_role_entry = UserRole.query.filter_by(user_id=user.id).first()
            role_id = user_role_entry.role_id

            # 4. Redirect based on your database IDs (2=Staff, 3=Student)
            if role_id == 2:
                return redirect(url_for('staff_dashboard'))
            elif role_id == 3:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid credentials, please try again."

    return render_template("login.html")

@app.route("/staff/dashboard")
def staff_dashboard():
    # For your demo, we'll fetch the 'admin' or first 'Teacher' user
    # In a full app, you'd use session['user_id']
    user = User.query.filter_by(username="admin").first() 
    
    # Fetch all users who have the 'Student' role (Role ID 3)
    students = User.query.join(UserRole).filter(UserRole.role_id == 3).all()
    
    # Example stats for the dashboard cards
    stats = {
        'total_students': len(students),
        'active_quizzes': 5,  # Static for now
        'avg_score': "82%"    # Static for now
    }
    
    return render_template("staff_dashboard.html", user=user, students=students, stats=stats)

@app.route("/student/dashboard")
def student_dashboard():
    # In a real app, pass the logged-in student's data here
    return render_template("student_dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)