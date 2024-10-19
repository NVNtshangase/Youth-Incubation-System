from flask import Flask, jsonify, render_template, redirect, url_for, flash, session,request
from models.models import FinancialAid, User,Course,Donor,Student, db
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from blue_prints.donation import donation_bp
from blue_prints.application import application_bp
from blue_prints.certificate import certificate_bp
from werkzeug.security import check_password_hash 

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

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Retrieve the user by email
        user = User.query.filter_by(username=email).first()  

        if user and check_password_hash(user.password, password):  
            login_user(user) 
            session['user_id'] = user.id  
            flash('Login successful!', 'success')
            #seed_courses()
            return redirect(url_for('home'))  
        else:
            flash('Login failed. Check your email and/or password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:  # Check if user_id is in session
        flash("You need to log in to access the dashboard.", 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id']) 
    student = None
    donor = None

    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
    elif user.role == 'donor':
        donor = Donor.query.filter_by(user_id=user.id).first()
    else:
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('home'))

    return render_template('dashboard.html', user=user, student=student, donor=donor)

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

# Profile
@app.route('/profile')
@login_required
def profile():
    try:
        # Ensure the role is available and check the user role
        if current_user.role == 'student':
            profile = Student.query.filter_by(user_id=current_user.id).first()  # Corrected to match user_id
        elif current_user.role == 'donor':
            profile = Donor.query.filter_by(user_id=current_user.id).first()  # Corrected to match user_id
        else:
            flash('You do not have access to this page.', 'warning')
            return redirect(url_for('home'))

        # Handle missing profile cases
        if profile is None:
            flash('Profile not found. Please complete your profile first.', 'warning')
            return redirect(url_for('home'))

        # Render the profile template with appropriate data
        return render_template('profile.html', profile=profile, role=current_user.role)

    except Exception as e:
        # Handle any errors that occur
        flash(f"An error occurred while fetching your profile: {str(e)}", "danger")
        return redirect(url_for('home'))
    
@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        # Get the current user from the session
        user = User.query.filter_by(id=current_user.id).first()

        # Check if the user exists
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))

        # Check the user's role and delete related records
        if user.role == 'student':
            student_profile = Student.query.filter_by(user_id=user.id).first()
            if student_profile:
                db.session.delete(student_profile)  # This deletes the student record

        elif user.role == 'donor':
            donor_profile = Donor.query.filter_by(user_id=user.id).first()
            if donor_profile:
                db.session.delete(donor_profile)  # This deletes the donor record

        # Delete the user record itself
        db.session.delete(user)

        # Commit all changes to the database
        db.session.commit()

        # Log the user out after deleting the account
        logout_user()

        flash('Your account and all associated data have been successfully deleted.', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()  # Rollback in case of any error
        flash(f"An error occurred while deleting your account: {str(e)}", 'danger')
        return redirect(url_for('profile'))

# Logout route
@app.route('/logout')
@login_required  
def logout():
    logout_user()  
    flash('You have been logged out.', 'info')  
    return redirect(url_for('home'))  

#App progress
@app.route('/status', methods=['GET'])
@login_required
def status():
    student_profile = Student.query.filter_by(user_id=current_user.id).first()

    if student_profile is None:
        flash("You do not have a student profile associated with your account.", 'warning')
        return redirect(url_for('dashboard'))

    # Query the FinancialAid table for the current user's application status
    application = FinancialAid.query.filter_by(student_code=student_profile.student_code).first()

    if application:
        status = application.application_status
        application_date = application.application_date
    else:
        status = "No application found."
        application_date = None

    return render_template('status.html', status=status, application_date=application_date)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)