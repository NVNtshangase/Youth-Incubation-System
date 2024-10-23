from flask import Blueprint, render_template
from models.models import Donor, Payment, Certificate,db
from datetime import datetime

certificate_bp = Blueprint('certificate_bp', __name__)

@certificate_bp.route('/certificate/<int:donor_code>', methods=['GET'])
def view_certificate(donor_code):
    # Fetch donor and payment details
    donor = Donor.query.filter_by(donor_code=donor_code).first()
    payments = Payment.query.filter_by(donor_code=donor_code).order_by(Payment.payment_date.desc()).all()

    # Assuming there is a method to generate the certificate
    certificate = generate_certificate(donor)  # Implement this function below

    return render_template('certificate.html', donor=donor, payments=payments, certificate=certificate)

def generate_certificate(donor):
    # You can customize the certificate details as needed
    certificate = Certificate(
        certificate_name=f"Thank You Certificate for {donor.donor_name} {donor.donor_surname}",
        certificate_date_issued=datetime.now().date(),
        certificate_message="Thank you for your generous donation!",
        certificate_signature="YUI Inc", 
        donor_code=donor.donor_code
    )
    
    db.session.add(certificate)
    db.session.commit()

    return certificate