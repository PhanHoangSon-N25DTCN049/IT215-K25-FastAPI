@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if user is None:
        return {
            "success": False,
            "message": "Email không tồn tại"
        }

    if data.password != user.password:
        return {
            "success": False,
            "message": "Mật khẩu không chính xác"
        }

    token = jwt.encode(
        {
            "email": user.email,
            "password": user.password,
            "role": user.role
        },
        "123456",
        algorithm="HS256"
    )

    return {
        "success": True,
        "access_token": token
    }
    
    
"""
Vấn đề: Mật khẩu được so sánh trực tiếp   
Nguy cơ:Có thể đang lưu mật khẩu dạng plaintext trong cơ sở dữ liệu. Nếu CSDL bị tấn công, toàn bộ mật khẩu người dùng sẽ bị lộ.
Cách khắc phục: Sử dụng thư viện băm mật khẩu (như Bcrypt) để băm mật khẩu khi đăng ký và dùng hàm verify để kiểm tra khi đăng nhập.

Vấn đề: Thông báo lỗi quá chi tiết ("Email không tồn tại" / "Mật khẩu không chính xác")  
Nguy cơ: Dẫn đến lỗ hổng User Enumeration (Dò tìm tài khoản). Kẻ tấn công có thể thử các email khác nhau để biết email nào đã được đăng ký trên hệ thống.
Cách khắc phục: Sử dụng một thông báo lỗi chung cho cả hai trường hợp: "Email hoặc mật khẩu không chính xác". Đồng thời trả về mã lỗi HTTP 401 Unauthorized thay vì return success: False

Vấn đề: Secret Key của JWT bị hardcode và quá yếu ("123456")
Nguy cơ: Kẻ tấn công có thể dễ dàng đoán được mã bí mật (brute-force) và tự tạo ra các token giả mạo để chiếm quyền truy cập của bất kỳ người dùng nào.
Cách khắc phục: Lưu Secret Key trong biến môi trường (Environment Variables - .env) và sử dụng một chuỗi ngẫu nhiên dài, phức tạp.

Vấn đề: Đưa dữ liệu nhạy cảm (password) vào JWT Payload
Nguy cơ: JWT chỉ được encode (Base64) chứ không mã hóa. Bất kỳ ai chặn bắt được token đều có thể dễ dàng decode và đọc được mật khẩu của người dùng.
Cách khắc phục: Tuyệt đối không đưa mật khẩu hay thông tin nhạy cảm vào JWT. Chỉ nên đưa các định danh như user_id, email hoặc role.

Vấn đề: JWT không có thời hạn (Thiếu claim exp)
Nguy cơ: Token được tạo ra sẽ có giá trị vĩnh viễn. Nếu token bị đánh cắp (qua XSS hoặc chặn bắt mạng), hacker có thể sử dụng token đó mãi mãi.
Cách khắc phục: Thêm thời gian hết hạn (exp - expiration time) vào payload của JWT (ví dụ: 30 phút hoặc 1 tiếng sau khi cấp).

"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
import os



@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()


    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )


    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-secret-key-for-dev-only")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    

    payload = {
        "sub": user.email, 
        "role": user.role,
        "exp": expire       
    }


    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer"
    }