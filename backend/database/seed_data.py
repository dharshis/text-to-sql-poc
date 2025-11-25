"""
Data generation script for text-to-sql-poc sample database.

Generates realistic retail market research data:
- 5-10 client companies
- ~200 products with realistic names and pricing
- ~2000 sales records with seasonal patterns (Q4 boost)
- Customer segments for each client

Usage:
    python -m database.seed_data
"""

import random
import json
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Base, Client, Product, Sale, CustomerSegment

# Initialize Faker
fake = Faker()
random.seed(42)  # For reproducible demo data

# Configuration
NUM_CLIENTS = random.randint(5, 10)
NUM_PRODUCTS = 200
NUM_SALES = 2000
SEGMENTS_PER_CLIENT = 3

# Industries for retail companies
INDUSTRIES = [
    "Retail",
    "Consumer Goods",
    "E-commerce",
    "Fashion",
    "Electronics",
    "Specialty Retail"
]

# Product categories distribution
CATEGORIES = {
    "electronics": 0.40,    # 40% of products
    "apparel": 0.30,        # 30% of products
    "home_goods": 0.30      # 30% of products
}

# Realistic product templates by category
PRODUCT_TEMPLATES = {
    "electronics": [
        {"name": "Samsung Galaxy S24", "brand": "Samsung", "price_range": (699, 999)},
        {"name": "iPhone 15 Pro", "brand": "Apple", "price_range": (999, 1199)},
        {"name": "iPad Air", "brand": "Apple", "price_range": (599, 749)},
        {"name": "Sony WH-1000XM5 Headphones", "brand": "Sony", "price_range": (349, 399)},
        {"name": "Dell XPS 13 Laptop", "brand": "Dell", "price_range": (999, 1499)},
        {"name": "MacBook Air", "brand": "Apple", "price_range": (1099, 1299)},
        {"name": "Samsung 55\" QLED TV", "brand": "Samsung", "price_range": (799, 1299)},
        {"name": "Bose QuietComfort Earbuds", "brand": "Bose", "price_range": (279, 329)},
        {"name": "Apple Watch Series 9", "brand": "Apple", "price_range": (399, 499)},
        {"name": "PlayStation 5", "brand": "Sony", "price_range": (499, 549)},
        {"name": "Nintendo Switch OLED", "brand": "Nintendo", "price_range": (349, 349)},
        {"name": "Amazon Echo Dot", "brand": "Amazon", "price_range": (49, 59)},
        {"name": "Google Pixel 8", "brand": "Google", "price_range": (699, 799)},
        {"name": "Canon EOS R6 Camera", "brand": "Canon", "price_range": (2499, 2799)},
        {"name": "Kindle Paperwhite", "brand": "Amazon", "price_range": (139, 159)},
    ],
    "apparel": [
        {"name": "Nike Air Max 270", "brand": "Nike", "price_range": (150, 180)},
        {"name": "Adidas Ultraboost", "brand": "Adidas", "price_range": (180, 200)},
        {"name": "Levi's 501 Jeans", "brand": "Levi's", "price_range": (59, 79)},
        {"name": "North Face Jacket", "brand": "The North Face", "price_range": (149, 299)},
        {"name": "Patagonia Fleece", "brand": "Patagonia", "price_range": (99, 149)},
        {"name": "Ray-Ban Aviator Sunglasses", "brand": "Ray-Ban", "price_range": (153, 179)},
        {"name": "Columbia Hiking Boots", "brand": "Columbia", "price_range": (89, 129)},
        {"name": "Under Armour Sports Shirt", "brand": "Under Armour", "price_range": (29, 49)},
        {"name": "Timberland Boots", "brand": "Timberland", "price_range": (149, 199)},
        {"name": "Tommy Hilfiger Polo", "brand": "Tommy Hilfiger", "price_range": (49, 69)},
        {"name": "Calvin Klein T-Shirt", "brand": "Calvin Klein", "price_range": (39, 59)},
        {"name": "Vans Old Skool Sneakers", "brand": "Vans", "price_range": (60, 75)},
        {"name": "Carhartt Work Pants", "brand": "Carhartt", "price_range": (49, 69)},
        {"name": "Champion Hoodie", "brand": "Champion", "price_range": (39, 59)},
        {"name": "New Balance 990 Sneakers", "brand": "New Balance", "price_range": (175, 200)},
    ],
    "home_goods": [
        {"name": "Dyson V15 Vacuum", "brand": "Dyson", "price_range": (649, 749)},
        {"name": "Ninja Air Fryer", "brand": "Ninja", "price_range": (99, 149)},
        {"name": "KitchenAid Stand Mixer", "brand": "KitchenAid", "price_range": (299, 449)},
        {"name": "Instant Pot Duo", "brand": "Instant Pot", "price_range": (79, 99)},
        {"name": "Keurig Coffee Maker", "brand": "Keurig", "price_range": (99, 139)},
        {"name": "Nespresso Machine", "brand": "Nespresso", "price_range": (149, 299)},
        {"name": "Roomba i7 Robot Vacuum", "brand": "iRobot", "price_range": (599, 699)},
        {"name": "Philips Hue Smart Bulbs", "brand": "Philips", "price_range": (49, 79)},
        {"name": "Casper Mattress Queen", "brand": "Casper", "price_range": (695, 795)},
        {"name": "Vitamix Blender", "brand": "Vitamix", "price_range": (349, 549)},
        {"name": "Le Creuset Dutch Oven", "brand": "Le Creuset", "price_range": (329, 399)},
        {"name": "Shark Ion Vacuum", "brand": "Shark", "price_range": (229, 279)},
        {"name": "Cuisinart Food Processor", "brand": "Cuisinart", "price_range": (149, 199)},
        {"name": "Nest Thermostat", "brand": "Google", "price_range": (129, 169)},
        {"name": "All-Clad Cookware Set", "brand": "All-Clad", "price_range": (499, 799)},
    ]
}

# Regions for sales distribution
REGIONS = ["North", "South", "East", "West"]

# Customer segments
CUSTOMER_SEGMENTS = [
    {"name": "Premium", "demographics": {"age_range": "35-54", "income": "high"}},
    {"name": "Standard", "demographics": {"age_range": "25-44", "income": "medium"}},
    {"name": "Budget", "demographics": {"age_range": "18-34", "income": "low-medium"}}
]


def generate_clients():
    """Generate 5-10 retail company clients with realistic names and industries."""
    clients = []
    for _ in range(NUM_CLIENTS):
        client = Client(
            client_name=fake.company(),
            industry=random.choice(INDUSTRIES)
        )
        clients.append(client)
    return clients


def generate_products(client_ids):
    """
    Generate ~200 realistic products distributed across clients.

    Distribution:
    - 40% electronics ($50-$2000)
    - 30% apparel ($20-$300)
    - 30% home goods ($30-$800)
    """
    products = []
    products_per_category = {
        "electronics": int(NUM_PRODUCTS * CATEGORIES["electronics"]),
        "apparel": int(NUM_PRODUCTS * CATEGORIES["apparel"]),
        "home_goods": int(NUM_PRODUCTS * CATEGORIES["home_goods"])
    }

    for category, count in products_per_category.items():
        templates = PRODUCT_TEMPLATES[category]

        for i in range(count):
            # Cycle through templates to ensure variety
            template = templates[i % len(templates)]

            # Add variation to product names (e.g., different colors, sizes)
            if i // len(templates) > 0:
                suffixes = ["- Black", "- White", "- Blue", "- Red", "- Large", "- Medium", "- Pro"]
                product_name = f"{template['name']} {suffixes[i % len(suffixes)]}"
            else:
                product_name = template['name']

            # Randomize price within range
            min_price, max_price = template['price_range']
            price = round(random.uniform(min_price, max_price), 2)

            # Assign to random client
            client_id = random.choice(client_ids)

            product = Product(
                client_id=client_id,
                product_name=product_name,
                category=category,
                brand=template['brand'],
                price=price
            )
            products.append(product)

    return products


def generate_sales(client_ids, product_ids):
    """
    Generate ~2000 sales records with temporal patterns.

    Patterns:
    - Date range: 2023-01-01 to 2024-12-31
    - Q4 (Oct-Dec) has 1.5x higher volume (holiday season)
    - Random regional distribution
    - Quantity: 1-50 units per sale
    - Revenue: quantity * product price
    """
    sales = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    # Generate sales with Q4 seasonality
    for _ in range(NUM_SALES):
        # Generate random date
        random_days = random.randint(0, date_range)
        sale_date = start_date + timedelta(days=random_days)

        # Apply Q4 seasonality boost
        # If date is in Q4 (Oct-Dec), increase probability of higher quantity
        is_q4 = sale_date.month in [10, 11, 12]
        quantity_multiplier = 1.5 if is_q4 else 1.0

        # Random quantity with Q4 boost
        base_quantity = random.randint(1, 50)
        quantity = int(base_quantity * quantity_multiplier) if is_q4 and random.random() > 0.5 else base_quantity

        # Select random client and product
        client_id = random.choice(client_ids)
        product_id = random.choice(product_ids)

        # Calculate revenue (will be adjusted after we know actual product price)
        # For now, use placeholder - will be updated in seed_database()
        revenue = 0.0  # Placeholder

        sale = Sale(
            client_id=client_id,
            product_id=product_id,
            region=random.choice(REGIONS),
            date=sale_date.strftime("%Y-%m-%d"),
            quantity=quantity,
            revenue=revenue  # Will calculate after linking to product
        )
        sales.append(sale)

    return sales


def generate_customer_segments(client_ids):
    """Generate 3 customer segments (Premium, Standard, Budget) for each client."""
    segments = []
    for client_id in client_ids:
        for segment_data in CUSTOMER_SEGMENTS:
            segment = CustomerSegment(
                client_id=client_id,
                segment_name=segment_data["name"],
                demographics=json.dumps(segment_data["demographics"])
            )
            segments.append(segment)
    return segments


def seed_database(db_path="../data/text_to_sql_poc.db"):
    """
    Main function to seed the database with all sample data.

    Steps:
    1. Create database and tables
    2. Generate clients
    3. Generate products
    4. Generate sales
    5. Generate customer segments
    6. Calculate revenue for sales
    """
    print(f"Initializing database at {db_path}...")

    # Create engine and tables
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1: Generate and insert clients
        print(f"Generating {NUM_CLIENTS} clients...")
        clients = generate_clients()
        session.add_all(clients)
        session.commit()

        client_ids = [client.client_id for client in clients]
        print(f"✓ Created {len(clients)} clients")

        # Step 2: Generate and insert products
        print(f"Generating ~{NUM_PRODUCTS} products...")
        products = generate_products(client_ids)
        session.add_all(products)
        session.commit()

        product_ids = [product.product_id for product in products]
        print(f"✓ Created {len(products)} products")

        # Step 3: Generate and insert sales
        print(f"Generating ~{NUM_SALES} sales records...")
        sales = generate_sales(client_ids, product_ids)
        session.add_all(sales)
        session.flush()  # Flush to get sale IDs without committing

        # Update revenue for each sale based on actual product price
        print("Calculating revenue for sales...")
        for sale in sales:
            product = session.query(Product).filter_by(product_id=sale.product_id).first()
            sale.revenue = round(sale.quantity * product.price, 2)

        session.commit()
        print(f"✓ Created {len(sales)} sales records")

        # Step 4: Generate and insert customer segments
        print(f"Generating customer segments...")
        segments = generate_customer_segments(client_ids)
        session.add_all(segments)
        session.commit()
        print(f"✓ Created {len(segments)} customer segments")

        # Summary
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETE")
        print("="*60)
        print(f"Clients:           {len(clients)}")
        print(f"Products:          {len(products)}")
        print(f"Sales:             {len(sales)}")
        print(f"Customer Segments: {len(segments)}")
        print(f"Database location: {db_path}")
        print("="*60)

    except Exception as e:
        session.rollback()
        print(f"Error during database seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
