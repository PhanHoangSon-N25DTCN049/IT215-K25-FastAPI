# Bài tập 1

raw_cart = [
    {"id": "SP1", "ten": " Áo sơ mi nam ", "gia": 150000, "sl": 2, "danh_muc": "Thời trang"},
    {"id": "SP2", "ten": "Quần tây ", "gia": 250000, "sl": 1, "danh_muc": "Thời trang"},
    {"id": "SP3", "ten": " Giày thể thao ", "gia": 450000, "sl": 1, "danh_muc": "Giày dép"},
    {"id": "SP4", "ten": "Tất cổ ngắn ", "gia": 30000, "sl": 5, "danh_muc": "Phụ kiện"}
]

# TODO 1: Duyệt raw_cart, dùng .strip() xóa khoảng trắng ở 'ten' và tính 'tong_tien' = gia * sl
for item in raw_cart:
    item["ten"] = item["ten"].strip()
    item["tong_tien"] = item["gia"] * item["sl"]

# TODO 2: Thêm sản phẩm SP5 mới vào raw_cart
sp5 = {"id": "SP5", "ten": "Áo khoác", "gia": 320000, "sl": 1, "danh_muc": "Thời trang", "tong_tien": 320000}
raw_cart.append(sp5)

# TODO 3: Xóa sản phẩm có id == "SP4" khỏi raw_cart
raw_cart = [item for item in raw_cart if item["id"] != "SP4"]

print("Giỏ hàng sau khi xử lý Bài 1:")
for item in raw_cart:
    print(item)
    
    
# Bài tập 2
cart_processed = [
    {"id": "SP1", "ten": "Áo sơ mi nam", "gia": 150000, "sl": 2, "danh_muc": "Thời trang", "tong_tien": 300000},
    {"id": "SP2", "ten": "Quần tây", "gia": 250000, "sl": 1, "danh_muc": "Thời trang", "tong_tien": 250000},
    {"id": "SP3", "ten": "Giày thể thao", "gia": 450000, "sl": 1, "danh_muc": "Giày dép", "tong_tien": 450000},
    {"id": "SP5", "ten": "Áo khoác", "gia": 320000, "sl": 1, "danh_muc": "Thời trang", "tong_tien": 320000}
]

# TODO 1: Dùng Set lấy danh mục duy nhất:
danh_muc_set = set(item["danh_muc"] for item in cart_processed)

# TODO 2: Dùng 1 dòng List Comprehension lọc tên sản phẩm có > 200000:
sp_cao_cap = [item["ten"] for item in cart_processed if item["tong_tien"] > 200000]

print("Danh mục duy nhất (Set):", danh_muc_set)
print("Sản phẩm > 200k (List Comp):", sp_cao_cap)