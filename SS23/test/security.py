from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from database import get_db
import models
import jwt

SECRET_KEY = "kanezukiakira"
ALGORITHM = "HS256"
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:

    """
    Dependency cốt lõi: Giải mã JWT từ Header, kiểm tra tính toàn vẹn,
    và truy vấn thông tin User từ cơ sở dữ liệu MySQL.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập!",
        headers={"WWW-Authenticate": "Bearer"},

    )
   
    try:

        # Bước 1: Giải mã Token bằng khóa bí mật
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        raise credentials_exception
    # Bước 2: Truy vấn thông tin người dùng từ MySQL thông qua SQLAlchemy ORM
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Người dùng không tồn tại trên hệ thống!"
        )
       
    # Bước 3: Kiểm tra xem tài khoản có đang bị khóa hay không

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Tài khoản này đã bị tạm khóa!"
        )

    # Trả về đối tượng người dùng hoàn chỉnh cho endpoint kế tiếp

    return user
