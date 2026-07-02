from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

# Dữ liệu ban đầu do hệ thống cung cấp
orders_list = [
    {"id": 1, "code": "SP001", "payment_status": "PAID", "method": "BANK_TRANSFER"},
    {"id": 2, "code": "SP002", "payment_status": "UNPAID", "method": "NONE"}
]

orders_dict = {order["id"]: order for order in orders_list}

app = FastAPI()

@app.get("/orders/{order_id}/payment")
def get_order_payment_by_id(order_id: int):
    try:
        if order_id not in orders_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Order not found!"
            )
        
        order = orders_dict[order_id]
        
        return {
            "payment_status": order["payment_status"],
            "method": order["method"]
        }
        
    except HTTPException as http_e:
        raise http_e
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           content={"detail": "Hệ thống đang gặp sự cố nội bộ. Vui lòng thử lại sau."}
        ) 