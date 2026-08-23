from sqlalchemy.orm import Session
from app.models import UserModel, ProjectModel,ProjectMembersModel, RoleProject
from app.schemas import ProjectData

def save_project(project_data: dict, owner_id: int, db: Session):
    
    project_data["owner_id"] = owner_id
    
    new_project = ProjectModel(**project_data)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    member = join_project(owner_id, new_project.id, db, RoleProject.OWNER)
    
    return ProjectData(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        owner_id=new_project.owner_id,
        created_at=new_project.created_at,
        role_user= member.role
    )

def join_project(user_id: int, project_id: int, db:Session, role: RoleProject = RoleProject.MEMBER):
    new_member = ProjectMembersModel( project_id=project_id, user_id=user_id, role = role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return new_member

def update_project(data_update: dict, project: ProjectData, db: Session):
    
    for key, value in data_update.items():
        setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    
    return project

def del_project(project: ProjectModel, db: Session):
    db.delete(project)
    db.commit()
    
    