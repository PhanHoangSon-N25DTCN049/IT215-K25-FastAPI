from sqlalchemy.orm import Session
from app.models import ProjectModel, ProjectMembersModel, RoleProject
from app.schemas import ProjectData
from app.core import NotFoundException
from .query import query_project_member_by_id



def save_project(project_data: dict, owner_id: int, db: Session):
    project_data["owner_id"] = owner_id
    new_project = ProjectModel(**project_data)
    db.add(new_project)
    db.flush() 
    
    new_member = ProjectMembersModel(
        project_id=new_project.id,
        user_id=owner_id,
        role=RoleProject.OWNER
    )
    db.add(new_member)
    db.commit()
    
    db.refresh(new_project)
    db.refresh(new_member)
    
    return ProjectData(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        owner_id=new_project.owner_id,
        created_at=new_project.created_at,
        role_user=new_member.role
    )


def join_project(user_id: int, project_id: int, db:Session, role: RoleProject = RoleProject.MEMBER):
    new_member = ProjectMembersModel( project_id=project_id, user_id=user_id, role = role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return new_member

def update_project(data_update: dict, project: ProjectModel, db: Session):
    
    for key, value in data_update.items():
        setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    
    return project

def del_project(project: ProjectModel, db: Session):
    project.is_delete = True
    db.commit()


    
def del_user_project(project_id: int, user_id: int, db: Session):
    user = member = db.query(ProjectMembersModel).filter(
        ProjectMembersModel.project_id == project_id,
        ProjectMembersModel.user_id == user_id
    ).first()

    if user is None:
        raise NotFoundException("Không tồn tại Member cần xóa") 
    db.delete(user)
    db.commit()
    