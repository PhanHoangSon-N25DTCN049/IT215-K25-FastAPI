from sqlalchemy.orm import Session
from app.models import UserModel

def register(user_data: dict, db: Session):
    new_user = UserModel(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user



def save_refresh_token(user: UserModel, refresh_token: str, db: Session):
    setattr(user, "refresh_token", refresh_token)
    setattr(user, "is_revoked", False)
    db.commit()
    