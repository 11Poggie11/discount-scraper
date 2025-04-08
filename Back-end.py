from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from sqlalchemy import select

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Admin01!@localhost:3307/discount_scraper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# Database models
class Deal(db.Model):
    __tablename__ = 'deals'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float)
    discount_percentage = db.Column(db.Integer)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    canonical_path = db.Column(db.String(255))
    url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ViewedDeal(db.Model):
    __tablename__ = 'viewed_deals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'), nullable=False)
    swipe_direction = db.Column(db.String(10), nullable=False)  # 'liked' or 'disliked'
    viewed_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Initialize database
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/api/deals')
@login_required
def get_deals():
    # Get unviewed deals using SQLAlchemy 2.x syntax
    subquery = select(ViewedDeal.deal_id).where(
        ViewedDeal.user_id == current_user.id
    ).scalar_subquery()
    
    available_deals = Deal.query.filter(
        Deal.id.notin_(subquery)
    ).all()

    return jsonify([{
        "id": deal.id,
        "product_name": deal.product_name,
        "price": deal.price,
        "old_price": deal.old_price,
        "discount_percentage": deal.discount_percentage,
        "description": deal.description,
        "image_url": deal.image_url,
        "url": deal.url,
        "created_at": deal.created_at
    } for deal in available_deals])

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            login_user(user)
            return jsonify({"message": "Login successful!"}), 200
        return jsonify({"error": "Invalid credentials"}), 401
    return render_template("login.html")

@app.route('/api/mark_viewed', methods=['POST'])
@login_required
def mark_viewed():
    data = request.get_json()
    deal_id = data.get('deal_id')
    swipe_direction = data.get('swipe_direction')  # 'liked' or 'disliked'

    if not deal_id or not swipe_direction:
        return jsonify({"error": "Missing deal_id or swipe_direction"}), 400

    # Check for existing entry
    existing = ViewedDeal.query.filter_by(
        user_id=current_user.id,
        deal_id=deal_id
    ).first()

    if existing:
        # Update swipe direction if already viewed
        existing.swipe_direction = swipe_direction
        existing.viewed_at = db.func.current_timestamp()
    else:
        # Create a new entry
        new_view = ViewedDeal(user_id=current_user.id, deal_id=deal_id, swipe_direction=swipe_direction)
        db.session.add(new_view)

    db.session.commit()
    
    return jsonify({"message": f"Deal marked as {swipe_direction}"}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Add these routes to your Back-end.py

@app.route('/api/liked_deals')
@login_required
def get_liked_deals():
    liked_deals = ViewedDeal.query.filter_by(
        user_id=current_user.id,
        swipe_direction='liked'
    ).join(Deal).add_entity(Deal).all()
    
    return jsonify([{
        "id": deal.id,
        "product_name": deal.product_name,
        # Include all other deal fields
    } for view, deal in liked_deals])

@app.route('/api/viewed_deals')
@login_required
def get_viewed_deals():
    viewed_deals = ViewedDeal.query.filter_by(
        user_id=current_user.id
    ).join(Deal).add_entity(Deal).all()
    
    return jsonify([{
        "id": deal.id,
        "product_name": deal.product_name,
        "swipe_direction": view.swipe_direction,
        # Include all other deal fields
    } for view, deal in viewed_deals])


if __name__ == '__main__':
    app.run(debug=True)
