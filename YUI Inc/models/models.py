from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User Table for Students and Donors
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    password_reset_token = db.Column(db.String(128), nullable=True)
    role = db.Column(db.String(10), nullable=False)  # role will distinguish between 'student' and 'donor'

    student = db.relationship('Student', backref='user', uselist=False)
    donor = db.relationship('Donor', backref='user', uselist=False)


# Student Table
class Student(db.Model):
    __tablename__ = 'student'
    
    student_code = db.Column(db.Integer, primary_key=True)
    student_id_number = db.Column(db.String(20), nullable=False, unique=True)
    student_name = db.Column(db.String(50), nullable=False)
    student_surname = db.Column(db.String(50), nullable=False)
    student_date_of_birth = db.Column(db.Date, nullable=False)
    student_race = db.Column(db.String(20), nullable=True)
    student_nationality = db.Column(db.String(50), nullable=False)
    student_phone_number = db.Column(db.String(20), nullable=True)
    student_email = db.Column(db.String(50), nullable=False)
    student_physical_address = db.Column(db.String(100), nullable=True)
    student_highest_grade = db.Column(db.String(20), nullable=True)
    student_financial_status = db.Column(db.String(20), nullable=True)

    # Foreign Key for Course
    course_code = db.Column(db.Integer, db.ForeignKey('course.course_id'))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key to User

    # Relationship
    financial_aid = db.relationship('FinancialAid', backref='student')
    courses = db.relationship('Course', secondary='take', back_populates='students')


# Donor Table
class Donor(db.Model):
    __tablename__ = 'donor'

    donor_code = db.Column(db.Integer, primary_key=True)
    donor_id_number = db.Column(db.String(20), nullable=False, unique=True)
    donor_name = db.Column(db.String(50), nullable=False)
    donor_surname = db.Column(db.String(50), nullable=False)
    donor_email = db.Column(db.String(50), nullable=False)
    donor_phone_number = db.Column(db.String(20), nullable=True)
    donor_organization = db.Column(db.String(100), nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key to User

    # Relationships
    payments = db.relationship('Payment', backref='donor')
    certificates = db.relationship('Certificate', backref='donor')


# Financial Aid Table
class FinancialAid(db.Model):
    __tablename__ = 'financial_aid'

    student_code = db.Column(db.Integer, db.ForeignKey('student.student_code'), primary_key=True)
    donor_code = db.Column(db.Integer, db.ForeignKey('donor.donor_code'), primary_key=True)
    application_status = db.Column(db.String(20), nullable=False)
    application_date = db.Column(db.Date, nullable=False)


# Course Table
class Course(db.Model):
    __tablename__ = 'course'
    
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    course_description = db.Column(db.String(200), nullable=True)
    course_duration = db.Column(db.String(20), nullable=False)
    course_cost = db.Column(db.Float, nullable=False)
    
    # Relationship for students taking courses
    students = db.relationship('Student', secondary='take', back_populates='courses')


# Association Table between Student and Course
class Take(db.Model):
    __tablename__ = 'take'
    
    student_code = db.Column(db.Integer, db.ForeignKey('student.student_code'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), primary_key=True)


# Payment Table
class Payment(db.Model):
    __tablename__ = 'payment'
    
    payment_id = db.Column(db.Integer, primary_key=True)
    payment_amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

    donor_code = db.Column(db.Integer, db.ForeignKey('donor.donor_code'))  # FK to Donor


# Certificate Table
class Certificate(db.Model):
    __tablename__ = 'certificate'

    certificate_id = db.Column(db.Integer, primary_key=True)
    certificate_name = db.Column(db.String(100), nullable=False)
    certificate_date_issued = db.Column(db.Date, nullable=False)
    certificate_message = db.Column(db.String(255), nullable=True)
    certificate_signature = db.Column(db.String(100), nullable=False)

    donor_code = db.Column(db.Integer, db.ForeignKey('donor.donor_code'))  # FK to Donor
