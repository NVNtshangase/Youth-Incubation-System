from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models.models import User, Student, Course, FinancialAid, db
from blue_prints.donation import (
    validate_email,
    validate_name,
    validate_cellphone_number,
    validate_password,
    validate_id_number,
)
from datetime import datetime
from werkzeug.security import generate_password_hash

application_bp = Blueprint('application', __name__)

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
        if not validate_cellphone_number(application_info['phone_number']):
            flash("Invalid phone number. Must be 10 digits.", 'error')
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

        # Check if the email already exists
        existing_user = User.query.filter_by(username=application_info['email']).first()
        if existing_user:
            flash("Email already registered. Please log in instead.", 'error')
            return redirect(url_for('home'))

        # Check if the ID number already exists
        existing_applicant = Student.query.filter_by(student_id_number=application_info['id_number']).first()
        if existing_applicant:
            flash("A profile with this ID number already exists. Please log in or contact support.", 'error')
            return redirect(url_for('home'))

        # Check if the cellphone number already exists
        existing_applicant_cell = Student.query.filter_by(student_phone_number=application_info['phone_number']).first()
        if existing_applicant_cell:
            flash("A profile with this cellphone number already exists. Please log in or contact support.", 'error')
            return redirect(url_for('home'))

        if error_fields:
            return render_template('application.html', course=course, request=request, error_fields=error_fields)

        try:
            # Create a new user with hashed password
            new_user = User(
                username=application_info['email'].strip(),
                password=generate_password_hash(application_info['password'].strip()),  
                role='student'
            )
            db.session.add(new_user)
            db.session.commit()

            # Create student and financial aid entries
            student_date_of_birth = datetime.strptime(application_info['date_of_birth'], '%Y-%m-%d').date()
            new_student = Student(
                student_id_number=application_info['id_number'].strip(),
                student_name=application_info['name'].strip().capitalize(),
                student_surname=application_info['surname'].strip().capitalize(),
                student_date_of_birth=student_date_of_birth,
                student_race=application_info['race'],
                student_nationality=application_info['nationality'],
                student_phone_number=application_info['phone_number'].strip(),
                student_email=application_info['email'].strip(),
                student_physical_address=application_info['physical_address'],
                student_highest_grade=application_info['highest_grade'].strip(),
                student_financial_status=application_info['financial_status'].strip(),
                user_id=new_user.id,
                course_code=course.course_id
            )

            db.session.add(new_student)
            db.session.commit()

            session['student_id'] = new_student.student_code 
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", 'danger')

    return render_template('application.html', course=course)

@application_bp.route('/courses', methods=['GET'])
def course_view():
    courses = Course.query.all()  # Query all courses
    return render_template('course_view.html', courses=courses)