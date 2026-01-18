"""
Contact routes - contact form handling.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_mail import Message

from app import mail
from app.forms import ContactForm

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page."""
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            subject=f"F1 ELO Contact Form: {form.subject.data}",
            recipients=[current_app.config.get('MAIL_RECIPIENT')],
            body=f"""
From: {form.name.data} <{form.email.data}>
Subject: {dict(form.subject.choices).get(form.subject.data)}

Message:
{form.message.data}
""",
            reply_to=form.email.data
        )
        try:
            mail.send(msg)
            flash('Thank you for your message! I will get back to you soon.', 'success')
        except Exception as e:
            current_app.logger.error(f"Email error: {str(e)}")
            flash('An error occurred sending your message. Please try again later.', 'danger')
        return redirect(url_for('contact.contact'))
    return render_template('contact.html', form=form)
