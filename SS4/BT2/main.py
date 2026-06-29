from fastapi import FastAPI
app = FastAPI()
orders = [
    {"id": 1, "customer_name": "Nguyễn Văn An", "total": 250000, "status": "pending"},
    {"id": 2, "customer_name": "Trần Thị Bình", "total": 500000, "status": "paid"},
    {"id": 3, "customer_name": "Lê Văn Cường", "total": 150000, "status": "cancelled"},
    {"id": 4, "customer_name": "Phạm Thị Dung", "total": 320000, "status": "pending"}
]

#code chỉ mới trả về dữ liệu chứ dữ liệu chưa được kiểm tra và sàng lọc
@app.get("/orders/status/{status}")
def get_orders_by_status(status: str):
    if status not in ("pending","paid","cancelled"):
        return {
            "message": "Trạng thái không hợp lệ"
        }
    list_orders = [b for b in orders if b["status"] == status]
    return list_orders