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