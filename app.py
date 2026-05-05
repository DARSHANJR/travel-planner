from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'travel-planner-secret-key-2024'
_basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(_basedir, 'database'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(_basedir, 'database', 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ─── MODELS ──────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    trips         = db.relationship('Trip',     backref='user', lazy=True)
    wishlist      = db.relationship('Wishlist', backref='user', lazy=True)
    reviews       = db.relationship('Review',   backref='user', lazy=True)

    def is_authenticated(self): return True
    def is_active(self):        return True
    def is_anonymous(self):     return False
    def get_id(self):           return str(self.id)
    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class Destination(db.Model):
    __tablename__  = 'destinations'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150), nullable=False)
    category       = db.Column(db.String(50),  nullable=False)
    description    = db.Column(db.Text,         nullable=False)
    estimated_cost = db.Column(db.Float,        nullable=False)
    image_url      = db.Column(db.String(500))
    rating         = db.Column(db.Float,  default=4.0)
    location       = db.Column(db.String(200))
    latitude       = db.Column(db.Float)
    longitude      = db.Column(db.Float)
    is_trending    = db.Column(db.Boolean, default=False)
    is_featured    = db.Column(db.Boolean, default=False)
    best_time      = db.Column(db.String(100))
    duration_days  = db.Column(db.Integer, default=3)
    tags           = db.Column(db.String(300))
    # ── Enriched detail fields ──
    highlights     = db.Column(db.Text)   # pipe-separated
    things_to_do   = db.Column(db.Text)   # pipe-separated
    travel_tips    = db.Column(db.Text)   # pipe-separated
    weather_info   = db.Column(db.String(300))
    language       = db.Column(db.String(100))
    currency       = db.Column(db.String(50))
    difficulty     = db.Column(db.String(30))  # Easy / Moderate / Challenging

    itinerary_items = db.relationship('ItineraryItem', backref='destination', lazy=True)
    reviews         = db.relationship('Review',        backref='destination', lazy=True)
    wishlisted_by   = db.relationship('Wishlist',      backref='destination', lazy=True)


class Trip(db.Model):
    __tablename__ = 'trips'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date)
    end_date   = db.Column(db.Date)
    notes      = db.Column(db.Text)
    total_cost = db.Column(db.Float,  default=0)
    status     = db.Column(db.String(20), default='Planned')
    created_at = db.Column(db.DateTime,   default=datetime.utcnow)
    items      = db.relationship('ItineraryItem', backref='trip', lazy=True, cascade='all, delete-orphan')


class ItineraryItem(db.Model):
    __tablename__  = 'itinerary_items'
    id             = db.Column(db.Integer, primary_key=True)
    trip_id        = db.Column(db.Integer, db.ForeignKey('trips.id'),        nullable=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'),        nullable=False)
    duration_days  = db.Column(db.Integer, default=3)
    session_id     = db.Column(db.String(100))


class Wishlist(db.Model):
    __tablename__  = 'wishlist'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'),        nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=False)
    added_at       = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__  = 'reviews'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'),        nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=False)
    rating         = db.Column(db.Integer, nullable=False)
    comment        = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def parse_pipe(text):
    """Convert pipe-separated string to list."""
    if not text:
        return []
    return [x.strip() for x in text.split('|') if x.strip()]

app.jinja_env.globals['parse_pipe'] = parse_pipe

# ─── SEED DATA ────────────────────────────────────────────────────────────────

def seed_data():
    if Destination.query.count() > 0:
        return
    destinations = [
        {
            "name": "Goa Beach Escape", "category": "Beach",
            "description": "Sun-kissed shores, vibrant nightlife, Portuguese heritage, and fresh seafood make Goa India's ultimate beach paradise. From Baga to Palolem, every beach tells a completely different story — party beaches up north, serene coves down south.",
            "estimated_cost": 15000, "image_url": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&q=80",
            "rating": 4.6, "location": "Goa, India", "latitude": 15.2993, "longitude": 74.1240,
            "is_trending": True, "is_featured": True, "best_time": "Nov – Feb", "duration_days": 5,
            "tags": "beach,party,seafood,heritage",
            "highlights": "Baga & Anjuna beaches|Portuguese Old Goa churches (UNESCO)|Dudhsagar Waterfall|Spice plantation tours|Vibrant Arpora night market",
            "things_to_do": "Parasailing & water sports at Baga|Sunset cruise on Mandovi River|Explore Fontainhas Latin Quarter|Try local Goan fish curry & feni|Visit Basilica of Bom Jesus|Night market shopping at Arpora",
            "travel_tips": "Book accommodation 2 months ahead for peak Dec–Jan|North Goa for parties, South Goa for peace & quiet|Rent a scooter — best way to explore (₹300/day)|Avoid monsoon Jun–Sep for beach visits|Carry cash — many beach shacks don't accept cards",
            "weather_info": "Tropical. Winter (Nov–Feb): 20–32°C, sunny & dry. Monsoon Jun–Sep: heavy rain.",
            "language": "Konkani, Hindi, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Manali Mountain Retreat", "category": "Mountain",
            "description": "Nestled in the Himalayas at 2,050m, Manali offers breathtaking snow-capped peaks, thrilling adventure sports, fragrant apple orchards, and the iconic Rohtang Pass. A haven for trekkers, honeymooners, and nature lovers.",
            "estimated_cost": 20000, "image_url": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800&q=80",
            "rating": 4.7, "location": "Manali, Himachal Pradesh", "latitude": 32.2396, "longitude": 77.1887,
            "is_trending": True, "is_featured": True, "best_time": "Mar – Jun", "duration_days": 6,
            "tags": "mountains,trekking,snow,adventure",
            "highlights": "Rohtang Pass at 3,978m|Solang Valley snow sports|Hadimba Devi Temple (1553 AD)|Beas River riverside walks|Old Manali cafes & hippie culture",
            "things_to_do": "Skiing & snowboarding at Solang Valley|Trek to Bhrigu Lake|River rafting on Beas River|Visit Naggar Castle (15th century)|Paragliding over the valleys|Day trip to Kasol & Kheerganga",
            "travel_tips": "Carry warm layers even in summer — nights drop to 5°C|Rohtang Pass requires a permit (book online at manalijammu.in)|Acclimatize for 1 day before strenuous trekking|ATMs limited beyond Manali — carry enough cash|Book homestays for authentic Himachali experience",
            "weather_info": "Alpine. Summer (Mar–Jun): 10–25°C. Winter (Dec–Feb): -5 to 10°C with heavy snowfall.",
            "language": "Hindi, Pahari, English", "currency": "Indian Rupee (₹)", "difficulty": "Moderate"
        },
        {
            "name": "Jaipur Royal Tour", "category": "Historical",
            "description": "The Pink City dazzles with magnificent forts, palaces, vibrant bazaars, and rich Rajasthani culture. Built in 1727 by Maharaja Jai Singh II, Jaipur is a UNESCO World Heritage city and India's finest example of royal Rajput architecture.",
            "estimated_cost": 10000, "image_url": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&q=80",
            "rating": 4.5, "location": "Jaipur, Rajasthan", "latitude": 26.9124, "longitude": 75.7873,
            "is_featured": True, "best_time": "Oct – Mar", "duration_days": 4,
            "tags": "history,culture,forts,shopping",
            "highlights": "Amber Fort — stunning hilltop fortress|Hawa Mahal — Palace of Winds (5 stories, 953 windows)|City Palace museum complex|Jantar Mantar observatory (UNESCO)|Johari Bazaar — gems & jewellery",
            "things_to_do": "Elephant ride up to Amber Fort at sunrise|Hot air balloon over the Pink City|Puppet show & Rajasthani folk dance evening|Shop for block-print textiles & blue pottery|Taste dal baati churma & ghewar|Sound & light show at Amber Fort",
            "travel_tips": "Hire a local guide at Amber Fort — stories make it magical|Bargain at bazaars — first price is always 3x real price|Wear modest clothing at temple and palace sites|Auto-rickshaws are cheapest for city travel|Try the famous Lassiwala on MI Road",
            "weather_info": "Semi-arid. Best (Oct–Mar): 8–25°C. Summers very hot up to 45°C. Avoid Apr–Jun.",
            "language": "Hindi, Rajasthani, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Kerala Backwater Bliss", "category": "Beach",
            "description": "God's Own Country enchants with 900km of serene backwaters, lush tea plantations, Ayurvedic wellness spas, and vibrant Kathakali dance performances. Kerala offers a unique pace of life found nowhere else in India.",
            "estimated_cost": 25000, "image_url": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&q=80",
            "rating": 4.8, "location": "Kerala, India", "latitude": 9.9312, "longitude": 76.2673,
            "is_trending": True, "is_featured": True, "best_time": "Sep – Mar", "duration_days": 7,
            "tags": "backwaters,nature,ayurveda,houseboats",
            "highlights": "Alleppey houseboat overnight stays|Munnar tea plantation sunrise views|Periyar Wildlife Sanctuary boat safari|Kovalam & Varkala cliff beaches|Traditional Kathakali performance in Kochi",
            "things_to_do": "Overnight houseboat stay in Alleppey backwaters|Ayurvedic Panchakarma treatment (minimum 3 days)|Jungle safari at Wayanad Wildlife Sanctuary|Kerala cooking class|Sunrise walk through Munnar tea gardens|Kalaripayattu martial arts show",
            "travel_tips": "Book houseboats 3–4 months in advance for winter|November to February is peak — book everything early|Mosquito repellent essential near backwaters|Try Kerala sadya (banana leaf feast) on Sundays|Trains are scenic and affordable between Kochi–Munnar–Alleppey",
            "weather_info": "Tropical. Pleasant Oct–Mar: 22–33°C. Two monsoon seasons — Jun–Aug and Oct–Nov.",
            "language": "Malayalam, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Rajasthan Desert Safari", "category": "Historical",
            "description": "Ride camels across golden Thar Desert dunes, sleep under a billion stars, and immerse in the timeless culture of Rajputana. Jaisalmer — the Golden City — rises from the desert like a living sandcastle, its fort still inhabited after 850 years.",
            "estimated_cost": 18000, "image_url": "https://images.unsplash.com/photo-1477587458883-47145ed31fde?w=800&q=80",
            "rating": 4.4, "location": "Jaisalmer, Rajasthan", "latitude": 26.9157, "longitude": 70.9083,
            "is_trending": True, "best_time": "Oct – Feb", "duration_days": 5,
            "tags": "desert,safari,camping,culture",
            "highlights": "Sam Sand Dunes camel safari|Jaisalmer Fort — 850-year living fortress|Patwon Ki Haveli ornate stone mansions|Gadisar Lake at sunset|Desert cultural evening with folk music & bonfire",
            "things_to_do": "Overnight desert camping under the stars|Camel safari at sunrise and sunset|Explore the living Jaisalmer Fort|Dune bashing in 4x4 jeeps|Visit ghost town of Kuldhara|Folk music & dance bonfire evenings",
            "travel_tips": "Desert nights are cold (Nov–Jan) — always carry a warm jacket|Stay inside Jaisalmer Fort for a unique experience|Book overnight desert camps through registered operators only|Carry lip balm & strong sunscreen — very dry & sunny|Bargain hard at fort souvenir shops",
            "weather_info": "Arid desert. Best (Oct–Feb): 7–25°C. Summers extremely hot 40–48°C. Avoid May–June.",
            "language": "Hindi, Rajasthani", "currency": "Indian Rupee (₹)", "difficulty": "Moderate"
        },
        {
            "name": "Ladakh High Altitude Adventure", "category": "Mountain",
            "description": "The land of high passes and ancient monasteries sits at 3,500m above sea level. Pangong Lake shifts from turquoise to cobalt to steel-blue within minutes. Nubra Valley's Bactrian camels, remote gompas, and the world's highest motorable roads create an experience unlike anywhere on Earth.",
            "estimated_cost": 35000, "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
            "rating": 4.9, "location": "Leh, Ladakh", "latitude": 34.1526, "longitude": 77.5771,
            "is_trending": True, "best_time": "Jun – Sep", "duration_days": 8,
            "tags": "adventure,mountains,monasteries,lakes",
            "highlights": "Pangong Tso — 134km high-altitude lake|Khardung La Pass at 5,359m|Nubra Valley & double-humped Bactrian camels|Thiksey & Hemis monasteries|Magnetic Hill optical illusion on Leh-Kargil highway",
            "things_to_do": "Royal Enfield bike ride on Manali-Leh Highway|Camping on Pangong Lake shore|Visit 1,000-year-old Lamayuru Monastery|Rafting on Zanskar River|Stok Kangri summit trek (6,153m)|Attend the Hemis Monastery Festival (July)",
            "travel_tips": "CRITICAL: Spend 2 full days acclimatizing in Leh before any activity|Carry altitude sickness medicine Diamox — consult doctor first|Requires Inner Line Permit for border areas (Pangong, Nubra)|No reliable ATM beyond Leh — carry sufficient cash|Petrol stations scarce — fill tank at every opportunity|Oxygen levels are 40% lower than sea level",
            "weather_info": "High-altitude cold desert. Summer (Jun–Sep): 10–25°C days, 0–5°C nights. Roads closed Oct–May due to snow.",
            "language": "Ladakhi, Hindi, English", "currency": "Indian Rupee (₹)", "difficulty": "Challenging"
        },
        {
            "name": "Agra Heritage Walk", "category": "Historical",
            "description": "Agra is home to three UNESCO World Heritage Sites — the Taj Mahal, Agra Fort, and Fatehpur Sikri. Built by Mughal Emperor Shah Jahan as an eternal testament to love, the Taj Mahal at sunrise remains one of humanity's most transcendent architectural experiences.",
            "estimated_cost": 8000, "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&q=80",
            "rating": 4.6, "location": "Agra, Uttar Pradesh", "latitude": 27.1767, "longitude": 78.0081,
            "is_featured": True, "best_time": "Oct – Mar", "duration_days": 2,
            "tags": "heritage,taj mahal,mughal,history",
            "highlights": "Taj Mahal at sunrise — a bucket-list moment|Agra Fort — Mughal imperial complex|Fatehpur Sikri — abandoned Mughal capital|Mehtab Bagh — Taj Mahal reflection garden|Kinari Bazaar for marble inlay handicrafts",
            "things_to_do": "Visit Taj Mahal at both sunrise and sunset|Explore Agra Fort's Diwan-i-Khas & Diwan-i-Am|Day trip to Fatehpur Sikri (37km away)|Watch Taj from Mehtab Bagh across Yamuna at dusk|Buy genuine marble inlay souvenirs|Try Agra's famous petha sweet & Mughlai cuisine",
            "travel_tips": "Arrive at Taj Mahal gate 30 minutes before opening to beat crowds|Fridays: Taj Mahal is closed to non-Muslims|Photography tripods not allowed inside Taj Mahal|Carry only small bags — large bags not permitted inside|Taj is just 2 hours from Delhi by Shatabdi Express|Hire ASI-certified guides at the entrance gate",
            "weather_info": "Semi-arid. Best (Oct–Mar): 8–28°C. Dense fog Dec–Jan can obscure Taj. Summers very hot 42°C+.",
            "language": "Hindi, Urdu, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Andaman Island Paradise", "category": "Beach",
            "description": "Crystal-clear turquoise waters, pristine coral reefs, and powdery white-sand beaches make the Andaman Islands India's most spectacular coastal destination. With 572 islands — only 37 inhabited — untouched nature is always just a ferry ride away.",
            "estimated_cost": 30000, "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80",
            "rating": 4.7, "location": "Port Blair, Andaman", "latitude": 11.7401, "longitude": 92.6586,
            "best_time": "Oct – May", "duration_days": 6,
            "tags": "islands,scuba,beach,snorkeling",
            "highlights": "Radhanagar Beach — Asia's best beach (Time Magazine)|Havelock Island crystal-clear waters|PADI scuba diving at North Bay|Cellular Jail — moving colonial history|Mahatma Gandhi Marine National Park",
            "things_to_do": "PADI scuba diving certification course|Glass-bottom boat at Coral Island|Sea kayaking through mangroves|Cellular Jail's Sound & Light show|Snorkeling at Elephant Beach, Havelock|Early morning dolphin watching",
            "travel_tips": "Book ferries to Havelock 2–3 weeks in advance|Pack reef-safe sunscreen to protect the coral|Limited ATMs on outer islands — carry enough cash|Inter-island ferries can be rough in choppy seas|Permit required for restricted tribal reserve areas|Best underwater visibility January to April",
            "weather_info": "Tropical maritime. Pleasant Oct–May: 23–30°C. Monsoon Jun–Sep brings rough seas and heavy rain.",
            "language": "Hindi, Bengali, Tamil, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Varanasi Spiritual Journey", "category": "Historical",
            "description": "One of the world's oldest continuously inhabited cities (over 3,000 years old), Varanasi is the spiritual heart of India. Every evening the Ganga Aarti ceremony lights up the ancient ghats with fire, chanting, and devotion in a profoundly moving spectacle.",
            "estimated_cost": 7000, "image_url": "https://images.unsplash.com/photo-1561361058-c24e021b4d0d?w=800&q=80",
            "rating": 4.3, "location": "Varanasi, UP", "latitude": 25.3176, "longitude": 82.9739,
            "best_time": "Oct – Mar", "duration_days": 3,
            "tags": "spiritual,ghats,temples,culture",
            "highlights": "Evening Ganga Aarti at Dashashwamedh Ghat|Pre-dawn boat ride on the Ganges|Kashi Vishwanath Temple — one of 12 Jyotirlingas|Sarnath — where Buddha gave his first sermon|Narrow 3,000-year-old lanes of the old city",
            "things_to_do": "Pre-dawn boat ride to watch sunrise on the Ganges|Attend evening Ganga Aarti ceremony|Visit Sarnath Buddhist ruins & museum (10km away)|Walk all 88 ghats from Assi to Manikarnika|Silk weaving workshop at a Banarasi loom|Classical Indian music concert at a heritage haveli",
            "travel_tips": "Manikarnika Ghat is an active cremation site — be respectful, no photos|Best Ganga Aarti viewing spot: arrive 45 minutes early for front row|Narrow lanes only accessible by cycle rickshaw|Stay near Assi Ghat for quieter, cleaner accommodation|Drink only bottled water — never Ganges water|Photography restricted at certain ghats — always ask first",
            "weather_info": "Subtropical. Best (Oct–Mar): 8–25°C. Summers intensely hot 40–45°C. Monsoon Jul–Sep brings ghat flooding.",
            "language": "Hindi, Bhojpuri, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
        {
            "name": "Coorg Coffee Country", "category": "Mountain",
            "description": "Called the Scotland of India, Coorg (Kodagu) is draped in misty hills, emerald coffee and tea plantations, and roaring waterfalls. Home to the proud Kodava warrior tribe, it offers a unique blend of untouched nature, rich culture, and exceptional cuisine.",
            "estimated_cost": 12000, "image_url": "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800&q=80",
            "rating": 4.5, "location": "Coorg, Karnataka", "latitude": 12.3375, "longitude": 75.8069,
            "is_trending": True, "best_time": "Oct – Mar", "duration_days": 4,
            "tags": "coffee,nature,trekking,waterfalls",
            "highlights": "Abbey Falls & Iruppu Falls|Estate coffee & spice plantation tours|Namdroling Monastery — Golden Temple|Brahmagiri Wildlife Sanctuary trek|Dubare Elephant Camp on the river",
            "things_to_do": "Morning coffee plantation walk & cupping session|Elephant bathing interaction at Dubare|Trek to Tadiandamol peak (1,748m — Coorg's highest)|White water rafting on Barapole River|Attend a traditional Kodava Kailpodh festival|Cook authentic pandi curry (pork) with a local family",
            "travel_tips": "Rent a car or hire a taxi — no public transport between sights|Leeches common during monsoon — wear closed shoes|Coffee estate stays (homestays) offer best experience|Buy fresh estate coffee — far better than any retail brand|Coorg roads are steep and winding — drive carefully and slowly|Mist-covered mornings from Nov–Jan are magical",
            "weather_info": "Highland tropical. Cool year-round: 15–28°C. Heavy monsoon Jun–Sep transforms the landscape.",
            "language": "Kodava, Kannada, English", "currency": "Indian Rupee (₹)", "difficulty": "Moderate"
        },
        {
            "name": "Rishikesh Yoga & Adventure", "category": "Mountain",
            "description": "Where the Ganges rushes out of the Himalayas, Rishikesh blends world-class white water rafting with ancient yoga ashrams. The Beatles meditated here in 1968. Today it remains the yoga capital of the world and India's undisputed adventure sports hub.",
            "estimated_cost": 9000, "image_url": "https://images.unsplash.com/photo-1609766857491-2493b0e13b98?w=800&q=80",
            "rating": 4.6, "location": "Rishikesh, Uttarakhand", "latitude": 30.0869, "longitude": 78.2676,
            "is_featured": True, "best_time": "Feb – May", "duration_days": 4,
            "tags": "yoga,rafting,adventure,spiritual",
            "highlights": "Grade 3–4 white water rafting on Ganges|Laxman Jhula & Ram Jhula suspension bridges|Beatles Ashram ruins (Maharishi Mahesh Yogi)|Neer Garh Waterfall trek|Evening Ganga Aarti at Triveni Ghat",
            "things_to_do": "White water rafting (Grade 2–4 rapids, 16–35km stretches)|Multi-day yoga & meditation retreat at an ashram|Bungee jumping (83m) at Jumpin Heights|Overnight beach camping on Ganges banks|Trek to Kunjapuri Temple for Himalaya sunrise|Free morning yoga classes at Parmarth Niketan ashram",
            "travel_tips": "Rafting season is September to June — suspended during monsoon|Only book with RAFT certified operators for safety|Alcohol and non-veg food banned in Rishikesh central zone|Laxman Jhula area has most backpacker cafes & yoga centers|Carry warm layers — evenings cool year-round even in summer|200-hour Yoga TTC (Teacher Training Courses) available month-long",
            "weather_info": "Sub-himalayan. Pleasant Feb–June: 15–35°C. Monsoon Jul–Sep: heavy rain, rafting suspended. Winter Dec–Jan: cold.",
            "language": "Hindi, English", "currency": "Indian Rupee (₹)", "difficulty": "Moderate"
        },
        {
            "name": "Mumbai City Experience", "category": "City",
            "description": "The city of dreams pulses 24/7 with energy, ambition, and breathtaking contrasts. From the grandeur of the Gateway of India to Dharavi's resilience, from Bollywood studios to Victorian architecture, world-class restaurants to ₹20 vada pav — Mumbai never ceases to amaze.",
            "estimated_cost": 13000, "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=800&q=80",
            "rating": 4.4, "location": "Mumbai, Maharashtra", "latitude": 19.0760, "longitude": 72.8777,
            "is_featured": True, "best_time": "Nov – Feb", "duration_days": 4,
            "tags": "city,bollywood,food,architecture",
            "highlights": "Gateway of India & Taj Mahal Palace Hotel|Marine Drive — the Queen's Necklace at night|Chhatrapati Shivaji Terminus (UNESCO)|Dharavi — Asia's largest & most entrepreneurial slum|Bandra-Worli Sea Link at sunset",
            "things_to_do": "Bollywood studio tour (Film City, Goregaon)|Ferry to Elephanta Caves (UNESCO World Heritage)|Mohammed Ali Road street food walk|Watch a Bollywood film at a heritage single-screen cinema|Sunset at Bandra Fort with sea views|Explore Chor Bazaar antique market on Fridays",
            "travel_tips": "Local trains are fastest but very crowded during rush hour (8–10am, 5–8pm)|Uber/Ola autos and taxis are affordable for tourists|Mumbai street food is legendary — try vada pav, pav bhaji, bhel puri|Book Elephanta Caves ferry from Gateway of India in the morning|Monsoon Jun–Sep: beautiful but flooding possible in low-lying areas|Nightlife scene excellent in Bandra, Juhu, and Lower Parel",
            "weather_info": "Tropical. Best (Nov–Feb): 18–32°C, pleasant & dry. Monsoon Jun–Sep: 2,200mm rainfall, high humidity.",
            "language": "Marathi, Hindi, English", "currency": "Indian Rupee (₹)", "difficulty": "Easy"
        },
    ]

    for d in destinations:
        db.session.add(Destination(**d))

    admin = User(name="Admin User", email="admin@travel.com", is_admin=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()

# ─── CONTEXT PROCESSORS ───────────────────────────────────────────────────────

@app.context_processor
def inject_cart_count():
    count = 0
    if current_user.is_authenticated:
        sid = session.get('cart_session')
        if sid:
            count = ItineraryItem.query.filter_by(
                user_id=current_user.id, trip_id=None, session_id=sid).count()
    return dict(cart_count=count)

# ─── PUBLIC ROUTES ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    featured    = Destination.query.filter_by(is_featured=True).limit(6).all()
    trending    = Destination.query.filter_by(is_trending=True).limit(4).all()
    random_recs = Destination.query.all()
    random.shuffle(random_recs)
    recommended = random_recs[:4]
    categories  = [c[0] for c in db.session.query(Destination.category).distinct().all()]
    return render_template('index.html', featured=featured, trending=trending,
                           recommended=recommended, categories=categories)


@app.route('/destinations')
def destinations():
    q        = request.args.get('q', '')
    category = request.args.get('category', '')
    sort     = request.args.get('sort', '')
    query    = Destination.query
    if q:
        query = query.filter(
            Destination.name.ilike(f'%{q}%') |
            Destination.description.ilike(f'%{q}%') |
            Destination.location.ilike(f'%{q}%'))
    if category:
        query = query.filter_by(category=category)
    if sort == 'cost_asc':
        query = query.order_by(Destination.estimated_cost.asc())
    elif sort == 'cost_desc':
        query = query.order_by(Destination.estimated_cost.desc())
    elif sort == 'rating':
        query = query.order_by(Destination.rating.desc())
    dests      = query.all()
    categories = [c[0] for c in db.session.query(Destination.category).distinct().all()]
    return render_template('destinations.html', destinations=dests, categories=categories,
                           selected_category=category, q=q, sort=sort)


@app.route('/destination/<int:dest_id>')
def destination_detail(dest_id):
    dest         = Destination.query.get_or_404(dest_id)
    reviews      = Review.query.filter_by(destination_id=dest_id).order_by(Review.created_at.desc()).all()
    is_wishlisted = False
    if current_user.is_authenticated:
        is_wishlisted = Wishlist.query.filter_by(
            user_id=current_user.id, destination_id=dest_id).first() is not None
    similar = Destination.query.filter_by(category=dest.category).filter(
        Destination.id != dest_id).limit(3).all()
    return render_template('destination.html', dest=dest, reviews=reviews,
                           is_wishlisted=is_wishlisted, similar=similar,
                           highlights=parse_pipe(dest.highlights),
                           things_to_do=parse_pipe(dest.things_to_do),
                           travel_tips=parse_pipe(dest.travel_tips))


@app.route('/add_review/<int:dest_id>', methods=['POST'])
@login_required
def add_review(dest_id):
    rating  = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    existing = Review.query.filter_by(user_id=current_user.id, destination_id=dest_id).first()
    if existing:
        existing.rating  = rating
        existing.comment = comment
    else:
        db.session.add(Review(user_id=current_user.id, destination_id=dest_id,
                               rating=rating, comment=comment))
    dest = Destination.query.get(dest_id)
    all_reviews = Review.query.filter_by(destination_id=dest_id).all()
    if all_reviews:
        dest.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
    db.session.commit()
    flash('Review submitted!', 'success')
    return redirect(url_for('destination_detail', dest_id=dest_id))

# ─── ITINERARY ────────────────────────────────────────────────────────────────

@app.route('/itinerary')
@login_required
def itinerary():
    sid   = session.get('cart_session')
    items = []
    if sid:
        items = ItineraryItem.query.filter_by(
            user_id=current_user.id, trip_id=None, session_id=sid).all()
    total = sum(i.destination.estimated_cost * i.duration_days / i.destination.duration_days
                for i in items)
    return render_template('itinerary.html', items=items, total=round(total, 2))


@app.route('/add_to_itinerary/<int:dest_id>', methods=['POST'])
@login_required
def add_to_itinerary(dest_id):
    if 'cart_session' not in session:
        session['cart_session'] = f"cart_{current_user.id}_{datetime.utcnow().timestamp()}"
    sid      = session['cart_session']
    existing = ItineraryItem.query.filter_by(
        user_id=current_user.id, destination_id=dest_id, trip_id=None, session_id=sid).first()
    if not existing:
        dest = Destination.query.get_or_404(dest_id)
        db.session.add(ItineraryItem(user_id=current_user.id, destination_id=dest_id,
                                      duration_days=dest.duration_days, session_id=sid))
        db.session.commit()
        flash(f'{dest.name} added to itinerary!', 'success')
    else:
        flash('Already in your itinerary!', 'info')
    return redirect(request.referrer or url_for('destinations'))


@app.route('/remove_from_itinerary/<int:item_id>', methods=['POST'])
@login_required
def remove_from_itinerary(item_id):
    item = ItineraryItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('itinerary'))


@app.route('/update_duration/<int:item_id>', methods=['POST'])
@login_required
def update_duration(item_id):
    item = ItineraryItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        days = int(request.form.get('days', 1))
        item.duration_days = max(1, min(days, 30))
        db.session.commit()
    return redirect(url_for('itinerary'))

# ─── PLANNER ──────────────────────────────────────────────────────────────────

@app.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():
    sid   = session.get('cart_session')
    items = []
    if sid:
        items = ItineraryItem.query.filter_by(
            user_id=current_user.id, trip_id=None, session_id=sid).all()
    if not items:
        flash('Your itinerary is empty. Add some destinations first!', 'warning')
        return redirect(url_for('destinations'))
    total = sum(i.destination.estimated_cost * i.duration_days / i.destination.duration_days
                for i in items)
    if request.method == 'POST':
        title      = request.form.get('title', 'My Trip')
        start_date = request.form.get('start_date')
        end_date   = request.form.get('end_date')
        notes      = request.form.get('notes', '')
        trip = Trip(
            user_id=current_user.id, title=title,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date()     if end_date   else None,
            notes=notes, total_cost=round(total, 2), status='Planned')
        db.session.add(trip)
        db.session.flush()
        for item in items:
            item.trip_id    = trip.id
            item.session_id = None
        session.pop('cart_session', None)
        db.session.commit()
        flash('Trip planned successfully! 🎉', 'success')
        return redirect(url_for('trip_confirmed', trip_id=trip.id))
    return render_template('planner.html', items=items, total=round(total, 2))


@app.route('/trip_confirmed/<int:trip_id>')
@login_required
def trip_confirmed(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('trip_confirmed.html', trip=trip)

# ─── TRIPS ────────────────────────────────────────────────────────────────────

@app.route('/trips')
@login_required
def trips():
    today = date.today()
    for trip in Trip.query.filter_by(user_id=current_user.id).all():
        if trip.start_date and trip.end_date:
            if trip.start_date <= today <= trip.end_date:
                trip.status = 'Ongoing'
            elif trip.end_date < today:
                trip.status = 'Completed'
    db.session.commit()
    all_trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
    return render_template('trips.html', trips=all_trips)


@app.route('/trip/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('trips'))
    return render_template('trip_detail.html', trip=trip)


@app.route('/delete_trip/<int:trip_id>', methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id == current_user.id:
        db.session.delete(trip)
        db.session.commit()
        flash('Trip deleted.', 'success')
    return redirect(url_for('trips'))

# ─── WISHLIST ─────────────────────────────────────────────────────────────────

@app.route('/wishlist/toggle/<int:dest_id>', methods=['POST'])
@login_required
def toggle_wishlist(dest_id):
    existing = Wishlist.query.filter_by(user_id=current_user.id, destination_id=dest_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'status': 'removed'})
    db.session.add(Wishlist(user_id=current_user.id, destination_id=dest_id))
    db.session.commit()
    return jsonify({'status': 'added'})


@app.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.added_at.desc()).all()
    return render_template('wishlist.html', items=items)

# ─── PROFILE ──────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        new_pw = request.form.get('new_password', '')
        if new_pw:
            current_user.set_password(new_pw)
        db.session.commit()
        flash('Profile updated!', 'success')
    trips_count    = Trip.query.filter_by(user_id=current_user.id).count()
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    reviews_count  = Review.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html', trips_count=trips_count,
                           wishlist_count=wishlist_count, reviews_count=reviews_count)

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name, email, password = request.form.get('name'), request.form.get('email'), request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome, {name}! Start planning your dream trip!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email, password = request.form.get('email'), request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ─── ADMIN ────────────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin')
@login_required
@admin_required
def admin():
    destinations = Destination.query.all()
    users        = User.query.all()
    trips        = Trip.query.order_by(Trip.created_at.desc()).limit(20).all()
    stats = {
        'destinations': Destination.query.count(),
        'users':        User.query.count(),
        'trips':        Trip.query.count(),
        'reviews':      Review.query.count(),
    }
    return render_template('admin.html', destinations=destinations,
                           users=users, trips=trips, stats=stats)


def _apply_dest_form(dest, form):
    """Apply form data to a Destination. Handles checkboxes correctly (absent = False)."""
    dest.name           = form['name']
    dest.category       = form['category']
    dest.description    = form['description']
    dest.estimated_cost = float(form['estimated_cost'])
    dest.image_url      = form.get('image_url', '')
    dest.location       = form.get('location', '')
    dest.best_time      = form.get('best_time', '')
    dest.tags           = form.get('tags', '')
    dest.highlights     = form.get('highlights', '')
    dest.things_to_do   = form.get('things_to_do', '')
    dest.travel_tips    = form.get('travel_tips', '')
    dest.weather_info   = form.get('weather_info', '')
    dest.language       = form.get('language', '')
    dest.currency       = form.get('currency', 'Indian Rupee (₹)')
    dest.difficulty     = form.get('difficulty', 'Easy')
    try:
        dest.rating        = float(form.get('rating', 4.0))
        dest.duration_days = int(form.get('duration_days', 3))
        dest.latitude      = float(form.get('latitude') or 0)
        dest.longitude     = float(form.get('longitude') or 0)
    except (ValueError, TypeError):
        pass
    # ── KEY FIX: HTML checkboxes send 'on' when checked, nothing when unchecked ──
    # Using `bool(form.get(...))` was always False for unchecked → stored False
    # Correct approach: check if the key EXISTS in the form dict
    dest.is_featured = 'is_featured' in form
    dest.is_trending = 'is_trending' in form
    return dest


@app.route('/admin/destination/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_destination():
    if request.method == 'POST':
        dest = _apply_dest_form(Destination(), request.form)
        db.session.add(dest)
        db.session.commit()
        featured_status = "Featured ✓" if dest.is_featured else "Not featured"
        trending_status = "Trending ✓" if dest.is_trending else "Not trending"
        flash(f'✅ "{dest.name}" added! {featured_status} | {trending_status} — Visible to all users immediately.', 'success')
        return redirect(url_for('admin'))
    return render_template('admin_form.html', dest=None)


@app.route('/admin/destination/edit/<int:dest_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_destination(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    if request.method == 'POST':
        _apply_dest_form(dest, request.form)
        db.session.commit()
        featured_status = "Featured ✓" if dest.is_featured else "Removed from Featured"
        trending_status = "Trending ✓" if dest.is_trending else "Removed from Trending"
        flash(f'✅ "{dest.name}" updated! {featured_status} | {trending_status} — Changes live for all users.', 'success')
        return redirect(url_for('admin'))
    return render_template('admin_form.html', dest=dest)


@app.route('/admin/destination/delete/<int:dest_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_destination(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    name = dest.name
    db.session.delete(dest)
    db.session.commit()
    flash(f'🗑️ "{name}" has been deleted and is no longer visible to users.', 'success')
    return redirect(url_for('admin'))


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/destinations')
def api_destinations():
    dests = Destination.query.all()
    return jsonify([{
        'id': d.id, 'name': d.name, 'lat': d.latitude, 'lng': d.longitude,
        'category': d.category, 'cost': d.estimated_cost, 'rating': d.rating
    } for d in dests if d.latitude and d.longitude])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, port=5000)
