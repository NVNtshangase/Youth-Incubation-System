from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from models.models import User,Course, db, Student
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from blue_prints.donation import donation_bp
from blue_prints.application import application_bp
from blue_prints.certificate import certificate_bp
from werkzeug.security import generate_password_hash, check_password_hash  # Import password hashing functions

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////workspaces/Youth-Incubation-System/YUI Inc/instance/site.db'


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

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    student = Student.query.filter_by(student_email=current_user.username).first()
    print(student)
    if request.method == 'POST':
        name = request.form.get('first_name')
        surname = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone_number')

        student.student_name = name
        student.student_surname = surname
        student.student_email = email
        student.student_phone_number = phone

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('home'))

    return render_template('update_profile.html', student=student)

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    student = Student.query.filter_by(student_email=current_user.username).first()
    user = User.query.filter_by(username=current_user.username).first()
    print(student)
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not check_password_hash(current_user.password, old_password):
            flash('Incorrect password. Try Again.', 'danger')
            return redirect(url_for('update_profile', student=student))
        if new_password != confirm_new_password:
            flash('New password does not match.', 'danger')
            return redirect(url_for('update_profile', student=student))
        
        user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Password updated successfully.', 'success')
        return redirect(url_for('home'))

    return render_template('update_profile.html', student=student)

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
            seed_courses()
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            flash('Login failed. Check your email and/or password.', 'danger')

    return render_template('login.html')  # Render login form

# Define a list of courses to seed into the database
practical_skill_courses = [
    {"course_name": "Beauty Therapy & Skin Care", "course_description": "Learn about skin care and beauty techniques.", "course_duration": "3 months", "course_cost": 500.00},
    {"course_name": "Pet Grooming", "course_description": "Train to be a pet grooming specialist.", "course_duration": "2 months", "course_cost": 300.00},
    {"course_name": "Automotive Mechanics", "course_description": "Learn how to maintain and repair cars.", "course_duration": "6 months", "course_cost": 1000.00},
    {"course_name": "Culinary Arts & Cooking", "course_description": "Master the art of cooking and culinary techniques.", "course_duration": "4 months", "course_cost": 700.00},
    {"course_name": "Basic Coding", "course_description": "Get started with basic programming and coding concepts.", "course_duration": "2 months", "course_cost": 200.00},
    {"course_name": "Floristry", "course_description": "Learn the art of floral arrangement.", "course_duration": "1 month", "course_cost": 150.00},
    {"course_name": "Masonry & Bricklaying", "course_description": "Train to become a professional bricklayer.", "course_duration": "4 months", "course_cost": 800.00},
    {"course_name": "Welding", "course_description": "Learn welding skills for various industries.", "course_duration": "5 months", "course_cost": 850.00},
    {"course_name": "Computer Repair & Maintenance", "course_description": "Learn to troubleshoot and repair computers.", "course_duration": "3 months", "course_cost": 400.00},
    {"course_name": "HVAC Technician", "course_description": "Become skilled in heating, ventilation, and air conditioning.", "course_duration": "6 months", "course_cost": 1200.00},
    {"course_name": "Financial Literacy", "course_description": "Understand personal finance and money management.", "course_duration": "1 month", "course_cost": 100.00},
    {"course_name": "Social Media Marketing", "course_description": "Learn marketing techniques for social media platforms.", "course_duration": "2 months", "course_cost": 300.00},
    {"course_name": "Hairdressing & Barbering", "course_description": "Train to become a professional hairdresser or barber.", "course_duration": "3 months", "course_cost": 600.00},
    {"course_name": "Landscaping & Gardening", "course_description": "Learn the basics of landscaping and gardening.", "course_duration": "2 months", "course_cost": 350.00},
    {"course_name": "Carpentry", "course_description": "Learn essential woodworking skills.", "course_duration": "4 months", "course_cost": 900.00},
    {"course_name": "Makeup Artistry", "course_description": "Master makeup techniques for professional applications.", "course_duration": "2 months", "course_cost": 400.00},
    {"course_name": "Pottery & Ceramics", "course_description": "Learn the art of pottery and ceramics.", "course_duration": "2 months", "course_cost": 200.00},
    {"course_name": "Electrical Installation", "course_description": "Become skilled in electrical installation and wiring.", "course_duration": "5 months", "course_cost": 1000.00},
    {"course_name": "Web Design & Development", "course_description": "Learn to create modern, responsive websites.", "course_duration": "4 months", "course_cost": 800.00},
    {"course_name": "Sewing & Tailoring", "course_description": "Master sewing and garment-making skills.", "course_duration": "3 months", "course_cost": 500.00},
    {"course_name": "Plumbing", "course_description": "Learn the fundamentals of plumbing.", "course_duration": "4 months", "course_cost": 850.00},
    {"course_name": "Small Business Management", "course_description": "Learn how to manage and grow a small business.", "course_duration": "3 months", "course_cost": 600.00},
    {"course_name": "Graphic Design", "course_description": "Develop creative design skills using digital tools.", "course_duration": "4 months", "course_cost": 700.00},
    {"course_name": "Jewelry Making", "course_description": "Learn the craft of making jewelry.", "course_duration": "2 months", "course_cost": 300.00},
    {"course_name": "Photography", "course_description": "Learn the fundamentals of photography.", "course_duration": "2 months", "course_cost": 400.00},
]

# Function to seed the courses into the database
def seed_courses():
    for course_data in practical_skill_courses:
        # Check if the course already exists to avoid duplicates
        existing_course = Course.query.filter_by(course_name=course_data["course_name"]).first()
        if not existing_course:
            new_course = Course(
                course_name=course_data["course_name"],
                course_description=course_data["course_description"],
                course_duration=course_data["course_duration"],
                course_cost=course_data["course_cost"]
            )
            db.session.add(new_course)
    
    # Commit the session to save the courses in the database
    db.session.commit()



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
