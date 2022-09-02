from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
    URLField,
    EmailField,
    PasswordField,
    DateTimeField,
    SelectField,
    BooleanField
)
from wtforms.validators import InputRequired, NumberRange, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import current_app
import json


class PDPtoATCForm(FlaskForm):
    quantity = IntegerField(validators=[InputRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField("Add to Cart")

class EditQuantityATCForm(FlaskForm):
	quantity = IntegerField(validators=[InputRequired(), NumberRange(min=0)])
	submit = SubmitField("Save")

class AddProductForm(FlaskForm):
    product_name = StringField("Product name", validators=[InputRequired(), Length(min=4)])
    cate_report = SelectField(
        "Cate report",
        validate_choice= False,
        validators=[InputRequired()],
        choices=[(cate, cate) for cate in ['Lifestyle', 'ITC', 'Phones - Tablets', 'Home Appliances', 'CG']]
        )
    sub_cate_report = SelectField(
        "Sub cate report",
        validate_choice= False,
        validators=[InputRequired()],
        choices=[(sub_cate ,sub_cate) for sub_cate in ['Sport - Travel', 'Book & Office Supplies', 'Home Living', 'Electronic Accessories', 'Camera', 'IT', 'Phones - Tablets', 'TV', 'Major Domestic Appliance', 'Small Appliances', 'Health - Beauty', 'Mom - Baby', 'FMCG']]
        )
    price = IntegerField("Price vnđ", validators=[InputRequired()])
    brand = StringField("Brand")
    stocks = IntegerField("Stocks", validators=[InputRequired(), NumberRange(min = 10)])    
    img_file = FileField("Product image", validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    listed = SelectField(
        "Listed ?",
        validators=[InputRequired()],
        choices=( (1, "Listed"), (0, "Not listed"))
    )
    submit = SubmitField("Add product")

class EditProductForm(FlaskForm):
    product_name = StringField(
        "Product name", 
        validators=[InputRequired(), Length(min=4)], 
        render_kw={'readonly': True}
        )
    cate_report = SelectField(
        "Cate report",
        validate_choice= False,
        validators=[InputRequired()],
        choices=[(cate, cate) for cate in ['Lifestyle', 'ITC', 'Phones - Tablets', 'Home Appliances', 'CG']], 
        render_kw={'readonly': True}
        )
    sub_cate_report = SelectField(
        "Sub cate report",
        validate_choice= False,
        validators=[InputRequired()],
        choices=[(sub_cate ,sub_cate) for sub_cate in ['Sport - Travel', 'Book & Office Supplies', 'Home Living', 'Electronic Accessories', 'Camera', 'IT', 'Phones - Tablets', 'TV', 'Major Domestic Appliance', 'Small Appliances', 'Health - Beauty', 'Mom - Baby', 'FMCG']], 
        render_kw={'readonly': True}
        )
    price = IntegerField("Price vnđ", validators=[InputRequired()])
    brand = StringField("Brand")
    stocks = IntegerField("Stocks", validators=[InputRequired()])    
    img_file = FileField("Add more image", validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    listed = SelectField(
        "Listed ?",
        validate_choice= False,
        validators=[InputRequired()],
        choices=( (1, "Listed"), (0, "Not listed"))
    )
    submit = SubmitField("Edit product")

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
