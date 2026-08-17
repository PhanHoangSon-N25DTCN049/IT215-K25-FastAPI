from sqlalchemy.orm import Session
from app.models import Users
import bcrypt

def query_username(username: str, db: Session):
    return db.query(Users).filter(Users.username == username).first()
 
def hash_password(password: str):
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()

def verity_password(password: str, hash_pw: str)-> bool:
    return bcrypt.checkpw(password=password.encode(), hashed_password=hash_pw.encode())

def add_user(user_data: dict, db: Session):
    user_new = Users(**user_data)
    db.add(user_new)
    db.commit()
    db.refresh(user_new)
    
    return user_new

def transaction(user1: Users, user2: Users,amount: float, db: Session):
    setattr(user1, "balance", (user1.balance - amount))
    setattr(user2, "balance", (user2.balance + amount))
    db.commit()
    
def query_all_user(db:Session):
    return db.query(Users).all()