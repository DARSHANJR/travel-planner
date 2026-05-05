# 🌍 Wanderlust — Smart Travel Itinerary Planner

A full-stack travel planning web application built with Python Flask, SQLite, and Vanilla JS with Leaflet maps.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install flask flask-login flask-sqlalchemy werkzeug --break-system-packages

# 2. Run the application
python app.py

# 3. Open in browser
http://localhost:5000
```

## 🔑 Demo Login
- **Admin:** admin@travel.com / admin123
- Or register a new account

## ✨ Features

| Feature | Details |
|--------|---------|
| 🔐 Auth | Register, Login, Logout with hashed passwords |
| 🗺️ Destinations | 12 sample Indian destinations with images, costs, ratings |
| 🔍 Search & Filter | Search by name/location, filter by category, sort by cost/rating |
| 📋 Itinerary | Add/remove destinations, update duration, live cost calculation |
| 📅 Trip Planner | Enter dates, notes, confirm trips |
| 📊 Trip Tracking | Planned / Ongoing / Completed status auto-updates |
| ❤️ Wishlist | Save favourite destinations |
| ⭐ Reviews | Rate and review destinations |
| 💰 Budget Estimator | Dynamic calculator on destination detail page |
| 🗺️ Maps | Interactive Leaflet maps — home, itinerary, trip route |
| 🛡️ Admin Panel | Add/edit/delete destinations, view users and trips |
| 👤 Profile | Edit name, change password, view stats |

## 🏗️ Project Structure

```
travel-itinerary-planner/
├── app.py                   # Flask app, models, routes
├── templates/
│   ├── layout.html          # Base template
│   ├── index.html           # Homepage
│   ├── destinations.html    # Listing page
│   ├── destination.html     # Detail page
│   ├── itinerary.html       # Cart equivalent
│   ├── planner.html         # Trip checkout
│   ├── trip_confirmed.html  # Confirmation
│   ├── trips.html           # My Trips list
│   ├── trip_detail.html     # Trip detail
│   ├── wishlist.html        # Saved destinations
│   ├── profile.html         # User profile
│   ├── login.html           # Login
│   ├── register.html        # Register
│   ├── admin.html           # Admin dashboard
│   └── admin_form.html      # Add/Edit destination form
├── static/
│   ├── css/style.css        # Full design system
│   └── js/app.js            # Frontend interactions
└── database/
    └── db.sqlite3           # Auto-created on first run
```

## 🎨 Design System

| Token | Value |
|-------|-------|
| Primary | #2563eb |
| Accent | #f59e0b |
| Success | #22c55e |
| Background | #f8fafc |
| Font | Playfair Display + DM Sans |

## 📍 Sample Destinations
- Goa Beach Escape — ₹15,000
- Manali Mountain Retreat — ₹20,000
- Jaipur Royal Tour — ₹10,000
- Kerala Backwater Bliss — ₹25,000
- Ladakh High Altitude — ₹35,000
- Andaman Island Paradise — ₹30,000
- And 6 more!

## 🛠️ Tech Stack
- **Backend:** Python Flask + Flask-Login + Flask-SQLAlchemy
- **Database:** SQLite (auto-created)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Maps:** Leaflet.js (OpenStreetMap)
- **Icons:** Font Awesome 6
- **Fonts:** Google Fonts (Playfair Display + DM Sans)
