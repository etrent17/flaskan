# Flask Analytics Dashboard

A self-hosted analytics dashboard built with Flask. Track pageviews, events, and visitor metrics across your websites.

---

## 📁 Project Structure

```
/your_project/
├── app.py                 # Main Flask application file
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── static/                # Static files
│   ├── css/
│   │   └── custom.css     # Optional custom styles
│   └── js/
│       └── dashboard.js   # Optional JS for dashboard
├── templates/             # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   └── admin.html
└── instance/              # Instance-specific files
    └── analytics.db       # SQLite database (created automatically)
```

---

## 📦 Requirements

```
Flask==2.3.3
Flask-SQLAlchemy==3.1.1
Werkzeug==2.3.7
gunicorn==21.2.0
```

---

## 🚀 Features

- **User Authentication**: Secure login system with admin and regular users
- **Dashboard**: Visualize pageviews and visitor trends
- **Event Tracking**: Track custom events from your websites
- **User Management**: Add and remove dashboard users (admin only)
- **Self-hosted**: Keep your analytics data private and under your control

---

## 🛠 Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd flask-analytics-dashboard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   flask init-db
   ```

5. Run the application:
   ```bash
   flask run
   ```

6. Access the dashboard at: [http://localhost:5000](http://localhost:5000)

---

## 🚚 Deployment

For production deployment, set these environment variables:

- `SECRET_KEY`: A secure random string for session encryption  
- `DATABASE_URL`: Database connection URL (defaults to SQLite)

Example with Gunicorn:
```bash
SECRET_KEY=your_secure_key gunicorn -w 4 app:app
```

---

## 📊 Usage

### 🔧 Tracking Code

Add this script to your website:

```html
<script src="https://your-dashboard-domain.com/track.js"></script>
```

### 🎯 Tracking Events

```javascript
// Track custom events
trackEvent('button_click', { buttonId: 'signup', page: 'homepage' });
```

---

## 🔐 Default Login

- Username: `admin`  
- Password: `admin`  

> **Important**: Change the default admin password immediately after first login.

---

## 🐳 Docker Deployment Example

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SECRET_KEY="change_this_in_production"
ENV FLASK_APP=app.py

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

### docker-compose.yml

```yaml
version: '3'

services:
  analytics:
    build: .
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./instance:/app/instance
    environment:
      - SECRET_KEY=your_secure_key_here
```
```

Let me know if you want this split into multiple `.md` files or if you need badges or formatting tweaks.
