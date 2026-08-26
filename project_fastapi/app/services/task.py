from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models import ProjectModel, ProjectMembersModel, RoleProject, TaskModel, TaskStatus, TaskPriority, CommentTaskModel
from app.schemas import ProjectData
from app.core import NotFoundException


def create_task(task_data: dict, db:Session):
    new_task = TaskModel(**task_data)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task



def get_all_task(project_id: int,
                 db: Session,
                 user_id: int = None,
                 status: TaskStatus = None,
                 priority: TaskPriority = None,
                 title: str = None,
                 page: int = 1,          
                 size: int = 10,         
                 sort_by: str = "created_at",  
                 sort_order: str = "desc"      
                 ):
    

    query = db.query(TaskModel).filter(TaskModel.project_id == project_id)
    
    if user_id is not None:
        query = query.filter(TaskModel.assignee_id == user_id)
    if status is not None:
        query = query.filter(TaskModel.status == status)
    if priority is not None:
        query = query.filter(TaskModel.priority == priority)
    if title is not None:
        query = query.filter(TaskModel.title.ilike(f"%{title}%"))

    if sort_by == "due_date":
        if sort_order == "asc":
            query = query.order_by(asc(TaskModel.due_date))
        else:
            query = query.order_by(desc(TaskModel.due_date))
    else:

        if sort_order == "asc":
            query = query.order_by(asc(TaskModel.created_at))
        else:
            query = query.order_by(desc(TaskModel.created_at))

    total_items = query.count()

 
    skip = (page - 1) * size
    tasks = query.offset(skip).limit(size).all()


    total_pages = (total_items + size - 1) // size
    
    return {
        "data": tasks,
        "meta": {
            "current_page": page,
            "page_size": size,
            "total_items": total_items,
            "total_pages": total_pages
        }
    }
    
def get_task_by_id(task_id: int, db: Session):
    return db.query(TaskModel).filter(TaskModel.id == task_id).first()

def update_task(task: TaskModel, task_data: dict, db: Session):
    
    for key, item in task_data.items():
        setattr(task, key, item)
        
    db.commit()
    db.refresh(task)
    return task
    
def del_task(task: TaskModel, db: Session):
    db.delete(task)
    db.commit()
    
def add_comment(comment_data: dict, db: Session):
    new_comment = CommentTaskModel(**comment_data)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def get_all_comment_task(task_id: int, db: Session):
    return db.query(CommentTaskModel).filter(CommentTaskModel.task_id == task_id).all()