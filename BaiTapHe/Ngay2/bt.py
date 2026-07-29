students_score = [
    {"name": "An", "gpa": 7.5},
    {"name": "Bình", "gpa": 6.2},
    {"name": "Cường", "gpa": 4.8},
    {"name": "Dũng", "gpa": 8.0}
]

# TODO 1: Khởi tạo cờ all_passed ban đầu là True
all_passed = True

# TODO 2: Duyệt danh sách, nếu phát hiện gpa < 5.0 thì đổi cờ thành False
for s in students_score:
    if s["gpa"] < 5.0:
        all_passed = False

print("Tất cả sinh viên đều qua môn:", all_passed)



# Bài tập 2
orders = [15000000, 5000000, 22000000, 800000, 12000000]

# TODO 1: Khởi tạo biến tích lũy tổng doanh thu và biến đếm đơn VIP
total_revenue = 0
vip_count = 0

for price in orders:
    total_revenue += price
    if price > 10000000:
        vip_count += 1

print(f"Tổng doanh thu: {total_revenue:,} VNĐ")
print(f"Số đơn VIP: {vip_count} đơn")