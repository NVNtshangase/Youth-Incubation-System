from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import User, Student, db
from blue_prints.donation import validate_email, validate_name, validate_cellphone_number, validate_password , validate_id_number

application_bp = Blueprint('application', __name__)

@application_bp.route('/apply', methods=['GET', 'POST'])
def application():
    if request.method == 'POST':
        # Process application information
        application_info = request.form
        
        # Validate form data
        if not validate_name(application_info['name']):
            flash("Invalid name. Name should only contain alphabetic characters.", 'error')
            return redirect(url_for('application.application'))
        if not validate_name(application_info['surname']):
            flash("Invalid surname. Surname should only contain alphabetic characters.", 'error')
            return redirect(url_for('application.application'))
        if not validate_email(application_info['email']):
            flash("Invalid email address.", 'error')
            return redirect(url_for('application.application'))
        if not validate_cellphone_number(application_info['phone_number']):
            flash("Invalid phone number. Must be 10 digits.", 'error')
            return redirect(url_for('application.application'))
        if not validate_id_number(application_info['id_number']):
                flash("Invalid ID number. Must be 13 digits and valid.", 'error')
                return redirect(url_for('application.application'))

        password_error = validate_password(application_info['password'])
        if password_error:
            flash(password_error, 'error')
            return redirect(url_for('application.application'))

        if application_info['password'] != application_info['password-confirm']:
            flash("Passwords do not match.", 'error')
            return redirect(url_for('application.application'))

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

        # Create a new user
        new_user = User(
            username=application_info['email'].strip(),
            password=application_info['password'].strip(), ######HASHING###
            role='student'
        )
        # Create a new student application
        new_student = Student(
            student_id_number=application_info['id_number'].strip(),
            student_name=application_info['name'].strip().capitalize(),
            student_surname=application_info['surname'].strip().capitalize(),
            student_date_of_birth=application_info['date_of_birth'],
            student_race=application_info['race'],
            student_nationality=application_info['nationality'],
            student_phone_number=application_info['phone_number'].strip(),
            student_email=application_info['email'].strip(),
            student_physical_address=application_info['physical_address'],
            student_highest_grade=application_info['highest_grade'].strip(),
            student_financial_status=application_info['financial_status'].strip(),
            user_id=new_user.id 
        )


        # Add the new user and student to the session
        db.session.add(new_user)
        db.session.add(new_student)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('application.html')