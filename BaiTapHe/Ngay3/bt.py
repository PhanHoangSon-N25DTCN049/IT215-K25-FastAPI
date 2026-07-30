inventory = [
    {"id": "SP1", "ten": "Tai nghe Sony", "gia": 1200000, "danh_muc": "Phụ kiện"},
    {"id": "SP2", "ten": "Chuột không dây", "gia": 450000, "danh_muc": "Phụ kiện"},
    {"id": "SP3", "ten": "Bàn phím cơ", "gia": 950000, "danh_muc": "Phụ kiện"},
    {"id": "SP4", "ten": "Màn hình Dell", "gia": 3500000, "danh_muc": "Thiết bị"}
]

# TODO 1: SV thay dấu ... bằng điều kiện lọc gia <= 1000000 và danh_muc == "Phụ kiện"
filtered_items = []
for item in inventory:
    if item["gia"] <= 1000000 and item["danh_muc"] == "Phụ kiện":
        filtered_items.append(item["ten"])

print("Sản phẩm Phụ kiện <= 1 triệu:", filtered_items)

# Bài tập 2

students = [
    {"name": "An", "gpa": 7.2},
    {"name": "Bình", "gpa": 9.5},
    {"name": "Cường", "gpa": 6.8},
    {"name": "Dũng", "gpa": 8.4}
]

# TODO 1: SV thay dấu ... để sắp xếp GIẢM DẦN theo gpa (So sánh gpa[j] < gpa[j+1])
n = len(students)
for i in range(n):
    for j in range(0, n - i - 1):
        if students[j]["gpa"] < students[j + 1]["gpa"]:
            students[j], students[j + 1] = students[j + 1], students[j]

print("Bảng xếp hạng sinh viên (GPA Giảm Dần):")
for s in students:
    print(f"  -> {s['name']}: {s['gpa']} điểm")