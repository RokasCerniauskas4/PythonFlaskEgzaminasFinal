import os

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, current_user, logout_user, login_user, login_required, login_manager, LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dfgsfdgsdfgasd12312321312312sdfgsdf'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'keliones.db?check_same_thread=False')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

db.init_app(app)

bcrypt = Bcrypt(app)


login_manager = LoginManager(app)
login_manager.login_view = 'Log in'
login_manager.login_message_category = 'info'
login_manager.login_message = "Login, to see the content."

association_table = db.Table('association', db.metadata,
    db.Column('keliautojas_id', db.Integer, db.ForeignKey('keliautojas.id')),
    db.Column('grupe_id', db.Integer, db.ForeignKey('grupe.id'))
)


## PRIES NAUDOJANT PASKAITYTI READ ME FAILA

class Client(db.Model, UserMixin):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("Name", db.String, unique=True, nullable=False)
    email = db.Column("Email address", db.String, unique=True, nullable=False)
    password = db.Column("Password", db.String, unique=True, nullable=False)

class Keliautojas(db.Model):
    __tablename__ = 'keliautojas'
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String)
    pavarde = db.Column("Pavardė", db.String)
    # Many2many Rysys su grupemis
    grupes = db.relationship("Grupe", secondary=association_table,
                          back_populates="keliautojai")
    saskaitos = db.relationship("Saskaita")
    userid = db.Column(db.Integer)


class Saskaita(db.Model):
    __tablename__ = 'saskaita'
    id = db.Column(db.Integer, primary_key=True)
    pavadinimas = db.Column("Pavadinimas", db.String)
    suma = db.Column("Suma", db.Integer)
    grupe_id = db.Column(db.Integer, db.ForeignKey("grupe.id"))
    userid = db.Column(db.Integer)
    keliautojas_id = db.Column(db.Integer, db.ForeignKey("keliautojas.id"))
    # Many2one rysys su Grupe
    grupe = db.relationship("Grupe")
    keliautojas = db.relationship('Keliautojas')

    def __str__(self):
        return self.pavadinimas


class Grupe(db.Model): # grupoe
    __tablename__ = 'grupe'
    id = db.Column(db.Integer, primary_key=True)
    pavadinimas = db.Column("Pavadinimas", db.String)
    aprasymas = db.Column("Aprasymas", db.String)
    pavadinimas_ir_aprasymas = db.Column("pavadinimas_ir_aprasymas", db.String)
    userid = db.Column(db.Integer)
    # One2many su saskaita
    saskaitos = db.relationship("Saskaita")
    # Many2many su keliautoju
    keliautojai = db.relationship("Keliautojas", secondary=association_table,
                         back_populates="grupes")

    def __str__(self):
        return self.pavadinimas

class ManoModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.email == "aa"


admin = Admin(app)
admin.add_view(ModelView(Keliautojas, db.session))
admin.add_view(ModelView(Grupe, db.session))
admin.add_view(ModelView(Saskaita, db.session))

@login_manager.user_loader
def load_user(client_id):
    db.create_all()
    return Client.query.get(int(client_id))

with app.app_context():
    import forms
    db.create_all()

@app.route("/register", methods=['GET', 'POST'])
def register():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Client(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Successfully registered! You can Log In now!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

@app.route("/sign_in", methods=['GET','POST'])
def sign_in():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.SignInForm()
    if form.validate_on_submit():
        user = Client.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Sign In Failed! Check email or password', 'danger')
    return render_template('sign_in.html', title='Sign In', form=form)

@app.route("/log_out")
def log_out():
    logout_user()
    return redirect(url_for('index'))


@app.route("/")
def index():
    return render_template('welcome.html')


@app.route("/grupes")
def grupes():
    try:
        grupes = Grupe.query.filter_by(userid=current_user.id)
    except:
        grupes = []
    return render_template("grupes.html", grupes=grupes)


@app.route("/nauja_grupe", methods=["GET", "POST"])
def nauja_grupe():
    db.create_all()
    forma = forms.GrupeForm()
    forma.keliautojai.query = Keliautojas.query.filter_by(userid=current_user.id)
    if forma.validate_on_submit():
        nauja_grupe = Grupe(pavadinimas=forma.pavadinimas.data, aprasymas=forma.aprasymas.data, pavadinimas_ir_aprasymas=f"{forma.pavadinimas.data} {forma.aprasymas.data}", userid=current_user.id)
        for keliautojas in forma.keliautojai.data:
            priskirtas_keliautojas = Keliautojas.query.get(keliautojas.id)
            nauja_grupe.keliautojai.append(priskirtas_keliautojas)
        db.session.add(nauja_grupe)
        db.session.commit()
        return redirect(url_for('grupes'))
    return render_template("prideti_grupe.html", form=forma)

@app.route("/istrinti_grupe/<int:id>")
def istrinti_grupe(id):
    uzklausa = Grupe.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for('grupes'))



@app.route("/keliautojai")
def keliautojai():
    try:
        visi_keliautojai = Keliautojas.query.filter_by(userid=current_user.id)
    except:
        visi_keliautojai = []
    return render_template("keliautojai.html", visi_keliautojai=visi_keliautojai)


@app.route("/naujas_keliautojas", methods=["GET", "POST"])
def naujas_keliautojas():
    db.create_all()
    forma = forms.KeliautojasForm()
    forma.grupes.query = Grupe.query.filter_by(userid=current_user.id)
    if forma.validate_on_submit():
        naujas_keliautojas = Keliautojas(vardas=forma.vardas.data,
                               pavarde=forma.pavarde.data, userid=current_user.id)
        for grupe in forma.grupes.data:
            priskirta_grupe = Grupe.query.get(grupe.id)
            naujas_keliautojas.grupes.append(priskirta_grupe)
        db.session.add(naujas_keliautojas)
        db.session.commit()
        return redirect(url_for('keliautojai'))
    return render_template("prideti_keliautoja.html", form=forma)

@app.route("/istrinti_keliautoja/<int:id>")
def istrinti_keliautoja(id):
    uzklausa = Keliautojas.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for('keliautojai'))





@app.route("/grupes/<int:id>/prideti_saskaita", methods=["GET", "POST"])
def prideti_saskaita(id):
    db.create_all()
    forma = forms.SaskaitaForm()
    forma.keliautojas.query = Keliautojas.query.filter_by(userid=current_user.id)
    if forma.validate_on_submit():
        nauja_saskaita = Saskaita(pavadinimas=forma.pavadinimas.data, suma=forma.suma.data, keliautojas_id=forma.keliautojas.data.id,userid=current_user.id,grupe_id=id)
        db.session.add(nauja_saskaita)
        db.session.commit()
        return redirect(url_for('grupes_saskaitos', id=id))
    return render_template("prideti_saskaita.html", form=forma)


@app.route("/grupes/<int:id>/saskaitos")
def grupes_saskaitos(id):
        try:
            visos_saskaitos = Saskaita.query.filter_by(grupe_id=id)
        except:
            visos_saskaitos = []
        return render_template("saskaitos.html", visos_saskaitos=visos_saskaitos)



@app.route("/grupes/<int:grupe_id>/istrinti_saskaita/<int:id>")
def istrinti_saskaita(grupe_id, id):
    uzklausa = Saskaita.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for('grupes_saskaitos', id=grupe_id))



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
    db.create_all()