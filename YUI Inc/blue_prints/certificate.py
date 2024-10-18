from flask import Blueprint, render_template, request, send_file
from models.models import Donor, db
import io
from fpdf import FPDF

certificate_bp = Blueprint('certificate', __name__)

@certificate_bp.route('/generate_certificate/<int:donor_id>')
def generate_certificate(donor_id):
    # Fetch donor information
    donor = Donor.query.get(donor_id)
    
    if not donor:
        return "Donor not found", 404
    
    # Create a PDF certificate
    pdf = FPDF()
    pdf.add_page()
    
    # Set font for the certificate
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 10, 'Certificate of Donation', ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(20)  # Line break
    
    # Add donor details
    pdf.cell(0, 10, f"This is to certify that:", ln=True, align='C')
    pdf.ln(10)  # Line break
    pdf.cell(0, 10, f"{donor.donor_name} {donor.donor_surname}", ln=True, align='C')
    pdf.cell(0, 10, f"ID Number: {donor.donor_id_number}", ln=True, align='C')
    
    pdf.ln(20)  # Line break
    pdf.cell(0, 10, "has made a generous donation.", ln=True, align='C')
    
    pdf.ln(10)  # Line break
    pdf.cell(0, 10, "Thank you for your support!", ln=True, align='C')
    
    # Save the PDF to a bytes buffer
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    # Send the PDF file as a response
    return send_file(buffer, as_attachment=True, download_name='certificate.pdf', mimetype='application/pdf')
