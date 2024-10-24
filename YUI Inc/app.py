from flask import Flask, render_template, redirect, send_file, session, url_for, flash, request
import requests, os
from models.models import Certificate, Donor, FinancialAid, Payment, Student, User,Course, db
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from blue_prints.donation import donation_bp
from blue_prints.application import application_bp
from blue_prints.certificate import certificate_bp
from werkzeug.security import check_password_hash ,generate_password_hash
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = ' ty7u8miooimnhbg-40_6jko0-6ojycdfvgbhjnmknbgvfcdxsdfgvbhju3etyrty2uhij'  
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

@app.route('/payment')
def payment():
    return render_template('payment.html')

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
    is_student = student is not None

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

    return render_template('update_profile.html', user_profile=user_profile,student=is_student)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Get the reCAPTCHA keys from environment variables
    sec_pk_nv = os.getenv('alt_pk')
    sec_sk_nv = os.getenv('alt_sk')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')  # Use get() instead of direct access

        recaptcha_verify_url = f"https://www.google.com/recaptcha/api/siteverify?secret={sec_sk_nv}&response={recaptcha_response}"
        
        # Verify reCAPTCHA
        response = requests.post(recaptcha_verify_url)
        result = response.json()

        if not result.get('success'):
            flash('Please complete the reCAPTCHA.', 'danger')
            return render_template('login.html', sc_pk_nv=sec_pk_nv)

        # Retrieve the user by email
        user = User.query.filter_by(username=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id
            
            # Check if the user is a donor and get the donor code
            if user.role == 'donor':
                donor = Donor.query.filter_by(user_id=user.id).first()
                if donor:
                    session['donor_code'] = donor.donor_code  
            seed_courses()
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')

    return render_template('login.html', sc_pk_nv=sec_pk_nv)

@app.route('/dashboard')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:  # Check if user_id is in session
        flash("You need to log in to access the dashboard.", 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id']) 
    student = None
    donor = None
    total_applications = 0 
    certificates_count = 0  # Initialize the count
    donor_balance = 0  # Initialize donor balance

    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
   
        if student:
            # Count the number of financial aid applications for the student
            total_applications = FinancialAid.query.filter_by(student_code=student.student_code).count()
            
    elif user.role == 'donor':
        donor = Donor.query.filter_by(user_id=user.id).first()
        
        if donor:
            donor_balance = donor.balance  # Get the donor's balance
            # Retrieve matches based on donor's balance
            donor.matches = get_recommended_students(donor_balance)  # Fetch matches for the donor
            certificates_count = Certificate.query.filter_by(donor_code=donor.donor_code).count()
    
    else:
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('home'))

    return render_template('dashboard.html', user=user, student=student, donor=donor, 
                           total_applications=total_applications, 
                           certificates_count=certificates_count, 
                           donor_balance=donor_balance)

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

@app.route('/certificate-history')
def certificate_history():
    donor_code = session.get('donor_code')
    print(f"Donor Code from session: {donor_code}")  # Debugging line

    # Query the certificates for this donor
    certificates = Certificate.query.filter_by(donor_code=donor_code).all()

    return render_template('certificate_history.html', certificates=certificates)

@app.route('/download-certificate/<int:certificate_id>')
def download_certificate(certificate_id):
    try:
        # Fetch the certificate by ID
        certificate = Certificate.query.get_or_404(certificate_id)  # Raises 404 if not found

        # Generate the file path based on donor code and certificate ID
        pdf_filename = f"{certificate.donor_code}_{certificate.id}_certificate.pdf"
        pdf_path = os.path.join('certificates', pdf_filename)

        # Check if the file exists before sending it
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)

        # If the file does not exist, flash a more informative message
        flash(
            'The certificate file is not available for download. '
            'Please check the email you received after making the donation transaction.',
            'warning'
        )
        return redirect(url_for('certificate_history'))  # Redirect to the certificate history page

    except Exception as e:
        # Log the exception for debugging (optional)
        print(f"An error occurred: {e}")
        flash(
            'An unexpected error occurred while trying to download the certificate. '
            'Please try again later or contact support if the issue persists.',
            'danger'
        )
        return redirect(url_for('certificate_history'))  # Redirect to the certificate history page

@app.route('/donor_dashboard/match_students', methods=['GET'])
@login_required
def match_students():
    if current_user.role != 'donor':
        return redirect(url_for('home'))  # Redirect if not a donor

    # Fetch the donor's balance
    donor = Donor.query.filter_by(user_id=current_user.id).first()

    if not donor:
        flash('Donor account not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Get recommended students based on the donor's balance
    recommended_students = get_recommended_students(donor.balance)

    if not recommended_students:
        flash('There are no students awaiting funding at this time.', 'info')

    # Pass both the students and donor information to the template
    return render_template('match_students.html', students=recommended_students, donor=donor)

def get_recommended_students(donor_balance):
    # Query students with application status 'awaiting funding'
    students = Student.query.join(FinancialAid).filter(
        FinancialAid.application_status == 'awaiting funding',
        Student.owing_amount <= donor_balance
    ).all()
    
    return students

from ortools.sat.python import cp_model

@app.route('/allocate_funds/<int:student_id>', methods=['POST'])
@login_required
def allocate_funds(student_id):
    donor = Donor.query.filter_by(user_id=current_user.id).first()
    student = Student.query.get(student_id)

    if student and donor:
        # Ensure the owing amount and donor balance are integers
        owing_amount = int(student.owing_amount)  # Convert to integer
        donor_balance = int(donor.balance)          # Convert to integer

        # Create the CP model
        model = cp_model.CpModel()

        # Create variables
        allocate = model.NewBoolVar(f'allocate_{student.student_code}')

        # Set the constraints
        model.Add(allocate * owing_amount <= donor_balance)  # Ensure allocation does not exceed donor balance

        # Objective: Maximize the total amount allocated
        model.Maximize(allocate * owing_amount)

        # Create the solver
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # If a feasible solution is found, allocate funds
            donor.balance -= owing_amount
            
            # Create a payment record
            payment = Payment(payment_amount=owing_amount, donor_code=donor.donor_code)
            db.session.add(payment)
            
            # Update the financial aid record
            financial_aid = FinancialAid.query.filter_by(student_code=student.student_code).first()
            
            if financial_aid:
                financial_aid.donor_code = donor.donor_code  # Assign donor to the financial aid
                financial_aid.application_status = 'approved'  # Change status to approved
            
            db.session.commit()  # Commit all changes to the database
            
            return redirect(url_for('match_students'))
        else:
            return "No feasible allocation found.", 400
    else:
        # Handle insufficient funds or student not found
        return "Insufficient funds or student not found", 400
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)