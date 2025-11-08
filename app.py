from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Book, BorrowRecord 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_change_me' # IMPORTANT: Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elibrary.db' # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Set the route for mandatory login

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Initialization ---
with app.app_context():
    db.create_all()
    # Optional: Add an Admin user if none exists for initial setup
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('adminpass', method='pbkdf2:sha256')
        admin_user = User(username='admin', password_hash=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: username='admin', password='adminpass'")

# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))

        # Securely hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Only show available books to students
    books = Book.query.filter_by(available=True).all()
    return render_template('dashboard.html', books=books)

@app.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if not book.available:
        flash(f'The book "{book.title}" is currently unavailable.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Check if the user already has an active loan for this book
    active_loan = BorrowRecord.query.filter_by(user_id=current_user.id, book_id=book.id, is_active=True).first()
    if active_loan:
        flash(f'You have already borrowed "{book.title}".', 'warning')
        return redirect(url_for('my_books'))

    try:
        # 1. Create Loan Record
        new_loan = BorrowRecord(user_id=current_user.id, book_id=book.id)
        db.session.add(new_loan)
        
        # 2. Update Book Availability
        book.available = False
        
        db.session.commit()
        flash(f'Successfully borrowed "{book.title}". Check "My Books".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/my_books')
@login_required
def my_books():
    # Fetch all active loans for the current user
    active_loans = BorrowRecord.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('my_books.html', loans=active_loans)

@app.route('/return/<int:loan_id>', methods=['POST'])
@login_required
def return_book(loan_id):
    loan = BorrowRecord.query.get_or_404(loan_id)
    
    if loan.user_id != current_user.id or not loan.is_active:
        flash('Invalid loan attempt.', 'danger')
        return redirect(url_for('my_books'))
        
    try:
        # 1. Update Loan Record
        loan.return_date = datetime.utcnow()
        loan.is_active = False
        
        # 2. Update Book Availability
        book = Book.query.get(loan.book_id)
        book.available = True
        
        db.session.commit()
        flash(f'Successfully returned "{book.title}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
        
    return redirect(url_for('my_books'))


if __name__ == '__main__':
    app.run(debug=True)