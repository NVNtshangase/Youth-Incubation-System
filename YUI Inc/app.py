from flask import Flask, render_template, redirect, session, url_for, flash, request
from models.models import Donor, FinancialAid, Student, User,Course, db
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from blue_prints.donation import donation_bp
from blue_prints.application import application_bp
from blue_prints.certificate import certificate_bp
from werkzeug.security import check_password_hash 
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = ' ty7u8miooimnhbg-40_6jko0-6ojy'  
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

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    student = Student.query.filter_by(student_email=current_user.username).first()
    donor = Donor.query.filter_by(donor_email=current_user.username).first()
    
    if student is None and donor is None:
        flash('Profile not found. Please log in again.', 'danger')
        return redirect(url_for('login'))  # Redirect to login or another appropriate page

    # If the user is a student, use the student profile. If they're a donor, use the donor profile.
    user_profile = student if student else donor

    if request.method == 'POST':
        name = request.form.get('first_name')
        surname = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone_number')

        # Update profile based on the user type
        if student:
            student.student_name = name
            student.student_surname = surname
            student.student_email = email
            student.student_phone_number = phone
            
            # Check if email has changed
            if email != current_user.username:
                # Update the username in the User table
                user = User.query.filter_by(username=current_user.username).first()
                user.username = email
                current_user.username = email  # Update current_user's username

        elif donor:
            donor.donor_name = name
            donor.donor_surname = surname
            donor.donor_email = email
            donor.donor_phone_number = phone
            
            # Check if email has changed
            if email != current_user.username:
                # Update the username in the User table
                user = User.query.filter_by(username=current_user.username).first()
                user.username = email
                current_user.username = email  # Update current_user's username

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('update_profile.html', user_profile=user_profile)

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
        
        # Retrieve the user by email
        user = User.query.filter_by(username=email).first()  

        if user and check_password_hash(user.password, password):  
            login_user(user) 
            session['user_id'] = user.id  
            flash('Login successful!', 'success')
            #seed_courses()
            return redirect(url_for('dashboard'))  
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
    total_applications = 0  # Initialize to hold the number of applications

    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
   
        if student:
            # Count the number of financial aid applications for the student
            total_applications = FinancialAid.query.filter_by(student_code=student.student_code).count()
            
    elif user.role == 'donor':
        donor = Donor.query.filter_by(user_id=user.id).first()
    else:
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('home'))

    return render_template('dashboard.html', user=user, student=student, donor=donor, total_applications=total_applications)

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

@app.route('/status', methods=['GET'])
@login_required
def status():
    try:
        student_profile = Student.query.filter_by(user_id=current_user.id).first()

        if student_profile is None:
            flash("You do not have a student profile associated with your account.", 'warning')
            return redirect(url_for('dashboard'))

        # Query the earliest FinancialAid application
        earliest_application = FinancialAid.query.filter_by(student_code=student_profile.student_code).order_by(FinancialAid.application_date.asc()).first()

        # Collect course info for the earliest application
        earliest_application_details = {}
        if earliest_application:
            # Get course details through the student relationship
            student_course = Course.query.filter_by(course_id=student_profile.course_code).first() 
            earliest_application_details = {
                'application': earliest_application,
                'course': student_course
            }


        # Query all FinancialAid applications for the student
        applications = FinancialAid.query.filter_by(student_code=student_profile.student_code).all()

        # Collect course info for each application
        application_details = []
        for application in applications:
            # Use the courses property to get the courses related to this financial aid application
            courses = application.courses  # This will use the courses property defined above

            # Append the application and its corresponding courses to the details list
            application_details.append({
                'application': application,
                'courses': courses  
            })

        return render_template('status.html', earliest_application_details=earliest_application_details, application_details=application_details)

    except Exception as e:
        flash(f"An error occurred while fetching your application status: {e}", 'danger')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)