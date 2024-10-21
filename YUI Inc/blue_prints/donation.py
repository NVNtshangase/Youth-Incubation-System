import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.models import User, Donor, db
from werkzeug.security import generate_password_hash
import phonenumbers

donation_bp = Blueprint('donation', __name__)

# Luhn algorithm to validate ID number
def validate_id_number(id_number):
    if len(id_number) != 13 or not id_number.isdigit():
        return False
    total = 0
    for i, digit in enumerate(id_number):
        num = int(digit)
        if i % 2 == 1:
            num *= 2
            if num > 9:
                num -= 9
        total += num
    return total % 10 == 0

# Function to validate phone number (international format)
def validate_cellphone_number(phone_number):
    try:
        # The phone_number should include the country code, e.g., +1234567890
        parsed_number = phonenumbers.parse(phone_number, None) 
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False

# Password complexity check
def validate_password(password):
    if len(password) < 6:
        return "Password must be at least 6 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None

# Email validation
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))

# Name validation (should not contain numbers)
def validate_name(name):
    return name.isalpha()

@donation_bp.route('/donate', methods=['GET', 'POST'])
def donate():
    donor_info = {}

    if request.method == 'POST':
        donor_info = request.form.to_dict()  # Convert form data to a dictionary

        try:
            if 'id_number' in donor_info:  # Profile creation step
                # Validate form data
                if not validate_name(donor_info['name']):
                    flash("Invalid name. Name should only contain alphabetic characters.", 'error')
                    return render_template('donation.html', donor_info=donor_info)

                if not validate_name(donor_info['surname']):
                    flash("Invalid surname. Surname should only contain alphabetic characters.", 'error')
                    return render_template('donation.html', donor_info=donor_info)

                if not validate_email(donor_info['email']):
                    flash("Invalid email address.", 'error')
                    return render_template('donation.html', donor_info=donor_info)

                if not validate_id_number(donor_info['id_number']):
                    flash("Invalid ID number. Must be 13 digits and valid.", 'error')
                    return render_template('donation.html', donor_info=donor_info)

                if not validate_cellphone_number(donor_info['full_phone_number']):
                    flash('Invalid phone number format.', 'error')
                    return render_template('donation.html', donor_info=donor_info)

                password_error = validate_password(donor_info['password'])
                if password_error:
                    flash(password_error, 'error')
                    return render_template('donation.html', donor_info=donor_info)

                if donor_info['password'] != donor_info['password-confirm']:
                    flash("Passwords do not match.", 'error')
                    return render_template('donation.html', donor_info=donor_info)

                # Check if the email already exists
                existing_user = User.query.filter_by(username=donor_info['email']).first()
                if existing_user:
                    flash("Email already registered. Please log in instead.", 'error')
                    return redirect(url_for('home'))

                # Check if the ID number already exists
                existing_donor = Donor.query.filter_by(donor_id_number=donor_info['id_number']).first()
                if existing_donor:
                    flash("A profile with this ID number already exists. Please log in or contact support.", 'error')
                    return redirect(url_for('home'))

                # Check if the cellphone number already exists
                existing_donor_cell = Donor.query.filter_by(donor_phone_number=donor_info['full_phone_number']).first()
                if existing_donor_cell:
                    flash("A profile with this cellphone number already exists. Please log in or contact support.", 'error')
                    return redirect(url_for('home'))

                # Create user
                new_user = User(
                    username=donor_info['email'].strip(),
                    password=generate_password_hash(donor_info['password'].strip()),
                    role='donor'
                )
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id

                # Capitalize first name and surname, strip spaces
                new_donor = Donor(
                    donor_id_number=donor_info['id_number'].strip(),
                    donor_name=donor_info['name'].strip().capitalize(),
                    donor_surname=donor_info['surname'].strip().capitalize(),
                    donor_email=donor_info['email'].strip(),
                    donor_phone_number=donor_info['full_phone_number'].strip(),  # Use the full international format
                    donor_organization=donor_info['organisation'],
                    user_id=new_user.id
                )
                db.session.add(new_donor)
                db.session.commit()

                session['donor_id'] = new_donor.donor_code
                flash('Profile created successfully', 'success')

                # Redirect to the home page after profile creation
                return redirect(url_for('payment'))

        except Exception as e:
            flash("An error occurred while processing your request. Please try again later.", 'error')
            return render_template('donation.html', donor_info=donor_info)

    return render_template('donation.html', donor_info=donor_info)