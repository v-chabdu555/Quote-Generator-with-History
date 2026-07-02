from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import random
import os

# ============================================
# DATABASE SETUP
# ============================================

db = SQLAlchemy()

class Quote(db.Model):
    """Quote model for storing quote history"""
    id = db.Column(db.Integer, primary_key=True)
    quote_text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(200), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Quote "{self.quote_text[:50]}...">'
    
    def to_dict(self):
        """Convert quote to dictionary for JSON responses"""
        return {
            'id': self.id,
            'quote_text': self.quote_text,
            'author': self.author,
            'viewed_at': self.viewed_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# ============================================
# FLASK APP INITIALIZATION
# ============================================

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# ============================================
# FALLBACK QUOTES (in case API fails)
# ============================================

FALLBACK_QUOTES = [
    {"content": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"content": "Innovation distinguishes between a leader and a follower.", "author": "Steve Jobs"},
    {"content": "Stay hungry, stay foolish.", "author": "Steve Jobs"},
    {"content": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
    {"content": "The purpose of our lives is to be happy.", "author": "Dalai Lama"},
    {"content": "Get busy living or get busy dying.", "author": "Stephen King"},
    {"content": "You only live once, but if you do it right, once is enough.", "author": "Mae West"},
    {"content": "Live as if you were to die tomorrow. Learn as if you were to live forever.", "author": "Mahatma Gandhi"},
    {"content": "Darkness cannot drive out darkness: only light can do that.", "author": "Martin Luther King Jr."},
    {"content": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
    {"content": "Be yourself; everyone else is already taken.", "author": "Oscar Wilde"},
    {"content": "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.", "author": "Albert Einstein"},
    {"content": "So many books, so little time.", "author": "Frank Zappa"},
    {"content": "Be who you are and say what you feel, because those who mind don't matter and those who matter don't mind.", "author": "Dr. Seuss"},
    {"content": "You only live once, but if you do it right, once is enough.", "author": "Mae West"}
]

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/quotes/random', methods=['GET'])
def get_random_quote():
    """
    Fetch a random quote from external API.
    If API fails, return a fallback quote.
    """
    try:
        # Try primary API (Quotable)
        print("Attempting to fetch from Quotable API...")
        response = requests.get('https://api.quotable.io/random', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quote_data = {
                'content': data.get('content', ''),
                'author': data.get('author', 'Unknown')
            }
            print(f"Successfully fetched from Quotable: {quote_data['content'][:50]}...")
        else:
            # Fallback to secondary API (ZenQuotes)
            print("Quotable API failed, trying ZenQuotes...")
            response = requests.get('https://zenquotes.io/api/random', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                quote_data = {
                    'content': data[0].get('q', ''),
                    'author': data[0].get('a', 'Unknown')
                }
                print(f"Successfully fetched from ZenQuotes: {quote_data['content'][:50]}...")
            else:
                # Use fallback quotes
                print("All APIs failed, using fallback quotes...")
                quote_data = random.choice(FALLBACK_QUOTES)
        
        # Save quote to database
        new_quote = Quote(
            quote_text=quote_data['content'],
            author=quote_data['author']
        )
        db.session.add(new_quote)
        db.session.commit()
        print(f"Saved quote to database (ID: {new_quote.id})")
        
        # Return JSON response
        return jsonify({
            'success': True,
            'quote': quote_data['content'],
            'author': quote_data['author'],
            'id': new_quote.id,
            'viewed_at': new_quote.viewed_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except requests.exceptions.Timeout:
        print("API request timed out, using fallback quote...")
        return get_fallback_quote()
        
    except requests.exceptions.ConnectionError:
        print("Network error, using fallback quote...")
        return get_fallback_quote()
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return get_fallback_quote()

def get_fallback_quote():
    """Helper function to return a fallback quote"""
    try:
        quote_data = random.choice(FALLBACK_QUOTES)
        
        # Save to database
        new_quote = Quote(
            quote_text=quote_data['content'],
            author=quote_data['author']
        )
        db.session.add(new_quote)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quote': quote_data['content'],
            'author': quote_data['author'],
            'id': new_quote.id,
            'viewed_at': new_quote.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'fallback'
        })
    except Exception as e:
        print(f"Error in fallback: {e}")
        # Ultimate fallback - return a hardcoded quote without database save
        return jsonify({
            'success': True,
            'quote': "The only way to do great work is to love what you do.",
            'author': "Steve Jobs",
            'id': 0,
            'viewed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/quotes/history', methods=['GET'])
def get_quote_history():
    """Retrieve all previously viewed quotes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        quotes = Quote.query.order_by(Quote.viewed_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'history': [quote.to_dict() for quote in quotes],
            'count': len(quotes)
        })
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quotes/history/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    """Delete a specific quote from history"""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({
                'success': False,
                'error': 'Quote not found'
            }), 404
            
        db.session.delete(quote)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quote deleted successfully',
            'id': quote_id
        })
    except Exception as e:
        print(f"Error deleting quote: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quotes/history/clear', methods=['DELETE'])
def clear_history():
    """Clear all quote history"""
    try:
        count = Quote.query.count()
        db.session.query(Quote).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'History cleared successfully',
            'deleted_count': count
        })
    except Exception as e:
        print(f"Error clearing history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quotes/stats', methods=['GET'])
def get_stats():
    """Get statistics about quotes"""
    try:
        total_quotes = Quote.query.count()
        
        # Get most viewed author
        from sqlalchemy import func
        top_author = db.session.query(
            Quote.author, 
            func.count(Quote.author).label('count')
        ).group_by(Quote.author).order_by(func.count(Quote.author).desc()).first()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_quotes': total_quotes,
                'top_author': top_author[0] if top_author else 'None',
                'top_author_count': top_author[1] if top_author else 0
            }
        })
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ============================================
# RUN THE APPLICATION
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Random Quote Generator")
    print("=" * 50)
    print(f"📁 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🌐 Server running at: http://localhost:5000")
    print("📝 Press CTRL+C to stop")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)