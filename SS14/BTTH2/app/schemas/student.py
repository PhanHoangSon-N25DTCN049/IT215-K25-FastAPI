from pydantic import BaseModel

class Student(BaseModel):
    full_name: str
    email: str
    major: str
    gpa: float
    
