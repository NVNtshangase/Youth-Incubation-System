from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import User, Student, Course, FinancialAid, db
from blue_prints.donation import (
    validate_email,
    validate_name,
    validate_cellphone_number,
    validate_password,
    validate_id_number,
)
from datetime import datetime
from werkzeug.security import generate_password_hash  # Importing password hashing function

application_bp = Blueprint('application', __name__)

@application_bp.route('/apply/<int:course_id>', methods=['GET', 'POST'])
def application(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        application_info = request.form  
        # Validate form data (omitted for brevity)
        
        # Create a new user with hashed password
        new_user = User(
            username=application_info['email'].strip(),
            password=generate_password_hash(application_info['password'].strip()),  
            role='student'
        )

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
            user_id=new_user.id 
        )

        new_student.courses.append(course)

        # Create a new financial aid record
        financial_aid = FinancialAid(
            student_code=new_student.student_code,
            application_status='Application Under Review',
        )

        # Append the financial aid record to the student's financial_aid relationship
        new_student.financial_aid.append(financial_aid)

        # Add the new user and student to the session
        db.session.add(new_user)
        db.session.add(new_student)
        db.session.commit()        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('application.html', course=course)

@application_bp.route('/courses', methods=['GET'])
def course_view():
    courses = Course.query.all()  # Query all courses
    return render_template('course_view.html', courses=courses)