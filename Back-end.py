from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Admin01!@localhost:3307/discount_scraper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the database model
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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

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
        canonical_path=data['canonical_path']
    )
    db.session.add(new_deal)
    db.session.commit()
    return jsonify({"message": "Deal added successfully!"})

@app.route('/')
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
        "canonical_path": deal.canonical_path,
        "created_at": deal.created_at
    } for deal in deals])


if __name__ == '__main__':
    app.run(debug=True)
