import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.models import Certificate, Payment, User, Donor, db
from werkzeug.security import generate_password_hash
import phonenumbers
import os
from dotenv import load_dotenv
import requests
from flask_login import current_user, login_required

# Load environment variables
load_dotenv()

# Paystack credentials
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_BASE_URL = 'https://api.paystack.co'
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
                existing_user = db.session.get(User, donor_info['email'])
                if existing_user:
                    flash("Email already registered. Please log in instead.", 'error')
                    return redirect(url_for('home'))

                # Check if the ID number already exists
                existing_donor = db.session.get(Donor, donor_info['id_number'])
                if existing_donor:
                    flash("A profile with this ID number already exists. Please log in or contact support.", 'error')
                    return redirect(url_for('home'))

                # Check if the cellphone number already exists
                existing_donor_cell = db.session.get(Donor, donor_info['full_phone_number'])
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

                return redirect(url_for('donation.pay'))

        except Exception as e:
            print(f"Error: {e}")
            flash("An error occurred while processing your request. Please try again later.", 'error')
            return render_template('donation.html', donor_info=donor_info)

    return render_template('donation.html', donor_info=donor_info)

@donation_bp.route('/pay')
@login_required
def pay():
    donor = db.session.get(Donor, current_user.id)
 
    if not donor:
        flash('Donor not found.', 'error')
        return redirect(url_for('home'))

    return render_template('pay.html', 
                            donor_name=donor.donor_name, 
                            donor_surname=donor.donor_surname,
                            email=donor.donor_email)

@donation_bp.route('/donor/history', methods=['GET'])
@login_required
def donor_donation_history():
    # Fetch payments related to the current donor
    payments = Payment.query.filter_by(donor_code=current_user.donor.donor_code).all()  # Correctly access donor_code
    return render_template('donation_history.html', payments=payments)

@donation_bp.route('/initialize-payment', methods=['POST'])
def initialize_payment():
    # Retrieve form data
    amount = request.form.get('amount')
    email = request.form.get('email')
    donor_name = request.form.get('donor_name')  # Get donor first name
    donor_surname = request.form.get('donor_surname')  # Get donor last name

    # Validate the input data
    if not amount or not email or not donor_name or not donor_surname:
        flash('Please provide all required details.', 'error')
        return redirect(url_for('donation.donate'))

    try:
        # Combine first name and surname into full name
        full_name = f"{donor_name} {donor_surname}"

        amount_in_kobo = int(amount) * 100  # Convert amount to kobo (for Paystack)
        initialize_url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
        
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        # Fetch the donor object based on the current user
        donor = Donor.query.filter_by(user_id=current_user.id).first()

        # Check if donor exists
        if not donor:
            flash('Donor not found.', 'error')
            return redirect(url_for('donation.donate'))

        # Prepare the data for Paystack request
        data = {
            'email': email,
            'amount': amount_in_kobo,
            'callback_url': 'https://effective-dollop-g4rq5wrxwp727w4-5000.app.github.dev/verify-payment',
            'metadata': {
                'donor_full_name': full_name,
                'donor_code': donor.donor_code  # Use the donor instance to access donor_code
            }
        }

        # Send request to Paystack API to initialize payment
        response = requests.post(initialize_url, json=data, headers=headers)
        response_data = response.json()

        # Log the Paystack API response for debugging
        print("Paystack API Response:", response_data)

        if response.status_code == 200 and response_data['status']:
            payment_url = response_data['data']['authorization_url']
            return redirect(payment_url)
        else:
            error_message = response_data.get('message', 'Unknown error')
            print("Paystack initialization error:", error_message)
            flash(f'Failed to initialize payment: {error_message}', 'error')
            return redirect(url_for('dashboard'))

    except Exception as e:
        print("An error occurred during payment initialization:", str(e))
        flash('An unexpected error occurred. Please try again later.', 'error')
        return redirect(url_for('dashboard'))

@donation_bp.route('/verify-payment', methods=['GET'])
def verify_payment():
    reference = request.args.get('reference')

    if not reference:
        flash('Payment reference missing. Unable to verify payment.', 'error')
        return redirect(url_for('dashboard'))

    verify_payment_url = f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}'
    
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.get(verify_payment_url, headers=headers)
    response_data = response.json()

    if response.status_code == 200 and response_data['status']:
        data = response_data['data']
        if data['status'] == 'success':
            amount = data['amount'] / 100  # Convert kobo to original amount
            donor_code = data['metadata'].get('donor_code')  

            new_payment = Payment(
                payment_amount=amount,
                donor_code=donor_code
            ) 

            db.session.add(new_payment)
            db.session.commit()
            
            donor = Donor.query.filter_by(donor_code=donor_code).first()

            # Check if donor exists and has an email
            if donor and donor.donor_email:
                # Send the email notification
                send_notification(donor)
            else:
                print("Donor not found or email is missing.")
            

            # Make sure to pass the donor_code to the URL
            return redirect(url_for('certificate_bp.view_certificate', donor_code=donor_code)) 

        else:
            flash('Payment verification failed. Please try again.', 'error')
    else:
        error_message = response_data.get('message', 'Payment verification failed.')
        print("Paystack error:", error_message)
        flash(f'Payment verification failed: {error_message}', 'error')

    return redirect(url_for('dashboard'))

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
S_K_P = os.getenv('S_K_P')
from sendgrid.helpers.mail import Attachment
import base64

def send_notification(donor):
    try:
        # Fetch the latest payment for a donor
        payment = Payment.query.filter_by(donor_code=donor.donor_code).order_by(Payment.payment_id.desc()).first()

        if payment is None:
            print("No payment found for donor:", donor.donor_code)
            return  # Exit if no payment found

        certificate = Certificate.query.filter_by(donor_code=donor.donor_code).first()
        
        if certificate is None:
            print("No certificate found for donor:", donor.donor_code)
            return  # Exit if no certificate found

        # Generate the PDF certificate
        pdf_path = generate_certificate(donor, payment, certificate)

        # Read the PDF file for attachment
        with open(pdf_path, "rb") as f:
            data = f.read()
            encoded_file = base64.b64encode(data).decode()
            attachment = Attachment(
                file_content=encoded_file,
                file_type='application/pdf',
                file_name='certificate.pdf',
                disposition='attachment'
            )

        message = Mail(
            from_email='ntandoyenkosivezokuhle360@gmail.com', 
            to_emails=donor.donor_email,
            subject='Thank You for Your Donation!',
            html_content=f'''
                <h1>Dear {donor.donor_name},</h1>
                <p>Thank you for your generous donation!</p>
                <p>Your donation has been successfully processed.</p>
                <p>Please find your certificate attached.</p>
                <p>Warm regards,<br>YUI Inc.</p>
            '''
        )
        message.attachment = attachment

        sg = SendGridAPIClient(S_K_P)
        sg.send(message)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")


from flask import render_template
from weasyprint import HTML

def generate_certificate(donor, payment, certificate):
    # Ensure the certificates directory exists
    if not os.path.exists('certificates'):
        os.makedirs('certificates')
    
    # Render the HTML template
    rendered_html = render_template(
        'certificate_template.html',  # Make sure this file exists
        donor=donor,
        payments=[payment],  # Pass the payment data
        certificate=certificate
    )

    # Create the PDF from the rendered HTML
    pdf = HTML(string=rendered_html).write_pdf()

    # Save the PDF to a file
    pdf_path = f"certificates/{donor.donor_code}_certificate.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(pdf)

    return pdf_path
