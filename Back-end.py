from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Admin01!@localhost:3307/discount_scraper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# Define the database models
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
    url = db.Column(db.String(255))  # Full URL for the deal
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database tables
with app.app_context():
    db.create_all()

# API endpoint to add a deal
@app.route('/add_deal', methods=['POST'])
def add_deal():
    data = request.json
    new_deal = Deal(
        product_name=data['product_name'],
        price=data['price'],
        old_price=data.get('old_price'),
        discount_percentage=data['discount_percentage'],
        description=data['description'],
        image_url=data['image_url'],
        canonical_path=data['canonical_path'],
        url=f"https://www.lidl.nl{data['canonical_path']}"
    )
    db.session.add(new_deal)
    db.session.commit()
    return jsonify({"message": "Deal added successfully!"})

@app.route('/')
@login_required
def index():
    return render_template("index.html")  # Serve the HTML file

@app.route('/api/deals')
def get_deals():
    deals = Deal.query.all()
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
    } for deal in deals])

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Ensure JSON data is parsed
    if not data:
        return jsonify({"error": "Invalid request payload"}), 400

    # Validate input fields
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    # Check for existing user
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a new user
    new_user = User(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# User login endpoint
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.get_json()  # Parse JSON data
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Invalid request payload"}), 400

        user = User.query.filter_by(username=data['username']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            login_user(user)
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    return render_template("login.html")



# User logout endpoint
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
