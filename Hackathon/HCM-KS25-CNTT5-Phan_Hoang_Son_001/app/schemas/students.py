from pydantic import BaseModel, Field, field_validator

class CreateStudent(BaseModel):
    full_name: str
    class_name: str
    email: str
    phone_number: str
    
    @field_validator("full_name", "class_name", "email", "phone_number")
    @classmethod
    def validate_strip(cls, value:str):
        value = value.strip()
        if not value:
            raise ValueError("Không được bỏ trống")
        return value
    
    