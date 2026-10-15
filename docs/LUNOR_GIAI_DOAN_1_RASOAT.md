# LUNOR OS — Báo cáo Giai đoạn 1: rà soát source, boot, cài đặt, Hyprland và đường kiểm thử web

**Ngày rà soát:** 16/10/2026  
**Phạm vi:** repository \`Gamevalentine/omarchy\`, nhánh \`lunor/1.0-clean-branding\` tại commit \`2371ac9c1e3484d6b4c55120b4cf9ccda7962e98\`; đối chiếu nhánh \`lunor/web-live-qa\`, \`lunor/usb-image-lab\`, \`lunor/cloudflare-pages\` và các log GitHub Actions.  
**Không phải:** chứng nhận toàn bộ 2.273 mục source; đây là kiểm toán trọng tâm trên đường **source → ISO → installer → bootloader → Hyprland → máy ảo → website**. Không có kiểm thử máy thật trong báo cáo.

## 1. Kết luận ngắn

**Giai đoạn 1: đạt ở phần xác minh baseline, nhưng KHÔNG được chuyển thẳng sang phát hành ảnh máy ảo hoặc khẳng định đã test được LUNOR qua trình duyệt.** Nền tảng đã được xác minh trong QEMU/KVM; các chốt còn thiếu để triển khai Giai đoạn 2 được liệt kê ở mục 4.

Điều kiện thành công đối với người dùng **không phải màu xanh GitHub Actions**. Thành công phải là: khởi động lại từ ảnh máy ảo đã cài sẵn, vào Hyprland mà không phải cài ISO lại, và người dùng nhìn thấy/điều khiển được menu, ứng dụng qua web. Hiện điều kiện này **chưa đạt**.

## 2. Bằng chứng kiểm chứng

| Hạng mục | Bằng chứng | Kết quả, phạm vi |
| --- | --- | --- |
| Nhánh LUNOR chính | So sánh commit \`2371ac9\` với \`lunor/1.0-clean-branding\`: identical, ahead 0 / behind 0 | **Đạt** — baseline không đổi |
| ISO build | [GitHub run 37935766465](https://github.com/Gamevalentine/omarchy/actions/runs/37935766465), job \`build-iso\`: success | **Đạt** — tạo ISO trong GitHub |
| ISO SHA256 | Run trên, job \`vm-test\`: ISO được tải và \`sha256sum --check\` thành công | **Đạt** — tính toàn vẹn file tải lại |
| Cài đặt và desktop | Run trên, job \`vm-test\`: \`Hyprland session is up\`, \`acceptance suite passed in 100s\`, \`success-session-03-desktop.png\` | **Đạt trong QEMU** — không suy ra tương thích laptop thật |
| Thử boot qua USB giả lập | [Run 38040758723](https://github.com/Gamevalentine/omarchy/actions/runs/38040758723): bước \`Install virtual disk and test boot portability\` success; job fail ở bước upload báo cáo | **Đạt giới hạn mô phỏng** — không phải USB thật, không phải release image |
| Web QA cuối | [Run 38768752905](https://github.com/Gamevalentine/omarchy/actions/runs/38768752905): bước \`Install, boot to Hyprland, and PUBLISH ready HTTPS link\` success; thông báo Hyprland running 16:37:47 UTC, link lúc 16:37:52 UTC; bước giữ desktop đến 17:37:59 UTC | **Đạt trong môi trường máy ảo web** — chưa xác nhận phiên tương tác thực tế của người dùng |
| Cloudflare Pages | Website \`https://lunor-os-preview-2026.pages.dev\` do người dùng chụp hiển thị | **Đạt phần portal tĩnh**, **chưa kết nối máy ảo thật** |
| Artifact ISO | \`lunor-os-iso-2\`, 6.244.052.612 byte (artifact nén), trong run 37935766465; chính sách \`retention-days: 7\`; API ghi \`expires_at: 2026-10-16T13:28:03Z\` | **Rủi ro sắp hết hạn / phải kiểm tra lại trước khi dùng** |

## 3. Kiến trúc và cấu hình nguồn đã kiểm tra

- **Mã/nhánh:** bộ cài ISO không tự có trong fork: workflow \`.github/workflows/lunor-iso-build-test.yml\` clone \`omacom/omarchy-iso\` (nhánh \`quattro\`) và \`omacom/omarchy-pkgs\`; áp dụng overlay LUNOR rồi build với \`omarchy-iso-make --local-source\`. Điều này giải thích vì sao chỉ nhìn vào repository fork không phải toàn bộ mã ISO đã build.
- **Bootloader:** \`etc/limine-entry-tool.d/omarchy-defaults.conf\` đặt \`TARGET_OS_NAME="LUNOR OS"\`, bật fallback bootloader; \`etc/limine-entry-tool.d/omarchy-uki.conf\` bật UKI.
- **Initramfs:** \`etc/mkinitcpio.conf.d/omarchy_hooks.conf\` có \`autodetect\`, \`block\`, \`filesystems\`, \`encrypt\`, \`kms\`. Một ảnh build trên QEMU có \`autodetect\` **chưa chắc** có đủ driver để khởi động trên máy/USB khác. Cần xác minh portable initramfs khi chuyển sang mục tiêu máy thật.
- **Display manager và Hyprland:** \`etc/sddm.conf.d/10-wayland.conf\` dùng \`start-hyprland\`; \`install/config/enable-services.sh\` enable \`sddm.service\`; \`config/hypr/hyprland.lua\` tải các cấu hình Hyprland; \`default/hypr/autostart.lua\` chạy \`omarchy-launch-shell\` và các dịch vụ phiên.
- **Trình cài đặt:** \`build/lunor-stage-a-overlay.py\` bổ sung lựa chọn autologin và bảo mật đĩa. Đây là overlay lúc build, cần gắn với đúng phiên bản upstream.
- **Đăng ký người dùng:** có cơ chế \`install/provisioning/omarchy-provision-owner.service\` và \`bin/omarchy-provision-owner\` dùng cho thiết lập người dùng ở lần boot đầu. **Chưa chứng minh** một ảnh sạch có thể được phát hành và hoàn tất setup không lỗi.
- **Web thử nghiệm:** \`lunor/web-live-qa\` chứa QEMU + noVNC + Cloudflare Quick Tunnel. Quy trình đã tự cài LUNOR vào \`base.qcow2\` **mỗi lần GitHub Actions chạy**; không duy trì ảnh đĩa giữa các run. Bản cập nhật sau đó mới đợi tín hiệu Hyprland trước khi công bố link, nhưng user acceptance qua browser chưa được xác nhận.
- **Website Cloudflare:** \`lunor/cloudflare-pages\` tạo cổng web + API báo trạng thái GitHub Actions; nó **không chạy Linux** và \`backendConnected:false\` được trả mặc định. Đây là cổng, không phải máy ảo.

## 4. Rủi ro / blockers bắt buộc trước Giai đoạn 2

### P0 — Phải xử lý

1. **Ảnh đĩa máy ảo dùng lại phải độc lập, sạch và có thể khởi động.** QA hiện sinh \`base.qcow2\` chứa tài khoản/mật khẩu demo và SSH key của test harness. Không đăng tải hoặc tái sử dụng ảnh đó làm bản public. Dùng cơ chế provisioning sạch *trước* khi tạo tài khoản demo, hoặc quy trình build factory-reset được kiểm chứng.
2. **Tạo snapshot có quy trình lưu trữ phù hợp.** GitHub-hosted runner xóa ổ đĩa khi job kết thúc; chỉ copy lại mã là không giải quyết việc cài lại. Cần chiến lược lưu ảnh VM không quá giới hạn quota/kích thước/chi phí và có SHA256; không hứa chạy miễn phí vô hạn.
3. **Cố định provenance ISO và phụ thuộc.** Workflow hiện clone các nhánh upstream thay vì commit pin, dùng \`archlinux:latest\` và \`pacman -Syu\`; việc tái tạo có thể khác phiên bản đã QA. ISO artifact Run 37935766465 có hạn đến **16/10/2026 13:28:03 UTC**; từ sau mốc đó phải xác minh artifact còn tồn tại hoặc build lại từ nguồn được khóa phiên bản. **Không tự kích hoạt build 6 GB để né hết hạn**.
4. **Kiểm chứng end-to-end thực sự.** Link Cloudflare mở được và GitHub job giữ VM 60 phút không chứng minh rằng web hiển thị/điều khiển desktop. Phải thử kết nối noVNC có xác thực, VNC framebuffer thực, bàn phím/chuột, mở terminal/menu và quay lại sau reboot.
5. **Bảo mật:** không tái sử dụng thông tin đăng nhập demo được từng chia sẻ trong chat; cần mật khẩu mới không lưu vào source công khai. SSH host key, authorized_keys và machine-id phải được reset/thiết lập đúng ở lần boot đầu của ảnh sạch.

### P1 — Rà soát tiếp

6. Kiểm thử dùng lại cùng một ảnh \`qcow2\` sau reboot, không mount/cài ISO lần nữa; kiểm tra bootloader EFI/UKI với firmware NVRAM mới.
7. Máy ảo QEMU hiện dùng \`virtio-vga\` / VNC, không tương đương GPU và âm thanh, Wi-Fi, độ sáng trên laptop thật. Phân loại chức năng nào có thể test web, chức năng nào bắt buộc test phần cứng.
8. Website Cloudflare Pages chỉ có UI + trạng thái workflow; tích hợp vào desktop thật cần máy chủ QEMU, cơ chế tạo phiên, xác thực, giới hạn thời gian, xử lý hỏng phiên. Không được thêm nút “Vào LUNOR” trước khi hoàn tất backend.

## 5. Tiêu chí cho phép chuyển sang Giai đoạn 2

- [x] Có baseline source chính xác, đã biết SHA.
- [x] Có bằng chứng cài OS và khởi động Hyprland trong QEMU.
- [x] Ghi rõ các file/config, điểm rủi ro và nhiệm vụ sửa.
- [ ] Chọn và chứng minh phương án tạo ảnh đĩa *sạch*, không demo credentials.
- [ ] Xác nhận lưu trữ ảnh và khả năng tải lại mà không cài ISO từ đầu (kèm chi phí nếu có).
- [ ] Thử boot ảnh hai lần độc lập và xác minh desktop.
- [ ] Xác nhận giao thức hiển thị tương tác web, sau đó mới nối Cloudflare.

**Đánh giá:** Giai đoạn 1 **hoàn thành ở mức rà soát và đóng băng baseline**, Giai đoạn 2 **chưa đạt/không được triển khai công khai** cho tới khi giải quyết các P0. Chưa thay đổi nhánh production, Windows, USB hoặc chạy ISO build nặng.

## 6. Nguồn tham chiếu

- [Main LUNOR source](https://github.com/Gamevalentine/omarchy/tree/lunor/1.0-clean-branding)
- [Full ISO/VM QA](https://github.com/Gamevalentine/omarchy/actions/runs/37935766465)
- [USB boot emulation test](https://github.com/Gamevalentine/omarchy/actions/runs/38040758723)
- [Latest real LUNOR Web QA](https://github.com/Gamevalentine/omarchy/actions/runs/38768752905)
- [USB safety lab](https://github.com/Gamevalentine/omarchy/tree/lunor/usb-image-lab)
- [Web QA lab](https://github.com/Gamevalentine/omarchy/tree/lunor/web-live-qa)
- [Cloudflare portal source](https://github.com/Gamevalentine/omarchy/tree/lunor/cloudflare-pages/cloudflare-pages)
