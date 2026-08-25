from sqlalchemy.orm import Session
from app.models import UserModel, ProjectMembersModel, ProjectModel, RoleProject
from app.schemas import ProjectData

def query_user_by_id(id:int, db: Session):
    user = db.query(UserModel).filter(UserModel.id == id).first()
    if not user:
        return None
    return user

def query_user_by_gmail(email: str, db:Session):
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        return None
    return user  


def query_user_by_admin(db: Session, name: str = None, email: str = None, status: bool = None):
    query = db.query(UserModel)
    
    if name:
        query = query.filter(UserModel.full_name.ilike(f"%{name}%"))
    if email:
        query = query.filter(UserModel.email.ilike(f"%{email}%"))
    if status is not None:
        query = query.filter(UserModel.is_active == status)
    return query.all()

def query_project_join(user_id: int, db: Session, search: str = None):
    query = db.query(ProjectMembersModel).join(ProjectModel).filter(ProjectMembersModel.user_id == user_id)
    if search is not None:
        query = query.filter(ProjectModel.name.ilike(f"%{search}%"))
    
    memberships = query.all()
    
    result = []
    for member in memberships:
        proj = member.project
        result.append(ProjectData(
            id=proj.id,
            name=proj.name,
            description=proj.description,
            owner_id=proj.owner_id,
            created_at=proj.created_at,
            role_user=member.role
        ))
        
    return result

def query_project_by_id(db: Session, id: int, id_user_query: int):
    project = db.query(ProjectModel).filter(ProjectModel.id == id).first()
    
    return ProjectData(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        role_user=RoleProject.OWNER if id_user_query == project.owner_id else RoleProject.MEMBER
    )

def query_project_member_by_id(id: int, db:Session):
    return db.query(ProjectMembersModel).filter(ProjectMembersModel.id == id).first()

def query_all_project_member(project_id: Session, db: Session):
    return db.query(ProjectMembersModel).filter(ProjectMembersModel.project_id == project_id).all()