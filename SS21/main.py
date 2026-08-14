import jwt
import time
import bcrypt
import json

def hash_password(password: str) -> str:
    
    hashed_bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    return hashed_bytes.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:

    return bcrypt.checkpw(password.encode(), hashed_password.encode())


SECRET_KEY = "Akira"

ALGORITHM = "HS256"


def generate_user_token(user_id: str, username: str) -> str:

    payload = {

        "sub": user_id,

        "username": username,

        "exp": int(time.time()) + 3600  

    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


    return token

if __name__ == "__main__":
    file_path = "data.json"

    while True:
        print("""
              1. Đăng nhập
              2. Đăng Ký
              """)
        choice = input("Nhập lựa chọn của bạn: ")
        
        match choice:
            case "2":
                user_name = input("Nhập tên đăng ký: ")
                password = input("Mật khẩu đăng ký: ")
                
                with open(file_path, "r", encoding="utf-8") as file:
                    load_data = json.load(file)
                check_user_name = False
                for i in load_data:
                    if i["user_name"] == user_name:
                        print("Tài khoản đã tồn tại")
                        check_user_name = True
                        break
                
                if check_user_name:
                    continue
                
                new_user = {
                    "id": max((i["id"] for i in load_data), default=0) + 1,
                    "user_name": user_name, 
                    "password": hash_password(password)
                }
                
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(new_user, file, ensure_ascii=False, indent=4)
                
            case "1":
                user_name = input("Nhập tên đăng nhập: ")
                password = input("Mật khẩu: ")
                
                with open(file_path, "r", encoding="utf-8") as file:
                    load_data = json.load(file)
                check_login = False
                for i in load_data:
                    if i["user_name"] == user_name:
                        if verify_password(password=password, hashed_password=i[password]):
                            print("Đăng nhập thành công")
                            print("token được cấp phát: ",generate_user_token(i["id"], i["user_name"]))
                            check_login = True
                            break
                        
                if check_login:
                    print("sai thông tin đăng nhập")
                        