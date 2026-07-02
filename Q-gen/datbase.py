from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class Quote(db.Model):
    """Quote model - represents a quote in our database"""
    id = db.Column(db.Integer, primary_key=True)
    quote_text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(200), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert quote to dictionary for JSON responses"""
        return {
            'id': self.id,
            'quote_text': self.quote_text,
            'author': self.author,
            'viewed_at': self.viewed_at.strftime('%Y-%m-%d %H:%M:%S')
        }