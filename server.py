from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import uuid
import logging
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///analytics.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(200), nullable=False)
    visitor_id = db.Column(db.String(36), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    referrer = db.Column(db.String(200), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.Text, nullable=True)
    visitor_id = db.Column(db.String(36), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    page_url = db.Column(db.String(200), nullable=True)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/analytics/pageviews')
@login_required
def pageviews_data():
    days = int(request.args.get('days', 7))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get pageviews per day
    views = PageView.query.filter(PageView.timestamp.between(start_date, end_date)).all()
    
    # Process data
    daily_views = {}
    for view in views:
        day = view.timestamp.strftime('%Y-%m-%d')
        if day not in daily_views:
            daily_views[day] = 0
        daily_views[day] += 1
    
    # Format data for chart
    dates = []
    counts = []
    
    for i in range(days):
        date = (end_date - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        dates.append(date)
        counts.append(daily_views.get(date, 0))
    
    return jsonify({
        'labels': dates,
        'data': counts
    })

@app.route('/analytics/popular-pages')
@login_required
def popular_pages():
    days = int(request.args.get('days', 7))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get popular pages
    pages = db.session.query(
        PageView.page_url,
        db.func.count(PageView.id).label('view_count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(
        PageView.page_url
    ).order_by(
        db.func.count(PageView.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'pages': [{'url': page.page_url, 'views': page.view_count} for page in pages]
    })

@app.route('/analytics/events')
@login_required
def events_data():
    days = int(request.args.get('days', 7))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get events by type
    events = db.session.query(
        Event.event_type,
        db.func.count(Event.id).label('event_count')
    ).filter(
        Event.timestamp.between(start_date, end_date)
    ).group_by(
        Event.event_type
    ).order_by(
        db.func.count(Event.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'events': [{'type': event.event_type, 'count': event.event_count} for event in events]
    })

@app.route('/analytics/visitors')
@login_required
def visitors_data():
    days = int(request.args.get('days', 7))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get unique visitors per day
    visitors = db.session.query(
        db.func.date(PageView.timestamp).label('date'),
        db.func.count(db.func.distinct(PageView.visitor_id)).label('visitor_count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(
        db.func.date(PageView.timestamp)
    ).all()
    
    # Process data
    daily_visitors = {str(v.date): v.visitor_count for v in visitors}
    
    # Format data for chart
    dates = []
    counts = []
    
    for i in range(days):
        date = (end_date - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        dates.append(date)
        counts.append(daily_visitors.get(date, 0))
    
    return jsonify({
        'labels': dates,
        'data': counts
    })

@app.route('/analytics/collect', methods=['POST'])
def collect_data():
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'type' not in data or 'visitorId' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if data['type'] == 'pageview':
            page_view = PageView(
                page_url=data.get('pageUrl', ''),
                visitor_id=data.get('visitorId', ''),
                referrer=data.get('referrer', ''),
                user_agent=request.headers.get('User-Agent', ''),
                ip_address=request.remote_addr
            )
            db.session.add(page_view)
            
        elif data['type'] == 'event':
            event = Event(
                event_type=data.get('eventType', ''),
                event_data=json.dumps(data.get('eventData', {})),
                visitor_id=data.get('visitorId', ''),
                page_url=data.get('pageUrl', '')
            )
            db.session.add(event)
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error collecting analytics data: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')

@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.all()
    return jsonify({
        'users': [{'id': user.id, 'username': user.username, 'is_admin': user.is_admin} for user in users]
    })

@app.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    data = request.json
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=data['username'],
        is_admin=data.get('is_admin', False)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'id': user.id})

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent deleting your own account
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/track.js')
def tracking_script():
    return """
    // Analytics Tracking Script
    (function() {
        // Generate visitor ID or use existing one
        let visitorId = localStorage.getItem('analyticsVisitorId');
        if (!visitorId) {
            visitorId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
            localStorage.setItem('analyticsVisitorId', visitorId);
        }
        
        // Track page view
        fetch('/analytics/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: 'pageview',
                pageUrl: window.location.href,
                referrer: document.referrer,
                visitorId: visitorId
            }),
            keepalive: true
        }).catch(console.error);
        
        // Helper function to track events
        window.trackEvent = function(eventType, eventData) {
            fetch('/analytics/collect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'event',
                    eventType: eventType,
                    eventData: eventData,
                    pageUrl: window.location.href,
                    visitorId: visitorId
                }),
                keepalive: true
            }).catch(console.error);
        };
    })();
    """

# Initialize database tables
@app.cli.command("init-db")
def init_db_command():
    """Create database tables and add admin user."""
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')  # Change in production!
        db.session.add(admin)
        db.session.commit()
        print("Admin user created with username 'admin' and password 'admin'")
    
    print("Database initialized!")

if __name__ == '__main__':
    # Create all tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')  # Change in production!
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with username 'admin' and password 'admin'")
    
    app.run(debug=True)
