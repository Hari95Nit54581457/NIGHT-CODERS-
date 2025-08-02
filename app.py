from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, send_from_directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'o1d2o3o4o5h6a7c8k'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    organization = db.Column(db.String(120))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(150))
    status = db.Column(db.String(20), default='Open')
    attachment = db.Column(db.String(200))
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='tickets')

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    vote_type = db.Column(db.String(10))  

    user = db.relationship('User', backref='votes')
    ticket = db.relationship('Ticket', backref='votes')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            flash('Email already registered.')
            return redirect(url_for('register'))

        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password']),
            role=request.form['role'],
            organization=request.form.get('organization', '')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.role == 'support':
                return redirect(url_for('dashboard_support'))
            else:
                return redirect(url_for('dashboard_user'))
        flash('Invalid credentials')
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard_user():
    page = request.args.get('page', 1, type=int)
    tickets = Ticket.query.order_by(Ticket.id.desc()).paginate(page=page, per_page=5)
    return render_template('dashboard_user.html', tickets=tickets)

@app.route('/create_ticket', methods=['POST'])
@login_required
def create_ticket():
    question = request.form['question']
    description = request.form['description']
    tags = request.form.get('tags', '')
    attachment = request.files.get('attachment')
    filename = None

    if attachment and attachment.filename:
        filename = secure_filename(attachment.filename)
        attachment.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_ticket = Ticket(
        question=question,
        description=description,
        tags=tags,
        attachment=filename,
        user_id=current_user.id
    )
    db.session.add(new_ticket)
    db.session.commit()
    flash('Ticket created.')
    return redirect(url_for('dashboard_user'))

@app.route('/vote/<int:ticket_id>/<string:action>', methods=['POST'])
@login_required
def vote(ticket_id, action):
    if action not in ['up', 'down']:
        return jsonify({'error': 'Invalid vote type'}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    existing_vote = Vote.query.filter_by(user_id=current_user.id, ticket_id=ticket_id).first()

    if existing_vote:
        #  for only one vote
        if existing_vote.vote_type == action:
            if action == 'up':
                ticket.upvotes -= 1
            else:
                ticket.downvotes -= 1
            db.session.delete(existing_vote)
        else:
            
            if action == 'up':
                ticket.upvotes += 1
                ticket.downvotes -= 1
            else:
                ticket.downvotes += 1
                ticket.upvotes -= 1
            existing_vote.vote_type = action
    else:
        
        new_vote = Vote(user_id=current_user.id, ticket_id=ticket_id, vote_type=action)
        db.session.add(new_vote)
        if action == 'up':
            ticket.upvotes += 1
        else:
            ticket.downvotes += 1

    db.session.commit()
    return jsonify({
        'upvotes': ticket.upvotes,
        'downvotes': ticket.downvotes,
        'score': ticket.upvotes - ticket.downvotes
    })

@app.route('/dashboard/support')
@login_required
def dashboard_support():
    if current_user.role != 'support':
        flash("Access denied.")
        return redirect(url_for('dashboard_user'))

    tickets = Ticket.query.order_by(Ticket.id.desc()).all()
    return render_template('dashboard_support.html', tickets=tickets)
@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    if current_user.role != 'support':
        flash("Access denied.")
        return redirect(url_for('dashboard_user'))   

    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('ticket_detail.html', ticket=ticket)
    if request.method == 'POST':
        ticket.reply = request.form['reply']
        ticket.status = request.form['status']
        db.session.commit()
        flash("Reply submitted.")
        return redirect(url_for('dashboard_support'))

    return render_template('ticket_detail.html', ticket=ticket)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    with app.app_context():
        db.create_all()
    app.run(debug=True)
