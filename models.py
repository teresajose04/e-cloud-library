from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

# ----------------- User Model -----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Stores the HASHED password
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationship: A user can have many loans
    loans = db.relationship('BorrowRecord', backref='student', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# ----------------- Book Model -----------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=True)
    digital_link = db.Column(db.String(500), nullable=False) # Secure URL to the digital file
    available = db.Column(db.Boolean, default=True)
    
    # Relationship: A book can be involved in many loans
    borrowed_by = db.relationship('BorrowRecord', backref='book_loaned', lazy=True)

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'

# ----------------- Borrow Record Model -----------------
class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    return_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True) # Used to easily filter current loans

    def __repr__(self):
        return f'<Loan User:{self.user_id} Book:{self.book_id}>'