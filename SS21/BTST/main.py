"""
2.1. Chính sách mật khẩu
Độ dài tối thiểu: Bắt buộc từ 8 ký tự trở lên.

Yêu cầu độ phức tạp: Phải bao gồm ít nhất 1 chữ cái in hoa, 1 chữ cái in thường, 1 chữ số và 1 ký tự đặc biệt (ví dụ: @, #, $, !).

Sử dụng lại mật khẩu: Không cho phép người dùng đổi lại mật khẩu trùng với 3 mật khẩu đã được sử dụng gần nhất.

Xử lý khi nhập sai: Khóa chức năng đăng nhập tạm thời sau 5 lần nhập sai liên tiếp để chống tấn công brute-force.

2.2. Chính sách Access Token
Thời gian tồn tại: Thiết lập thời gian sống ngắn, tối ưu từ 15 đến 30 phút.

Thông tin lưu trong Payload: Chỉ lưu các định danh cơ bản không nhạy cảm dùng cho việc xác thực và phân quyền như user_id, email, và role.

Thông tin tuyệt đối không được lưu: Mật khẩu (dù đã được băm), thông tin cá nhân (số điện thoại, căn cước công dân, địa chỉ nhà).

Cách xử lý khi token hết hạn: Server trả về mã lỗi 401 Unauthorized. Phía client sẽ tự động gọi API lấy token mới bằng Refresh Token, hoặc chuyển hướng người dùng về trang đăng nhập nếu phiên bản làm việc đã hết hạn hoàn toàn.

Xử lý khi tài khoản bị khóa nhưng token còn hạn: Áp dụng cơ chế Token Blacklist (lưu danh sách các token bị vô hiệu hóa vào Redis) hoặc thiết lập một Middleware luôn kiểm tra trạng thái is_active/is_locked của người dùng trong cơ sở dữ liệu ở các luồng API quan trọng để từ chối request ngay lập tức.

2.3. Chính sách đăng nhập
Số lần đăng nhập sai cho phép: Tối đa 5 lần.

Thời gian khóa tài khoản: Khóa 15 phút cho lần vi phạm đầu tiên. Nếu cố tình vi phạm tiếp sau khi hết hạn khóa, thời gian sẽ tăng lên 1 giờ hoặc khóa vĩnh viễn cho đến khi liên hệ quản trị viên.

Lưu lịch sử đăng nhập: Hệ thống ghi log chi tiết mọi phiên đăng nhập (thành công và thất bại) bao gồm: Địa chỉ IP, thiết bị (User-Agent), và thời gian.

Thông báo thiết bị lạ: Hệ thống đối chiếu IP và User-Agent với lịch sử đăng nhập. Nếu phát hiện có sự thay đổi lớn (ví dụ: đăng nhập từ quốc gia khác hoặc thiết bị hoàn toàn mới), tự động gửi email cảnh báo bảo mật.

3. Chính sách phân quyền
Căn cứ vào yêu cầu, quyền hạn của từng loại tài khoản trong hệ thống LMS được thiết lập như sau:

Student (Sinh viên): Được phép xem thông tin cá nhân và xem điểm cá nhân. Không có quyền nhập điểm hay quản lý tài khoản.

Teacher (Giảng viên): Được phép xem thông tin cá nhân và nhập điểm cho sinh viên thuộc lớp mình phụ trách. Không được quản lý tài khoản hay xem điểm tổng quát ngoài thẩm quyền.

Training Manager (Quản lý đào tạo): Được phép xem thông tin cá nhân, xem điểm cá nhân (của mọi sinh viên), nhập điểm, và quản lý tài khoản ở mức độ hạn chế (chỉ quản lý, thêm/sửa/xóa tài khoản của Student và Teacher).

Admin (Quản trị viên): Nắm toàn quyền hệ thống. Được phép thực hiện tất cả chức năng: xem thông tin, xem điểm, nhập điểm và quản lý toàn bộ các loại tài khoản (bao gồm cả Training Manager).

4. Sơ đồ luồng xác thực
Người dùng nhập email và password tại form đăng nhập.

Server tiếp nhận và kiểm tra email có tồn tại trong cơ sở dữ liệu hay không.

Nếu email tồn tại, hệ thống sử dụng hàm verify của thư viện Bcrypt để so sánh mật khẩu nhập vào với mã hash trong CSDL.

Kiểm tra trạng thái tài khoản. Nếu tài khoản đang bị khóa hoặc vô hiệu hóa, từ chối đăng nhập.

Nếu hợp lệ, hệ thống sinh ra Access Token và Refresh Token.

Client nhận token, lưu trữ cục bộ và gửi kèm Access Token (chuẩn Bearer) trong HTTP Header ở các request tiếp theo.

Server thông qua Middleware kiểm tra chữ ký và thời hạn của token.

Trả về dữ liệu nếu token hợp lệ, hoặc từ chối truy cập (mã 401/403) nếu token sai hoặc thiếu quyền.

5. Yêu cầu sáng tạo bổ sung
Để tối ưu hóa bảo mật trong môi trường thực tế, hệ thống nên bổ sung các tính năng:

Refresh Token Rotation: Mỗi khi người dùng sử dụng Refresh Token để đổi lấy Access Token mới, hệ thống sẽ cấp luôn một Refresh Token mới và vô hiệu hóa cái cũ. Việc này giúp ngăn chặn triệt để rủi ro bị đánh cắp session dài hạn.

Chống Brute-force bằng CAPTCHA: Thay vì khóa tài khoản ngay lập tức gây ảnh hưởng trải nghiệm, hệ thống sẽ yêu cầu giải mã Google reCAPTCHA hoặc Cloudflare Turnstile sau khi nhập sai mật khẩu từ lần thứ 3 trở đi.

Thu hồi Token từ xa (Logout Everywhere): Cung cấp giao diện cho phép người dùng xem danh sách các phiên đăng nhập đang hoạt động và cho phép họ nhấn nút "Đăng xuất" để thu hồi token trên các thiết bị lạ từ xa (đưa token của thiết bị đó vào Blacklist).
"""