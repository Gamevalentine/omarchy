# LUNOR OS — Giai đoạn 2: máy ảo cài sẵn và thử khởi động lại

## Mục tiêu đúng
Khởi động LUNOR thật từ một ảnh máy ảo đã cài, **không chạy trình cài đặt ISO mỗi khi muốn thử desktop**.

## Phần đang triển khai (chỉ QA trên GitHub)
- Lấy đúng source LUNOR đã được nghiệm thu và ISO đã kiểm tra SHA256 từ Run 37935766465.
- Dùng bộ test upstream được **ghim vào commit** `8d57ac988b734581d4070fdc832ca1f924e32112` (tránh branch cập nhật ngầm).
- Cài LUNOR **đúng một lần** vào `base.qcow2` 40 GiB.
- Chạy hai lượt khởi động mới từ `base.qcow2` bằng `--reuse-base`: mỗi lượt dùng lớp ghi tạm, kiểm tra Hyprland và acceptance suite.
- Sau mỗi lượt xác minh `qemu-img check` và SHA256 ảnh gốc không thay đổi.
- **Không upload** `base.qcow2`, SSH key, screenshot, video, log đăng nhập; artifact nếu có chỉ chứa `summary.txt`.
- Thời gian job có trần 45 phút. Không chạy lại tự động chỉ vì sửa source.

**Lưu ý quan trọng:** `base.qcow2` hiện vẫn có tài khoản QA `omarchy`, mật khẩu QA, SSH authorized key. Vì vậy nó chỉ được dùng làm bằng chứng khởi động lặp lại *trên runner dùng một lần*. **Nó không phải bản sạch để phát hành hoặc gắn vào website Cloudflare**.

## Các cổng chặn còn phải vượt qua trước khi có máy ảo dùng thật
1. Tạo **factory-first-boot QCOW2** chưa có tài khoản demo / SSH test key: kiểm tra offline thư mục home, passwd/shadow, authorized_keys, SSH host identity, machine-id, service setup owner pending.
2. Kiểm thử một **bản sao riêng** của ảnh factory-first-boot: tạo tài khoản mới rồi vào SDDM/Hyprland, reboot lại. Không biến bản factory đang phân phối thành ảnh đã đăng nhập.
3. Chứng minh nơi lưu ảnh qua các lần khởi chạy: GitHub-hosted runner **xóa filesystem sau mỗi job**. Cần nơi lưu có kiểm soát quyền, checksum, quota và chi phí được duyệt; không có nghĩa chạy ổn mãi miễn phí.
4. Kiểm thử Web end-to-end: trang Cloudflare Pages **không tự chạy** QCOW2. Chỉ công bố nút vào desktop sau khi có host QEMU và xác thực phiên.
5. Chức năng GPU, độ sáng, Wi-Fi và âm thanh thật vẫn cần xác nhận trên laptop HP khi người dùng cho phép.

## Nguồn kiểm chứng
- [Baseline LUNOR](https://github.com/Gamevalentine/omarchy/tree/lunor/1.0-clean-branding)
- [Báo cáo Giai đoạn 1](https://github.com/Gamevalentine/omarchy/blob/lunor/stage1-source-audit/docs/LUNOR_GIAI_DOAN_1_RASOAT.md)
- [Bộ kiểm thử ISO/VM đã đạt](https://github.com/Gamevalentine/omarchy/actions/runs/37935766465)
- [Website Cloudflare Portal](https://lunor-os-preview-2026.pages.dev/)

Không chạy CMD trên máy người dùng, không format ổ, không tạo dịch vụ trả phí. Nếu artifact ISO đã hết hạn, fail sớm; không chạy build nặng tự động để thay thế.
