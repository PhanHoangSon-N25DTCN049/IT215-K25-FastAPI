from sqlalchemy.orm import Session
from app.models.product import Product

def get_all(db: Session):
    return db.query(Product).all()

def get_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def create(db: Session, product_data: dict):
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update(db: Session, db_product: Product, update_data: dict):
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete(db: Session, db_product: Product):
    db.delete(db_product)
    db.commit()