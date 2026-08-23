import sys
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core import hash_password
from app.db import Base, engine, SessionLocal
from app.models import (
    UserModel,
    RoleUser,
    ProjectModel,
    ProjectMembersModel,
    RoleProject,
    TaskModel,
    TaskStatus,
    TaskPriority,
)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def seed_data():

    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Bắt đầu seed dữ liệu...")

        # 1. Seed Users
        users = []
        for i in range(1, 4):
            email = f"user{i}@example.com"
            user = db.query(UserModel).filter(UserModel.email == email).first()
            if not user:
                user = UserModel(
                    email=email,
                    password_hash=hash_password("string"),
                    full_name=f"Người dùng Hệ thống {i}",
                    role=RoleUser.ADMIN,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            users.append(user)

        db.commit()
        for user in users:
            db.refresh(user)

        # 2. Seed Projects
        projects = []
        for i in range(1, 3):
            project_name = f"Dự án Web {i}"
            project = db.query(ProjectModel).filter(ProjectModel.name == project_name).first()
            if not project:
                project = ProjectModel(
                    name=project_name,
                    description=f"Mô tả chi tiết cho dự án web {i}",
                    owner_id=users[0].id,
                )
                db.add(project)
                db.flush()
            projects.append(project)

        db.commit()
        for project in projects:
            db.refresh(project)

        # 3. Seed ProjectMembers
        for project in projects:
            # Gán quyền OWNER
            owner_member = db.query(ProjectMembersModel).filter(
                ProjectMembersModel.project_id == project.id,
                ProjectMembersModel.user_id == users[0].id,
            ).first()
            if not owner_member:
                owner_member = ProjectMembersModel(
                    user_id=users[0].id,
                    project_id=project.id,
                    role=RoleProject.OWNER,
                )
                db.add(owner_member)

            # Gán quyền MEMBER
            normal_member = db.query(ProjectMembersModel).filter(
                ProjectMembersModel.project_id == project.id,
                ProjectMembersModel.user_id == users[1].id,
            ).first()
            if not normal_member:
                normal_member = ProjectMembersModel(
                    user_id=users[1].id,
                    project_id=project.id,
                    role=RoleProject.MEMBER,
                )
                db.add(normal_member)

        db.commit()

        # 4. Seed Tasks
        for project in projects:
            for i in range(1, 4):
                task_title = f"Triển khai tính năng {i} của {project.name}"
                task = db.query(TaskModel).filter(
                    TaskModel.project_id == project.id,
                    TaskModel.title == task_title,
                ).first()
                if not task:
                    task = TaskModel(
                        title=task_title,
                        description=f"Cần hoàn thiện API và liên kết với Frontend cho tính năng {i}.",
                        status=random.choice([TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]),
                        priority=random.choice([TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH]),
                        due_date=datetime.now() + timedelta(days=random.randint(1, 14)),
                        project_id=project.id,
                        assignee_id=random.choice([users[0].id, users[1].id, users[2].id]),
                    )
                    db.add(task)

        db.commit()
        print("Seed dữ liệu thành công!")

    except Exception as e:
        db.rollback()
        print(f"Có lỗi xảy ra, đã rollback CSDL: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()