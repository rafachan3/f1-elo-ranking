from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message="Name must be between 2 and 50 characters")
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    
    subject = SelectField('Subject', validators=[DataRequired()], choices=[
        ('general', 'General Question about F1 ELO Rankings'),
        ('methodology', 'Question about ELO Calculation Methodology'),
        ('suggestion', 'Feature Suggestion'),
        ('data', 'Historical F1 Data Question'),
        ('bug', 'Bug Report'),
        ('contribute', 'Interest in Contributing'),
        ('other', 'Other')
    ])
    
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=1000, message="Message must be between 10 and 1000 characters")
    ])

    submit = SubmitField('Submit', render_kw={'class': 'btn btn-danger'})