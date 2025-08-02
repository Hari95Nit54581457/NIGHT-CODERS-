from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(150))
    status = db.Column(db.String(20), default='Open')
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    reply = db.Column(db.Text) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='tickets')


    @property
    def user_name(self):
        return self.user.name

    @property
    def user_org(self):
        return self.user.organization if hasattr(self.user, 'organization') else ""

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    vote_type = db.Column(db.String(10))  # 'up' or 'down'

    user = db.relationship('User', backref='votes')
    ticket = db.relationship('Ticket', backref='votes')
    
class TicketThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    sender_role = db.Column(db.String(10))  # 'user' or 'support'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

    user = db.relationship('User', backref='threads')
    ticket = db.relationship('Ticket', backref='threads')
