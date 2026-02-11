from controller.database import db

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
    

