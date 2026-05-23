import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

database_url = database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if not database_url:
    database_url = 'sqlite:///redsocial.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mi_secreto'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(100), default='default.png')
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    author = db.relationship('User')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
@login_required
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('home.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        foto = request.files['foto']

        usuario_existente = User.query.filter_by(username=username).first()

        if usuario_existente:
            flash('Ese usuario ya existe', 'danger')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        nombre_foto = 'default.png'

        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(ruta)
            nombre_foto = filename

        nuevo_usuario = User(
            username=username,
            password=password_hash,
            profile_pic=nombre_foto
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Cuenta creada correctamente', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/crear_post', methods=['POST'])
@login_required
def crear_post():
    content = request.form['content']

    nuevo_post = Post(content=content, user_id=current_user.id)
    db.session.add(nuevo_post)
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/comentario/<int:post_id>', methods=['POST'])
@login_required
def comentario(post_id):
    content = request.form['content']

    nuevo_comentario = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )

    db.session.add(nuevo_comentario)
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = Post.query.get(post_id)
    post.likes = (post.likes or 0) + 1
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)