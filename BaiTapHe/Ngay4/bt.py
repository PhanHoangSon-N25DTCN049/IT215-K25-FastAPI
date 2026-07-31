def validate_registration_input(name, email, phone):
    clean_name = name.strip()
    clean_email = email.strip().lower()
    clean_phone = phone.strip()
    
    # TODO 1: Kiểm tra email chứa ký tự @
    is_email_valid = "@" in clean_email
    
    # TODO 2: Kiểm tra SĐT (10 chữ số, toàn số, đầu 03/05/07/08/09)
    valid_prefixes = ("03", "05", "07", "08", "09")
    is_phone_valid = (len(clean_phone) == 10) and clean_phone.isdigit() and clean_phone.startswith(valid_prefixes)
    
    return clean_name, clean_email, is_email_valid, clean_phone, is_phone_valid

# Dữ liệu kiểm thử
registers = [
    {"name": "  Nguyen Van An  ", "email": "an.nguyen@gmail.com", "phone": "0987654321"},
    {"name": "Tran Thi Bich", "email": "bich_gmail.com", "phone": "0912345678"},
    {"name": "Le Hoang Cuong", "email": "cuong@rikkei.edu.vn", "phone": "0123456789"}
]

print("=== BÁO CÁO KẾT QUẢ VALIDATE THÔNG TIN ===")
for r in registers:
    c_n, c_e, e_ok, c_p, p_ok = validate_registration_input(r["name"], r["email"], r["phone"])
    status = "✅ HỢP LỆ" if (e_ok and p_ok) else "❌ KHÔNG HỢP LỆ"
    print(f"[{c_n}] Email: {c_e} | SDT: {c_p} -> {status}")

#Bai Tap 2

def safe_process_invoice(order_id, raw_total, discount_code, is_vip):
    try:
        # TODO 1: Ép kiểu float(raw_total)
        subtotal = float(raw_total)
        
        # TODO 2: Tính chiết khấu VIP
        discount_rate = 0.0
        if is_vip and discount_code == "VIP10":
            discount_rate = 0.10
        elif is_vip and discount_code == "VIP20":
            discount_rate = 0.20
            
        subtotal_after_discount = subtotal * (1 - discount_rate)
        vat = subtotal_after_discount * 0.10
        final_total = subtotal_after_discount + vat
        
        tier = "HÓA ĐƠN LỚN (VIP)" if final_total >= 10000000 else "HÓA ĐƠN THƯỜNG"
        return final_total, tier
        
    except ValueError:
        print(f"⚠️ Xử lý lỗi [{order_id}]: Số tiền '{raw_total}' không hợp lệ! Bỏ qua đơn hàng.")
        return None, "LỖI"

orders = [
    {"id": "DH01", "total": "12500000", "discount_code": "VIP10", "is_vip": True},
    {"id": "DH02", "total": "450000", "discount_code": "INVALID", "is_vip": False},
    {"id": "DH03", "total": "ABC_ERROR", "discount_code": "", "is_vip": False}
]

print("=== BÁO CÁO THỰC THI HÓA ĐƠN ===")
for o in orders:
    tot, t = safe_process_invoice(o["id"], o["total"], o["discount_code"], o["is_vip"])
    if tot:
        print(f"[{o['id']}] Tổng thanh toán: {tot:,.0f} VNĐ [{t}]")
