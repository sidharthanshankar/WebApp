from controller.database import db
from datetime import datetime

class Role(db.Model):
    _tablename_ = "role"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def _repr_(self):
        return f"<Role {self.name}>"


class User(db.Model):
    _tablename_ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    roles = db.relationship("UserRole", back_populates="user")

    def _repr_(self):
        return f"<User {self.username}>"


class UserRole(db.Model):
    _tablename_ = "user_role"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)

    user = db.relationship("User", back_populates="roles")
    role = db.relationship("Role")

    def _repr_(self):
        return f"<UserRole user={self.user_id} role={self.role_id}>"
    
class Quiz(db.Model):
     _tablename_ = "quiz"
     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
     title = db.Column(db.String(100), nullable=False)
     creator_id = db.Column(db.Integer, db.ForeignKey("user.id")) # Link to Staff

class Question(db.Model):
    _tablename_ = "question"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"))
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False) # Stores ['A','B','C','D']
    correct_answer = db.Column(db.String(100), nullable=False)

class StudentScore(db.Model):
    _tablename_ = "student_score"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # Who took it
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id")) # Which quiz
    score = db.Column(db.Integer) # The score (e.g., 85)
    total_questions = db.Column(db.Integer) # Total questions in that quiz


class StudentResult(db.Model):
    _tablename_ = "student_result"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="results")
    quiz = db.relationship("Quiz", backref="results")

class StudentAnswer(db.Model):
    _tablename_ = "student_answer"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    selected_option = db.Column(db.String(200), nullable=False) # e.g., "A" or the text
    is_correct = db.Column(db.Boolean, nullable=False)

    user = db.relationship("User", backref="answers")
    question = db.relationship("Question")


