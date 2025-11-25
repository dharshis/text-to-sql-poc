"""
SQLAlchemy models for text-to-sql-poc database schema.

This module defines the database tables for the retail market research sample data:
- clients: Retail companies using the system
- products: Product catalog for each client
- sales: Sales transaction records
- customer_segments: Customer segmentation data

All tables enforce client_id foreign key relationships for multi-tenant data isolation.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Client(Base):
    """Client/Company table - represents retail companies in the system."""

    __tablename__ = 'clients'

    client_id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String, nullable=False)
    industry = Column(String, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="client")
    sales = relationship("Sale", back_populates="client")
    customer_segments = relationship("CustomerSegment", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.client_id}, name='{self.client_name}', industry='{self.industry}')>"


class Product(Base):
    """Product catalog table - products sold by each client."""

    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # electronics, apparel, home_goods
    brand = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="products")
    sales = relationship("Sale", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.product_id}, name='{self.product_name}', category='{self.category}', price=${self.price})>"


# Index for frequent queries by client and category
Index('idx_products_client_category', Product.client_id, Product.category)


class Sale(Base):
    """Sales transaction table - records of product sales."""

    __tablename__ = 'sales'

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    region = Column(String, nullable=False)  # North, South, East, West
    date = Column(String, nullable=False)  # ISO format: YYYY-MM-DD
    quantity = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="sales")
    product = relationship("Product", back_populates="sales")

    def __repr__(self):
        return f"<Sale(id={self.sale_id}, client={self.client_id}, product={self.product_id}, revenue=${self.revenue})>"


# Index for frequent queries by client and date
Index('idx_sales_client_date', Sale.client_id, Sale.date)


class CustomerSegment(Base):
    """Customer segmentation table - demographic segments for each client."""

    __tablename__ = 'customer_segments'

    segment_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    segment_name = Column(String, nullable=False)  # Premium, Standard, Budget
    demographics = Column(String)  # JSON string: {"age_range": "25-34", "income": "high"}

    # Relationships
    client = relationship("Client", back_populates="customer_segments")

    def __repr__(self):
        return f"<CustomerSegment(id={self.segment_id}, client={self.client_id}, segment='{self.segment_name}')>"
