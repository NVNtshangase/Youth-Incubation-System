from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import UserMixin

db = SQLAlchemy()

# User Table for Students and Donors
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan', lazy='joined')
    donor = db.relationship('Donor', backref='user', uselist=False, cascade='all, delete-orphan', lazy='joined')


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
    financial_aid = db.relationship('FinancialAid', backref='student', cascade='all, delete-orphan', lazy='joined')
    courses = db.relationship('Course', secondary='take', back_populates='students', lazy='dynamic')


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
    payments = db.relationship('Payment', backref='donor', cascade='all, delete-orphan', lazy='joined')
    certificates = db.relationship('Certificate', backref='donor', cascade='all, delete-orphan', lazy='joined')


# Financial Aid Table
class FinancialAid(db.Model):
    __tablename__ = 'financial_aid'
    financial_aid = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.Integer, db.ForeignKey('student.student_code'),nullable=False)
    donor_code = db.Column(db.Integer, db.ForeignKey('donor.donor_code'), nullable=True)
    application_status = db.Column(db.String(20), nullable=False)
    application_date = db.Column(db.DateTime, nullable=False)

        # Property to get courses related to this financial aid application
    @property
    def courses(self):
        # Get all courses associated with the student via the Take association
        return Course.query.join(Take).filter(Take.student_code == self.student_code).all()


# Course Table
class Course(db.Model):
    __tablename__ = 'course'
    
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    course_description = db.Column(db.String(200), nullable=True)
    course_duration = db.Column(db.String(20), nullable=False)
    course_cost = db.Column(db.Float, nullable=False)
    
    # Relationship for students taking courses
    students = db.relationship('Student', secondary='take', back_populates='courses', lazy='dynamic')


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
