from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
app = FastAPI()

@app.get("/database/health")
def get_health_db(db: Session = Depends(get_db)):
    try:
        db.connection()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi kết nối database")
    return {
        "message": "Kết nối database thành công"
    }