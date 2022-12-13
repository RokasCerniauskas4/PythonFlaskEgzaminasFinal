from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
import main
from flask_login import current_user

def keliautojas_query():
    return main.Keliautojas.query

class KeliautojasForm(FlaskForm):
    vardas = StringField('Vardas', [DataRequired()])
    pavarde = StringField('Pavardė', [DataRequired()])
    grupes = QuerySelectMultipleField(get_label="pavadinimas", get_pk=lambda obj: str(obj))
    submit = SubmitField('Įvesti')

class SaskaitaForm(FlaskForm):
    pavadinimas = StringField('Pavadinimas', [DataRequired()])
    suma = IntegerField('Suma', [DataRequired()])
    keliautojas = QuerySelectField(get_label="vardas", get_pk=lambda obj: str(obj))
    submit = SubmitField('Įvesti')


class GrupeForm(FlaskForm):
    pavadinimas = StringField('Pavadinimas', [DataRequired()])
    aprasymas = StringField('Aprasymas', [DataRequired()])
    keliautojai = QuerySelectMultipleField(get_label="vardas", get_pk=lambda obj: str(obj))
    submit = SubmitField('Įvesti')

class RegisterForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    email = StringField('Email address', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    valid_password = PasswordField("Re-enter your password", [EqualTo('password', "Password must match.")])
    submit = SubmitField('Register')

    def check_name(self, name):
        client = main.Client.query.filter_by(name=name.data).first()
        if client:
            raise ValidationError('This name is already in use! Create new one')

    def check_email(self, email):
        client = main.Client.query.filter_by(email=email.data).first()
        if client:
            raise ValidationError('This email is already in use! Create new one')

class SignInForm(FlaskForm):
    email = StringField('Email address', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField('Sign In')