from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from models.models import User, db
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from blue_prints.donation import donation_bp
from blue_prints.application import application_bp
from blue_prints.certificate import certificate_bp
from werkzeug.security import generate_password_hash, check_password_hash  # Import password hashing functions

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Make sure to change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update this to your database

# Initialize the database
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect here if not logged in

# Register Blueprints
app.register_blueprint(donation_bp)
app.register_blueprint(application_bp)
app.register_blueprint(certificate_bp)

# Load user function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Sample routes
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(username=email).first()  # Find the user by email

        if user and check_password_hash(user.password, password):  # Check password
            login_user(user)  # Log the user in
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            flash('Login failed. Check your email and/or password.', 'danger')

    return render_template('login.html')  # Render login form

# Logout route
@app.route('/logout')
@login_required  # Ensure the user is logged in to access this route
def logout():
    logout_user()  # Log the user out
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))  # Redirect to the home page

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
