# database.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

# Initialize the database extension
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model for storing login information.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)

    def set_password(self, password):
        """Creates a secure hash for the user's password."""
        self.password_hash = generate_password_hash(password)


class History(db.Model):
    """
    History model for storing analysis results.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Updated field: stores image file path instead of just name
    image_path = db.Column(db.String(300))  

    analysis = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationship: connect history items to their user
    user = db.relationship('User', backref=db.backref('history', lazy=True))