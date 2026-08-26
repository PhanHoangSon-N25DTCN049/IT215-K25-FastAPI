import sys
import argparse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
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
    CommentTaskModel,
    ActivityLogModel,
)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def reset_database(db: Session):
    """Xóa sạch dữ liệu cũ theo đúng thứ tự ràng buộc khóa ngoại."""
    print("Đang dọn dẹp dữ liệu cũ...")
    # Tắt kiểm tra khóa ngoại tạm thời để truncate/delete an toàn
    db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    db.execute(text("TRUNCATE TABLE task_comment;"))
    db.execute(text("TRUNCATE TABLE activity_logs;"))
    db.execute(text("TRUNCATE TABLE tasks;"))
    db.execute(text("TRUNCATE TABLE project_members;"))
    db.execute(text("TRUNCATE TABLE projects;"))
    db.execute(text("TRUNCATE TABLE users;"))
    db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    db.commit()
    print("Đã làm sạch cơ sở dữ liệu thành công!")


def seed_data(reset: bool = False):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        if reset:
            reset_database(db)

        print("=" * 70)
        print(">>> BẮT ĐẦU SEED DỮ LIỆU MẪU CHO DỰ ÁN FASTAPI <<<")
        print("=" * 70)

        # -------------------------------------------------------------
        # 1. SEED USERS
        # -------------------------------------------------------------
        default_pwd = hash_password("Password123@")
        
        users_data = [
            # Quản trị viên
            {
                "email": "admin@fastapi.dev",
                "full_name": "Quản Trị Viên Hệ Thống",
                "role": RoleUser.ADMIN,
                "is_active": True,
            },
            # Tech Lead / Project Managers
            {
                "email": "son.phan@example.com",
                "full_name": "Phan Hoàng Sơn",
                "role": RoleUser.USER,
                "is_active": True,
            },
            {
                "email": "lan.nguyen@example.com",
                "full_name": "Nguyễn Thị Mai Lan",
                "role": RoleUser.USER,
                "is_active": True,
            },
            # Developers
            {
                "email": "nam.tran@example.com",
                "full_name": "Trần Văn Nam",
                "role": RoleUser.USER,
                "is_active": True,
            },
            {
                "email": "huong.le@example.com",
                "full_name": "Lê Thu Hương",
                "role": RoleUser.USER,
                "is_active": True,
            },
            {
                "email": "minh.vu@example.com",
                "full_name": "Vũ Tuấn Minh",
                "role": RoleUser.USER,
                "is_active": True,
            },
            # QA / Testers
            {
                "email": "duc.hoang@example.com",
                "full_name": "Hoàng Minh Đức",
                "role": RoleUser.USER,
                "is_active": True,
            },
            {
                "email": "trang.do@example.com",
                "full_name": "Đỗ Quỳnh Trang",
                "role": RoleUser.USER,
                "is_active": True,
            },
            # Inactive User (Phục vụ test tài khoản bị khóa)
            {
                "email": "khoa.dang@example.com",
                "full_name": "Đặng Anh Khoa",
                "role": RoleUser.USER,
                "is_active": False,
            },
            # Tài khoản mẫu chuẩn (Tương thích ngược)
            {
                "email": "user1@example.com",
                "full_name": "Người Dùng Mẫu 1",
                "role": RoleUser.ADMIN,
                "is_active": True,
            },
            {
                "email": "user2@example.com",
                "full_name": "Người Dùng Mẫu 2",
                "role": RoleUser.USER,
                "is_active": True,
            },
            {
                "email": "user3@example.com",
                "full_name": "Người Dùng Mẫu 3",
                "role": RoleUser.USER,
                "is_active": True,
            },
        ]

        users_map = {}
        for u_data in users_data:
            user = db.query(UserModel).filter(UserModel.email == u_data["email"]).first()
            if not user:
                user = UserModel(
                    email=u_data["email"],
                    password_hash=default_pwd,
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    is_active=u_data["is_active"],
                )
                db.add(user)
                db.flush()
            users_map[u_data["email"]] = user

        db.commit()
        for email in users_map:
            db.refresh(users_map[email])

        print(f"[+] Đã khởi tạo {len(users_map)} người dùng (Tất cả mật khẩu: Password123@)")

        # -------------------------------------------------------------
        # 2. SEED PROJECTS
        # -------------------------------------------------------------
        projects_data = [
            {
                "name": "Hệ thống E-Commerce & Bán hàng Đa kênh",
                "description": "Nền tảng thương mại điện tử tích hợp cổng thanh toán VNPay/Momo, quản lý tồn kho thời gian thực và đồng bộ đơn hàng đa kênh.",
                "owner_email": "son.phan@example.com",
                "created_days_ago": 30,
                "members": [
                    {"email": "son.phan@example.com", "role": RoleProject.OWNER},
                    {"email": "nam.tran@example.com", "role": RoleProject.MEMBER},
                    {"email": "huong.le@example.com", "role": RoleProject.MEMBER},
                    {"email": "duc.hoang@example.com", "role": RoleProject.MEMBER},
                    {"email": "admin@fastapi.dev", "role": RoleProject.MEMBER},
                ],
                "tasks": [
                    {
                        "title": "Thiết kế cơ sở dữ liệu và ERD Diagram",
                        "description": "Xác định bảng Users, Products, Orders, OrderItems, Payments và quan hệ khóa ngoại.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -15,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "nam.tran@example.com", "content": "Đã hoàn thành file db_schema.sql và ERD diagram trên dbdiagram.io."},
                            {"user_email": "son.phan@example.com", "content": "Thiết kế hợp lý, đã duyệt để team bắt đầu viết migration models."},
                        ]
                    },
                    {
                        "title": "Xây dựng RESTful API Xác thực & Phân quyền JWT",
                        "description": "Viết API /auth/register, /auth/login, /auth/refresh với JWT Access/Refresh Token và Bcrypt hashing.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -10,
                        "assignee_email": "son.phan@example.com",
                        "comments": [
                            {"user_email": "son.phan@example.com", "content": "Đã tích hợp bảo vệ rate limiting cho endpoint /auth/login bằng slowapi."},
                            {"user_email": "duc.hoang@example.com", "content": "QA đã test thử các trường hợp sai mật khẩu, brute-force và token hết hạn. Hoạt động chính xác."},
                        ]
                    },
                    {
                        "title": "Tích hợp Cổng thanh toán trực tuyến VNPay Sandbox",
                        "description": "Tạo URL thanh toán bảo mật với mã hóa SHA512 HMAC và xử lý IPN Webhook callback.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.HIGH,
                        "days_due": 3,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "nam.tran@example.com", "content": "Đã kết nối thành công môi trường sandbox, đang hoàn thiện hàm kiểm tra chữ ký checksum IPN."},
                        ]
                    },
                    {
                        "title": "Xây dựng Giao diện Giỏ hàng & Thanh toán (Frontend)",
                        "description": "Phát triển trang Checkout Responsive, quản lý state giỏ hàng, tích hợp form địa chỉ giao hàng.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 5,
                        "assignee_email": "huong.le@example.com",
                        "comments": [
                            {"user_email": "huong.le@example.com", "content": "Đang kết nối API với backend, giao diện responsive đã test mượt mà trên mobile."},
                        ]
                    },
                    {
                        "title": "Viết Test tự động & Kiểm thử Tải (Load Testing)",
                        "description": "Viết bộ test pytest cho toàn bộ API luồng đặt hàng và chạy test tải mô phỏng 500 CCU.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.LOW,
                        "days_due": 14,
                        "assignee_email": "duc.hoang@example.com",
                        "comments": []
                    },
                ]
            },
            {
                "name": "Ứng dụng Di động Đặt món & Giao hàng Siêu tốc",
                "description": "Ứng dụng di động đặt đồ ăn và thức uống, tích hợp bản đồ định vị GPS theo dõi shipper và tính năng săn voucher khuyến mãi.",
                "owner_email": "lan.nguyen@example.com",
                "created_days_ago": 20,
                "members": [
                    {"email": "lan.nguyen@example.com", "role": RoleProject.OWNER},
                    {"email": "minh.vu@example.com", "role": RoleProject.MEMBER},
                    {"email": "huong.le@example.com", "role": RoleProject.MEMBER},
                    {"email": "trang.do@example.com", "role": RoleProject.MEMBER},
                ],
                "tasks": [
                    {
                        "title": "Thiết kế UI/UX App Mobile trên Figma",
                        "description": "Thiết kế đầy đủ luồng người dùng: Màn hình Home, Tìm kiếm nhà hàng, Giỏ món ăn, Theo dõi đơn giao hàng.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -5,
                        "assignee_email": "lan.nguyen@example.com",
                        "comments": [
                            {"user_email": "lan.nguyen@example.com", "content": "Đã bàn giao file Figma cho team Frontend và Mobile dev."},
                        ]
                    },
                    {
                        "title": "API Tìm kiếm & Phân loại Nhà hàng theo Khoảng cách GPS",
                        "description": "Tính toán tọa độ Haversine giữa vị trí khách hàng và nhà hàng gần nhất trong bán kính 5km.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.HIGH,
                        "days_due": 4,
                        "assignee_email": "minh.vu@example.com",
                        "comments": [
                            {"user_email": "minh.vu@example.com", "content": "Đã bổ sung index vị trí địa lý trên database để tăng tốc độ truy vấn."},
                        ]
                    },
                    {
                        "title": "Tính năng Áp dụng Mã giảm giá & Flash Sale Voucher",
                        "description": "Kiểm tra điều kiện đơn hàng tối thiểu, số lượng voucher khả dụng và tính toán mức chiết khấu tối đa.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 8,
                        "assignee_email": "minh.vu@example.com",
                        "comments": []
                    },
                    {
                        "title": "Kiểm thử Chức năng Đặt món & Huỷ đơn trên thiết bị thật",
                        "description": "Test các case hủy đơn trước và sau khi shipper nhận cuốc, kiểm tra hoàn tiền ví.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 12,
                        "assignee_email": "trang.do@example.com",
                        "comments": []
                    },
                ]
            },
            {
                "name": "Nền tảng Quản trị Nhân sự & Chấm công HRM",
                "description": "Giải pháp chuyển đổi số nhân sự toàn diện: chấm công AI, quản lý KPI, tính lương tự động và xét duyệt nghỉ phép trực tuyến.",
                "owner_email": "admin@fastapi.dev",
                "created_days_ago": 45,
                "members": [
                    {"email": "admin@fastapi.dev", "role": RoleProject.OWNER},
                    {"email": "lan.nguyen@example.com", "role": RoleProject.MEMBER},
                    {"email": "son.phan@example.com", "role": RoleProject.MEMBER},
                    {"email": "nam.tran@example.com", "role": RoleProject.MEMBER},
                ],
                "tasks": [
                    {
                        "title": "Phân tích Nghiệp vụ Tính Lương & BHYT/BHXH Theo Luật Lao Động",
                        "description": "Xây dựng công thức tính thuế thu nhập cá nhân, trích nộp bảo hiểm và các khoản phụ cấp lương.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -20,
                        "assignee_email": "lan.nguyen@example.com",
                        "comments": [
                            {"user_email": "lan.nguyen@example.com", "content": "Đã thống nhất biểu mẫu bảng lương với phòng Kế toán & HR."},
                        ]
                    },
                    {
                        "title": "Module Đơn Xin Nghỉ Phép & Luồng Duyệt Đa Cấp",
                        "description": "Nhân viên tạo đơn -> Quản lý trực tiếp duyệt -> Trưởng phòng HR phê duyệt lần cuối.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": -7,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "nam.tran@example.com", "content": "Đã cấu hình gửi thông báo email tự động khi đơn được duyệt."},
                        ]
                    },
                    {
                        "title": "Báo cáo Thống kê Đi muộn & Hiệu suất Nhân sự theo Tháng",
                        "description": "Tổng hợp dữ liệu chấm công từ máy chấm công vân tay/nhận diện khuôn mặt để xuất file Excel báo cáo.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 6,
                        "assignee_email": "son.phan@example.com",
                        "comments": []
                    },
                    {
                        "title": "Tích hợp Đăng nhập Một lần SSO (Single Sign-On)",
                        "description": "Tích hợp giao thức OAuth2 Google Workspace và Microsoft Azure AD cho tài khoản công ty.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.LOW,
                        "days_due": 18,
                        "assignee_email": "admin@fastapi.dev",
                        "comments": []
                    },
                ]
            },
            {
                "name": "Cổng Hỗ trợ Khách hàng & Helpdesk 24/7",
                "description": "Hệ thống tiếp nhận, phân loại và xử lý ticket tự động đa kênh (Email, Chat, Hotline), tích hợp AI Chatbot trả lời tự động.",
                "owner_email": "son.phan@example.com",
                "created_days_ago": 15,
                "members": [
                    {"email": "son.phan@example.com", "role": RoleProject.OWNER},
                    {"email": "minh.vu@example.com", "role": RoleProject.MEMBER},
                    {"email": "trang.do@example.com", "role": RoleProject.MEMBER},
                    {"email": "user2@example.com", "role": RoleProject.MEMBER},
                ],
                "tasks": [
                    {
                        "title": "Xây dựng Ticket Routing Engine tự động phân công Kỹ thuật viên",
                        "description": "Phân chia ticket theo danh mục (Lỗi kỹ thuật, Hỏi đáp, Khiếu nại) và độ ưu tiên SLA.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.HIGH,
                        "days_due": 2,
                        "assignee_email": "minh.vu@example.com",
                        "comments": [
                            {"user_email": "minh.vu@example.com", "content": "Đang hoàn thiện thuật toán phân bổ Round-Robin cân bằng tải nhân sự."},
                        ]
                    },
                    {
                        "title": "Dashboard Thống kê Thời gian Phản hồi Đầu tiên (FRT) và SLA",
                        "description": "Hiển thị biểu đồ realtime về tỷ lệ vi phạm SLA và điểm đánh giá hài lòng khách hàng (CSAT).",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 10,
                        "assignee_email": "minh.vu@example.com",
                        "comments": []
                    },
                    {
                        "title": "Tích hợp Webhook đồng bộ tin nhắn Fanpage Facebook & Zalo OA",
                        "description": "Nhận tin nhắn khách hàng gửi từ Fanpage và chuyển thành ticket hỗ trợ tự động.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.LOW,
                        "days_due": 15,
                        "assignee_email": "son.phan@example.com",
                        "comments": []
                    },
                ]
            },
            {
                "name": "Hạ tầng DevOps, Docker & CI/CD Pipeline",
                "description": "Chuẩn hóa quy trình triển khai ứng dụng, tự động hóa build & test với GitHub Actions, container hóa Docker và giám sát.",
                "owner_email": "nam.tran@example.com",
                "created_days_ago": 25,
                "members": [
                    {"email": "nam.tran@example.com", "role": RoleProject.OWNER},
                    {"email": "son.phan@example.com", "role": RoleProject.MEMBER},
                    {"email": "duc.hoang@example.com", "role": RoleProject.MEMBER},
                    {"email": "admin@fastapi.dev", "role": RoleProject.MEMBER},
                ],
                "tasks": [
                    {
                        "title": "Viết Dockerfile đa tầng (Multi-stage Build) tối ưu kích thước image",
                        "description": "Tối ưu hóa Docker image cho FastAPI app từ 1GB xuống dưới 150MB, loại bỏ cache rác.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -12,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "nam.tran@example.com", "content": "Đã test build docker image thành công, kích thước cuối chỉ còn 128MB."},
                            {"user_email": "son.phan@example.com", "content": "Tốt lắm, image nhẹ sẽ giúp pull và deploy lên staging cực nhanh."},
                        ]
                    },
                    {
                        "title": "Cấu hình GitHub Actions CI Workflow tự động chạy Pytest",
                        "description": "Tự động kích hoạt test và linting (flake8/black) mỗi khi có Pull Request vào nhánh develop hoặc main.",
                        "status": TaskStatus.DONE,
                        "priority": TaskPriority.HIGH,
                        "days_due": -8,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "duc.hoang@example.com", "content": "Workflow CI chạy rất ổn định, thời gian chạy toàn bộ 79 tests chỉ mất ~30s."},
                        ]
                    },
                    {
                        "title": "Thiết lập Giám sát Hệ thống với Prometheus & Grafana",
                        "description": "Theo dõi các chỉ số CPU, RAM, Latency API p95/p99, tỷ lệ lỗi 5xx và gửi cảnh báo về kênh Slack/Telegram.",
                        "status": TaskStatus.IN_PROGRESS,
                        "priority": TaskPriority.MEDIUM,
                        "days_due": 7,
                        "assignee_email": "nam.tran@example.com",
                        "comments": [
                            {"user_email": "nam.tran@example.com", "content": "Đã dựng xong cụm Grafana và import dashboard FastAPI Metrics."},
                        ]
                    },
                    {
                        "title": "Xây dựng Script Tự động Sao lưu Cơ sở dữ liệu Định kỳ",
                        "description": "Lập lịch cronjob tự động dump CSDL MySQL hàng ngày lúc 02:00 AM và upload lên Cloud Storage an toàn.",
                        "status": TaskStatus.TODO,
                        "priority": TaskPriority.LOW,
                        "days_due": 16,
                        "assignee_email": "son.phan@example.com",
                        "comments": []
                    },
                ]
            }
        ]

        total_tasks_count = 0
        total_comments_count = 0
        total_logs_count = 0

        for p_data in projects_data:
            owner = users_map[p_data["owner_email"]]
            created_at_proj = datetime.now() - timedelta(days=p_data["created_days_ago"])
            
            project = db.query(ProjectModel).filter(ProjectModel.name == p_data["name"]).first()
            if not project:
                project = ProjectModel(
                    name=p_data["name"],
                    description=p_data["description"],
                    owner_id=owner.id,
                    created_at=created_at_proj,
                )
                db.add(project)
                db.flush()
            else:
                project.description = p_data["description"]
                project.owner_id = owner.id
                db.flush()

            # Seed Activity: Project Created
            proj_create_log = db.query(ActivityLogModel).filter(
                ActivityLogModel.project_id == project.id,
                ActivityLogModel.action == "CREATE_PROJECT"
            ).first()
            if not proj_create_log:
                log_entry = ActivityLogModel(
                    project_id=project.id,
                    user_id=owner.id,
                    action="CREATE_PROJECT",
                    details={"name": project.name, "description": project.description},
                    created_at=created_at_proj,
                )
                db.add(log_entry)
                total_logs_count += 1

            # Seed Members
            for m_data in p_data["members"]:
                member_user = users_map[m_data["email"]]
                pm = db.query(ProjectMembersModel).filter(
                    ProjectMembersModel.project_id == project.id,
                    ProjectMembersModel.user_id == member_user.id
                ).first()
                if not pm:
                    pm = ProjectMembersModel(
                        project_id=project.id,
                        user_id=member_user.id,
                        role=m_data["role"],
                        joined_at=created_at_proj + timedelta(days=1),
                    )
                    db.add(pm)
                    
                    if m_data["role"] != RoleProject.OWNER:
                        log_mem = ActivityLogModel(
                            project_id=project.id,
                            user_id=owner.id,
                            action="ADD_MEMBER",
                            details={"user_id": member_user.id, "user_name": member_user.full_name, "role": m_data["role"].value},
                            created_at=created_at_proj + timedelta(days=1),
                        )
                        db.add(log_mem)
                        total_logs_count += 1

            # Seed Tasks
            for t_data in p_data["tasks"]:
                assignee = users_map.get(t_data["assignee_email"])
                task = db.query(TaskModel).filter(
                    TaskModel.project_id == project.id,
                    TaskModel.title == t_data["title"]
                ).first()
                
                due_date_val = datetime.now() + timedelta(days=t_data["days_due"])
                task_created_at = created_at_proj + timedelta(days=2)

                if not task:
                    task = TaskModel(
                        project_id=project.id,
                        title=t_data["title"],
                        description=t_data["description"],
                        assignee_id=assignee.id if assignee else None,
                        status=t_data["status"],
                        priority=t_data["priority"],
                        due_date=due_date_val,
                        created_at=task_created_at,
                    )
                    db.add(task)
                    db.flush()
                    total_tasks_count += 1

                    # Log task creation
                    log_task = ActivityLogModel(
                        project_id=project.id,
                        user_id=owner.id,
                        action="CREATE_TASK",
                        details={
                            "task_id": task.id,
                            "title": task.title,
                            "priority": task.priority.value,
                            "assignee": assignee.full_name if assignee else "Chưa gán"
                        },
                        created_at=task_created_at,
                    )
                    db.add(log_task)
                    total_logs_count += 1

                    # If status updated or done, add log
                    if task.status != TaskStatus.TODO:
                        log_status = ActivityLogModel(
                            project_id=project.id,
                            user_id=assignee.id if assignee else owner.id,
                            action="UPDATE_TASK_STATUS",
                            details={
                                "task_id": task.id,
                                "task_title": task.title,
                                "old_status": TaskStatus.TODO.value,
                                "new_status": task.status.value,
                            },
                            created_at=task_created_at + timedelta(days=2),
                        )
                        db.add(log_status)
                        total_logs_count += 1

                # Seed Comments
                for c_data in t_data.get("comments", []):
                    c_user = users_map[c_data["user_email"]]
                    comment = db.query(CommentTaskModel).filter(
                        CommentTaskModel.task_id == task.id,
                        CommentTaskModel.content == c_data["content"]
                    ).first()
                    if not comment:
                        comment = CommentTaskModel(
                            task_id=task.id,
                            user_id=c_user.id,
                            content=c_data["content"],
                            created_at=task_created_at + timedelta(days=3),
                        )
                        db.add(comment)
                        total_comments_count += 1

        db.commit()

        print(f"[+] Đã khởi tạo {len(projects_data)} dự án thực tế.")
        print(f"[+] Đã khởi tạo {total_tasks_count} công việc (tasks) đa dạng trạng thái và độ ưu tiên.")
        print(f"[+] Đã khởi tạo {total_comments_count} thảo luận/bình luận (comments) chi tiết.")
        print(f"[+] Đã khởi tạo {total_logs_count} nhật ký hoạt động (activity logs) của dự án.")
        print("=" * 70)
        print(">>> TỔNG HỢP TÀI KHOẢN MẪU ĐỂ ĐĂNG NHẬP / TEST API <<<")
        print("=" * 70)
        print(f"{'Email':<30} | {'Họ và Tên':<25} | {'Vai trò':<8} | {'Mật khẩu'}")
        print("-" * 75)
        for u in users_data:
            role_str = "ADMIN" if u["role"] == RoleUser.ADMIN else "USER"
            active_str = "" if u["is_active"] else " (ĐÃ KHÓA)"
            print(f"{u['email']:<30} | {u['full_name'] + active_str:<25} | {role_str:<8} | Password123@")
        print("=" * 70)
        print("SEED DỮ LIỆU THÀNH CÔNG VÀ SẴN SÀNG SỬ DỤNG!")

    except Exception as e:
        db.rollback()
        print(f"[!] Có lỗi xảy ra trong quá trình seed dữ liệu: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed dữ liệu mẫu cho hệ thống FastAPI.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Xóa sạch toàn bộ dữ liệu cũ trước khi nạp dữ liệu mẫu mới.",
    )
    args = parser.parse_args()
    seed_data(reset=args.reset)