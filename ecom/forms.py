from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
    URLField,
    EmailField,
    PasswordField,
    DateTimeField
)
from wtforms.validators import InputRequired, NumberRange, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import current_app


class PDPtoATCForm(FlaskForm):
    quantity = IntegerField(validators=[InputRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField("Add to Cart")

class EditQuantityATCForm(FlaskForm):
	quantity = IntegerField(validators=[InputRequired(), NumberRange(min=0)])
	submit = SubmitField("Save")

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[
        InputRequired(),
        Length(min=4)
    ])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[
        InputRequired(),
        Length(min=4)
    ])
    confirm_password = PasswordField("Confirm password", validators=[
        InputRequired(),
        EqualTo("password")
    ])
    submit = SubmitField("Register")
