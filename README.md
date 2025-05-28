# Đề tài: Xây dựng website giới thiệu và bán hàng mỹ phẩm cho hãng Hada Labo

## Hướng dẫn cài đặt và chạy dự án

### Bước 1: Tải và giải nén
- Tải file **Do_an_KHMT.zip** về máy.
- Giải nén file này ra thư mục **Do_an_KHMT**.

### Bước 2: Tạo database
- Mở **pgAdmin4** (hoặc công cụ quản lý PostgreSQL khác).
- Tạo một database mới với tên:cosmetics 


### Bước 3: Cài đặt môi trường và chạy server
1. Mở thư mục dự án **ban_hang_my_pham** bằng **VS Code** (hoặc IDE khác).  
2. Mở Terminal trong VS Code và thực hiện các lệnh sau:

```bash
# Tạo migration
py manage.py makemigrations

# Áp dụng migration để tạo bảng trong database
py manage.py migrate

# Chạy server
py manage.py runserver
