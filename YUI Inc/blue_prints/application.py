from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_login import current_user
import pytz
from models.models import Take, User, Student, Course, FinancialAid, db
from blue_prints.donation import (
    validate_email,
    validate_name,
    validate_cellphone_number,
    validate_password,
    validate_id_number,
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

application_bp = Blueprint('application', __name__)

def extract_dob_from_sa_id(id_number):
    try:
        dob_str = id_number[:6] 
        year = int(dob_str[:2])  
        month = int(dob_str[2:4])  
        day = int(dob_str[4:6])  

        # Determine the century based on the year
        if year >= 0 and year <= 22:  
            year += 2000
        elif year >= 23 and year <= 99: 
            year += 1900
        else:
            raise ValueError("Invalid year in ID number")

        # Create the date of birth
        dob = datetime(year, month, day).date()
        return dob
    except (ValueError, IndexError):
        return None

def calculate_age(dob):
    today = datetime.now().date() 
    age = today.year - dob.year  

    # Adjust age if the birthday hasn't occurred yet this year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1

    return age

@application_bp.route('/apply/<int:course_id>', methods=['GET', 'POST'])
def application(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        application_info = request.form
        error_fields = []

        # Validate form data
        if not validate_name(application_info['name']):
            flash("Invalid name. Name should only contain alphabetic characters.", 'error')
            error_fields.append('First Name')
        if not validate_name(application_info['surname']):
            flash("Invalid surname. Surname should only contain alphabetic characters.", 'error')
            error_fields.append('Last Name')
        if not validate_email(application_info['email']):
            flash("Invalid email address.", 'error')
            error_fields.append('Email')
        if not validate_cellphone_number(application_info['full_phone_number']):
            flash('Invalid phone number format.', 'error')
            error_fields.append('Cellphone Number')
        if not validate_id_number(application_info['id_number']):
            flash("Invalid ID number. Must be 13 digits and valid.", 'error')
            error_fields.append('ID number')

        password_error = validate_password(application_info['password'])
        if password_error:
            flash(password_error, 'error')
            error_fields.append('Password')

        if application_info['password'] != application_info['password-confirm']:
            flash("Passwords do not match.", 'error')
            error_fields.append('Password')

        # Extract date of birth from ID number
        dob = extract_dob_from_sa_id(application_info['id_number'])
        if dob is None:
            flash("Invalid ID number. Unable to extract date of birth.", 'error')
            error_fields.append('ID number')
        else:
            # Calculate age using the dob
            age = calculate_age(dob)  
            current_date = datetime.now().date()
            age_in_days = (current_date - dob).days
            min_age_days = 15 * 365
            max_age_days = 35 * 365

            if not (min_age_days <= age_in_days <= max_age_days):
                dob_str = dob.strftime('%Y-%m-%d')  # Format date of birth for display
                flash(f"You must be between 15 and 35 years old to apply. ID Number: {application_info['id_number']}, Age: {age} years, Date of Birth: {dob_str}", 'error')
                error_fields.append('Date of Birth')


        # Check for existing records
        existing_user = User.query.filter_by(username=application_info['email']).first()
        if existing_user:
            flash("Email already registered. Please log in instead.", 'error')
            return redirect(url_for('home'))

        existing_applicant = Student.query.filter_by(student_id_number=application_info['id_number']).first()
        if existing_applicant:
            flash("A profile with this ID number already exists. Please log in or contact support.", 'error')
            return redirect(url_for('home'))

        existing_applicant_cell = Student.query.filter_by(student_phone_number=application_info['full_phone_number']).first()
        if existing_applicant_cell:
            flash("A profile with this cellphone number already exists. Please log in or contact support.", 'error')
            return redirect(url_for('home'))

        if error_fields:
            # Render the form again but pass the previously entered data back to the form
            return render_template(
                'application.html', 
                course=course, 
                request=request, 
                error_fields=error_fields,
                application_info=application_info
            )

        try:
            # Create a new user with hashed password
            new_user = User(
                username=application_info['email'].strip(),
                password=generate_password_hash(application_info['password'].strip()),  
                role='student'
            )
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id

            # Create student and financial aid entries
            new_student = Student(
                student_id_number=application_info['id_number'].strip(),
                student_name=application_info['name'].strip().capitalize(),
                student_surname=application_info['surname'].strip().capitalize(),
                student_date_of_birth=dob,  
                student_race=application_info['race'],
                student_nationality=application_info['nationality'],
                student_phone_number=application_info['full_phone_number'].strip(),
                student_email=application_info['email'].strip(),
                student_physical_address=application_info['physical_address'],
                student_highest_grade=application_info['highest_grade'].strip(),
                student_financial_status=application_info['financial_status'].strip(),
                disability=application_info.get('disability', ''), 
                criminal_record=application_info.get('criminal_record', ''),
                age=age,
                owing_amount=int(course.course_cost),
                user_id=new_user.id,
                course_code=course.course_id
            )

            db.session.add(new_student)
            db.session.commit()
            
            sast_timezone = pytz.timezone('Africa/Johannesburg')
            sast_time = datetime.now(sast_timezone)

            new_financial_aid = FinancialAid(
                student_code=new_student.student_code, 
                donor_code=None, 
                application_status='Pending',  
                application_date=sast_time  
            )
            db.session.add(new_financial_aid)
            db.session.commit()
            process_financial_aid_applications()

            session['student_id'] = new_student.student_code 
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", 'danger')

    current_date = datetime.now()
    return render_template(
        'application.html', 
        course=course, 
        current_date=current_date  
    )

@application_bp.route('/apply/course/<int:course_id>', methods=['POST'])
def apply(course_id):
    if not current_user.is_authenticated:
        flash("You need to log in to apply for a course.", 'danger')
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        flash("Student profile not found.", 'danger')
        return redirect(url_for('home'))

    course = Course.query.get_or_404(course_id)

    # Check if the student record exists for this course in the 'Student' table
    existing_student_course_application = Student.query.filter_by(student_id_number=student.student_id_number).first()
    
    if existing_student_course_application and existing_student_course_application.course_code == course.course_id:
        flash("You cannot apply for this course again. Please choose a different course.", 'warning')
        return redirect(url_for('application.course_view'))

    # Check the number of current applications for the student
    current_applications_count = Take.query.filter_by(student_code=student.student_code).count()

    if current_applications_count >= 1:
        flash("You cannot apply for more than 2 courses at the same time.", 'warning')
        return redirect(url_for('application.course_view'))

    try:
        # Create a new entry in the 'Take' table
        new_enrollment = Take(
            student_code=student.student_code,
            course_id=course.course_id
        )
        db.session.add(new_enrollment)

        # Create a financial aid entry (if applicable)
        sast_timezone = pytz.timezone('Africa/Johannesburg')
        sast_time = datetime.now(sast_timezone)

        new_financial_aid = FinancialAid(
            student_code=student.student_code,
            donor_code=None,  
            application_status='Pending',
            application_date=sast_time
        )
        
        db.session.add(new_financial_aid)
        db.session.commit()
        process_financial_aid_applications()

        flash('Application submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        db.session.rollback()  # Roll back the session if an error occurs
        flash(f"Error submitting application: {e}", 'danger')
        return redirect(url_for('application.course_view'))
    
@application_bp.route('/courses', methods=['GET'])
def course_view():
    courses = Course.query.all() 
    return render_template('course_view.html', courses=courses)

@application_bp.route('/withdraw/<int:course_id>', methods=['POST'])
def withdraw_application(course_id):
    if not current_user.is_authenticated:
        flash("You need to log in to withdraw an application.", 'danger')
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        flash("Student profile not found.", 'danger')
        return redirect(url_for('home'))

    course = Course.query.get_or_404(course_id)

    # Check if there is a financial aid application for the student and course
    financial_aid = FinancialAid.query.filter_by(student_code=student.student_code, application_status='awaiting funding').first()

    if not financial_aid:
        flash("No awaiting funding application found to withdraw.", 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Optionally, remove the course enrollment if linked to the application
        enrollment = Take.query.filter_by(student_code=student.student_code, course_id=course.course_id).first()

        if enrollment:
            db.session.delete(enrollment)

        # Delete the financial aid application
        db.session.delete(financial_aid)
        db.session.commit()

        flash('Application withdrawn successfully!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        db.session.rollback()  # Roll back the session if an error occurs
        flash(f"Error withdrawing application: {e}", 'danger')
        return redirect(url_for('application.course_view'))

# Function to calculate eligibility score
def calculate_eligibility_score(student):
    score = 0
    
    # Scoring based on race
    race_priority = {
        "African": 20,
        "Coloured": 15,
        "Indian": 10,
        "White": 5
    }
    score += race_priority.get(student.student_race, 0)
    
    # Scoring based on nationality
    nationality_priority = {
        "South African": 20,
        "African": 15,
        "Asian": 10,
        "European": 5,
        "American": 5,
        "Australian": 5
    }
    score += nationality_priority.get(student.student_nationality, 0)
    
    # Scoring based on highest grade
    highest_grade_priority = {
        "10": 20,
        "11": 20,
        "12": 20,
        "7": 15,
        "8": 15,
        "9": 15,
        "0": 5,
        "1": 5,
        "2": 5,
        "3": 5,
        "4": 5,
        "5": 5,
        "6": 5
    }
    score += highest_grade_priority.get(student.student_highest_grade, 0)
    
    # Scoring based on financial status
    financial_status_priority = {
        "Below 100000": 20,
        "100000-200000": 15,
        "200000-300000": 10,
        "Above 300000": 5
    }
    score += financial_status_priority.get(student.student_financial_status, 0)
    
    # Scoring based on disability
    if student.disability == "Yes":
        score += 10

    # Scoring based on criminal record (penalty if "Yes")
    if student.criminal_record == "Yes":
        score -= 10
    
    # Scoring based on age
    if 25 <= student.age <= 35:
        score += 20
    elif 20 <= student.age < 25:
        score += 15
    elif 15 <= student.age < 20:
        score += 5
    
    return score

# Function to process financial aid applications
def process_financial_aid_applications():
    # Query financial aid applications
    financial_aid_apps = FinancialAid.query.filter_by(application_status='Pending').all()
    
    for application in financial_aid_apps:
        # Get the student information based on student_code
        student = Student.query.filter_by(student_code=application.student_code).first()
        
        # Ensure maximum of 2 application records per student
        student_apps_count = FinancialAid.query.filter_by(student_code=student.student_code).count()
        if student_apps_count > 2:
            application.application_status = "declined"
            db.session.commit()
            continue
        
        # Calculate eligibility score
        eligibility_score = calculate_eligibility_score(student)
        
        # Determine status based on score threshold
        if eligibility_score >= 60:  # Example: 60 is the threshold for approval
            application.application_status = "awaiting funding"
        else:
            application.application_status = "declined"
        
        # Commit changes to database
        db.session.commit()