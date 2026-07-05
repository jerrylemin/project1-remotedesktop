# Hướng dẫn sử dụng TelePC cho máy Server và máy Client

Tài liệu này giúp thiết lập TelePC trên hai máy Windows trong cùng mạng LAN:

```text
Máy Server / Admin                    Máy Client được điều khiển
FastAPI :8000                         TelePCClient.exe hoặc client.py
WebSocket Relay :8001       <---->    Kết nối tới Server
Trình duyệt quản trị                  Hiện popup Yes / No tại máy Client
```

Kết quả cuối cùng cần thấy:

- Server mở được `http://localhost:8000/admin/login`.
- Client xuất hiện tại trang `Machines` với trạng thái `online`.
- Mọi thao tác nhạy cảm chỉ chạy sau khi người ngồi tại Client bấm **Yes** trong popup 15 giây.

> Chỉ dùng TelePC trên máy được cấp quyền. Giữ cửa sổ Client hiển thị; không dùng để điều khiển âm thầm.

## 1. Chuẩn bị

### Máy Server

- Windows 10/11.
- Python 3.11 trở lên; khuyến nghị Python 3.12.
- Repo TelePC đầy đủ.
- Kết nối LAN với Client.
- Quyền Administrator nếu muốn script tự mở Windows Firewall.

Kiểm tra Python:

```powershell
py -3.12 --version
```

### Máy Client

Chọn một trong hai cách:

1. Chạy `TelePCClient.exe`: máy Client không cần cài Python.
2. Chạy `client.py`: cần Python 3.11+ và source repo.

Các tính năng thật cần thêm thư viện:

| Tính năng | Gói |
|---|---|
| Chụp màn hình | `mss` |
| Danh sách process/application | `psutil` |
| Webcam | `opencv-python` |
| Keylogger Lab có consent | `pynput` |
| Điều khiển chuột/phím thật, chỉ khi được phép | `pyautogui` |

## 2. Thiết lập máy Server lần đầu

Mở PowerShell tại thư mục repo:

```powershell
cd "C:\Users\Administrator\Documents\MEGA\project1-remotepc"
```

### Bước 2.1 — Cài dependency

```powershell
py -3.12 -m pip install -r requirements.txt
```

### Bước 2.2 — Tạo tài khoản Admin

```powershell
py -3.12 scripts/create_admin.py --username admin
```

Nhập mật khẩu khi PowerShell hỏi. Mật khẩu không hiển thị trên màn hình. Không dùng `admin123` hoặc mật khẩu đang dùng cho tài khoản cá nhân.

Chỉ cần tạo Admin một lần. Các lần sau dữ liệu nằm trong `telepc.db`.

### Bước 2.3 — Khởi động Server

```powershell
py -3.12 main.py
```

Lệnh này khởi động:

- API/admin web trên TCP `8000`.
- WebSocket relay trên TCP `8001`.
- Không khởi động fake/demo agent.

Giữ cửa sổ PowerShell này mở. Dừng Server bằng `Ctrl+C`.

### Bước 2.4 — Kiểm tra Server

Mở một PowerShell khác:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

Kết quả đúng có `StatusCode : 200`.

Mở trình duyệt:

```text
http://localhost:8000/admin/login
```

Đăng nhập bằng tài khoản vừa tạo.

### Bước 2.5 — Xác định IP LAN của Server

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
  Select-Object InterfaceAlias, IPAddress
```

Ví dụ IP Server là `192.168.1.10`. Dùng IP thật của máy, không dùng IP trong ví dụ.

### Bước 2.6 — Kiểm tra Firewall

`main.py` sẽ thử mở cổng `8000` và `8001`. Nếu Client không kết nối được, chạy PowerShell bằng quyền Administrator trên Server:

```powershell
New-NetFirewallRule -DisplayName "TelePC API 8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
New-NetFirewallRule -DisplayName "TelePC Relay 8001" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001
```

Chỉ mở hai cổng này trong mạng lab/private được cấp quyền.

## 3. Cấp danh tính cho máy Client

TelePC không chấp nhận Client dùng token tùy ý. Server phải cấp:

- Enroll token dùng một lần.
- `machine_id` riêng.
- `machine_secret` riêng.

### Bước 3.1 — Server tạo enroll token

Trên máy Server, mở PowerShell mới. Thay `192.168.1.10` bằng IP Server:

```powershell
$Server = "http://192.168.1.10:8000"
$Credential = Get-Credential -UserName "admin"
$LoginBody = @{
  username = $Credential.UserName
  password = $Credential.GetNetworkCredential().Password
} | ConvertTo-Json

$Login = Invoke-RestMethod -Method Post -Uri "$Server/auth/login" -ContentType "application/json" -Body $LoginBody
$Headers = @{ Authorization = "Bearer $($Login.access_token)" }
$Enroll = Invoke-RestMethod -Method Post -Uri "$Server/api/enroll-tokens" -Headers $Headers
$Enroll.enroll_token
```

Sao chép giá trị enroll token sang máy Client qua kênh nội bộ an toàn. Token này chỉ dùng được một lần.

Không chụp màn hình hoặc đưa token vào báo cáo công khai.

### Bước 3.2 — Client đổi enroll token lấy machine secret

Trên máy Client:

```powershell
$Server = "http://192.168.1.10:8000"
$EnrollToken = Read-Host "Nhap enroll token mot lan"
$EnrollBody = @{
  enroll_token = $EnrollToken
  hostname = $env:COMPUTERNAME
  os = "Windows"
  username = $env:USERNAME
} | ConvertTo-Json

$Machine = Invoke-RestMethod -Method Post -Uri "$Server/api/agents/enroll" -ContentType "application/json" -Body $EnrollBody
$Machine.machine_id
```

Secret nằm trong `$Machine.machine_secret` nhưng không được in ra console. Giữ `$Machine` trong phiên PowerShell hiện tại. Không lưu `machine_secret` vào repo, ảnh chụp, chat, log hoặc lệnh Git.

Nếu đóng PowerShell, lưu secret trong trình quản lý mật khẩu của phòng lab rồi nạp lại vào biến môi trường khi chạy Client.

## 4. Chạy máy Client bằng file EXE

### Bước 4.1 — Lấy file EXE

File chuẩn nằm tại Server:

```text
dist\TelePCClient.exe
```

Sao chép duy nhất file này sang một thư mục trên Client, ví dụ:

```text
C:\TelePC\TelePCClient.exe
```

Nếu cần build lại trên Server:

```powershell
py -3.12 -m pip install pyinstaller
py -3.12 -m scripts.package_client_exe
Test-Path .\dist\TelePCClient.exe
```

### Bước 4.2 — Kiểm tra kết nối từ Client

```powershell
Test-NetConnection 192.168.1.10 -Port 8000
Test-NetConnection 192.168.1.10 -Port 8001
```

Cả hai lệnh cần có:

```text
TcpTestSucceeded : True
```

### Bước 4.3 — Chạy EXE ở chế độ an toàn mặc định

Trong cùng PowerShell đã enroll:

```powershell
cd C:\TelePC
$env:MACHINE_TOKEN = $Machine.machine_secret
.\TelePCClient.exe --server 192.168.1.10 --machine-id $Machine.machine_id --mode real
```

Nếu đã đóng phiên enroll, nạp secret từ nơi lưu an toàn:

```powershell
$MachineId = Read-Host "Nhap machine ID da cap"
$SecretCredential = Get-Credential -UserName $MachineId -Message "Nhap machine secret vao o Password"
$env:MACHINE_TOKEN = $SecretCredential.GetNetworkCredential().Password
.\TelePCClient.exe --server 192.168.1.10 --machine-id $MachineId --mode real
```

Giữ console Client mở. Dấu hiệu đúng:

```text
TelePC agent ... running in REAL mode
API: http://192.168.1.10:8000
Relay: ws://192.168.1.10:8001
Keep this console open
```

## 5. Chạy máy Client bằng source Python

Trên Client, mở PowerShell tại repo và cài dependency:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"
```

Chạy:

```powershell
$env:MACHINE_TOKEN = $Machine.machine_secret
py -3.12 client.py --server 192.168.1.10 --machine-id $Machine.machine_id --mode real
```

Chế độ này không tự bật điều khiển input thật hoặc power thật. Đây là cấu hình nên dùng cho demo và chấm đồ án.

## 6. Thao tác từ máy Server

### Bước 6.1 — Chọn máy

1. Mở `http://localhost:8000/admin/login`.
2. Đăng nhập.
3. Mở `Machines`.
4. Kiểm tra đúng hostname/username của Client và trạng thái `online`.
5. Bấm `Manage`.
6. Bấm `Claim Control` trước khi gửi lệnh.

Chỉ một Admin được giữ quyền điều khiển một máy tại một thời điểm.

### Bước 6.2 — Quy trình consent

Khi Server yêu cầu thao tác nhạy cảm:

1. Server tạo consent gắn với đúng command ID và payload.
2. Client hiện popup mô tả thao tác.
3. Người dùng Client chọn **Yes** hoặc **No**.
4. Không trả lời trong 15 giây được xem là từ chối.
5. Lệnh chỉ được relay chuyển tiếp khi consent khớp chính xác và chưa dùng.
6. Kết quả được ghi vào Audit Logs.

### Bước 6.3 — Applications

Tab Applications luôn có năm ứng dụng:

- Zalo
- Discord
- VSCode
- Chrome
- Notepad

`missing` nghĩa là máy Client chưa cài ứng dụng. Start/Stop yêu cầu popup local. Không nhập đường dẫn `.exe` tùy ý.

### Bước 6.4 — Processes

- Xem PID, tên, CPU, RAM và username.
- Chỉ thử Stop với process vô hại do bạn vừa mở, ví dụ Notepad.
- Không thử với process hệ thống.
- TelePC chặn các process quan trọng và kiểm tra lại tên process để tránh PID đã bị tái sử dụng.

### Bước 6.5 — Screen

- `Start Live Screen`: Client phải approve trước khi frame bắt đầu.
- `Stop`: có consent riêng.
- `Screenshot`: có consent riêng.

Nếu ảnh không xuất hiện, kiểm tra Client đã cài `mss` và vẫn online.

### Bước 6.6 — Files

Trên Client, tạo thư mục thử nghiệm:

```powershell
New-Item -ItemType Directory -Force C:\Remote
Set-Content C:\Remote\telepc-test.txt "TelePC lab test"
```

TelePC chỉ hiển thị thư mục `X:\Remote` thực sự tồn tại, ví dụ `C:\Remote` hoặc `D:\Remote`. Không hỗ trợ Desktop, Downloads, `Windows\System32`, UNC hoặc đường dẫn có `..`.

List và Download đều yêu cầu consent riêng. File tải từ Client bị giới hạn kích thước để tránh dùng quá nhiều bộ nhớ.

### Bước 6.7 — Webcam

1. Bấm tải danh sách thiết bị.
2. Client approve popup enumerate.
3. Chọn đúng camera được agent trả về.
4. Bấm Start và approve popup.
5. Bấm Stop khi hoàn tất.

Không có webcam thì UI phải hiển thị `no webcam found`; không tự dùng camera 0 giả.

### Bước 6.8 — Keylogger Lab Module

Chỉ dùng trong bài lab được cấp quyền:

1. Chọn TTL ngắn, ví dụ 30 hoặc 60 giây.
2. Bấm Start.
3. Người dùng Client đọc cảnh báo và bấm Yes.
4. Quan sát trạng thái `running` và thời gian hết hạn.
5. Bấm Stop khi xong; TTL cũng tự dừng listener.
6. Export cần consent riêng.

Không gõ mật khẩu, OTP, thông tin ngân hàng hoặc dữ liệu cá nhân trong lúc kiểm thử.

### Bước 6.9 — Power

`restart` và `shutdown` là chức năng nguy hiểm:

- Không bật real power trong demo thông thường.
- Chỉ thử khi phòng lab cho phép.
- Luôn nhập lý do ít nhất 5 ký tự và approve tại Client.

## 7. Chế độ lab-real cho input và power

Mặc định TelePC không thực thi input/power thật. Chỉ bật trên máy lab được phép:

```powershell
$env:MACHINE_TOKEN = $Machine.machine_secret
py -3.12 client.py `
  --profile lab-real `
  --confirm-real-mode TELEPC_LAB_AUTHORIZED `
  --server 192.168.1.10 `
  --machine-id $Machine.machine_id
```

Lệnh này bật real input và real power cho tiến trình Client hiện tại. Đóng Client ngay sau bài kiểm thử.

## 8. Dừng hệ thống đúng cách

### Client

Tại console Client:

```text
Ctrl+C
```

Keylogger listener và webcam session được giải phóng khi Client ngắt kết nối.

### Server

Tại console chạy `main.py`:

```text
Ctrl+C
```

Không tắt cửa sổ bằng Task Manager nếu có thể; `Ctrl+C` cho phép tiến trình con dừng sạch.

## 9. Lỗi thường gặp

### Client báo không kết nối được API hoặc relay

Kiểm tra:

```powershell
Test-NetConnection <SERVER_IP> -Port 8000
Test-NetConnection <SERVER_IP> -Port 8001
```

- Xác nhận Server vẫn chạy.
- Dùng IP LAN, không dùng `127.0.0.1` trên Client.
- Kiểm tra Windows Firewall Server.
- Hai máy phải nhìn thấy nhau trong cùng mạng/VLAN được phép.

### `invalid machine secret`

- Phải dùng `machine_id` và `machine_secret` từ cùng một lần enroll.
- Không dùng enroll token làm machine secret.
- Enroll token chỉ dùng một lần.
- Nếu mất secret, tạo enroll token mới và enroll lại thành máy mới.

### Client không xuất hiện trong Machines

- Console Client phải còn mở.
- Kiểm tra hai cổng.
- Kiểm tra mode là `real`.
- Kiểm tra machine secret đúng.
- Refresh trang Machines sau vài giây.

### Đăng nhập bị HTTP 429

TelePC giới hạn đăng nhập sai liên tiếp trong 60 giây. Dừng thử mật khẩu, chờ hết cửa sổ giới hạn rồi đăng nhập lại bằng mật khẩu đúng.

### Application báo `APP_NOT_FOUND`

Ứng dụng nằm trong whitelist nhưng chưa được cài hoặc không nằm ở vị trí Windows phổ biến. Không sửa bằng cách gửi raw executable path.

### Process/Webcam/Screen báo dependency thiếu

Nếu chạy bằng source:

```powershell
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"
```

Nếu chạy EXE, build lại sau khi các gói này đã được cài trên máy build.

### Popup không hiện

- Client phải chạy trong phiên desktop có người dùng đăng nhập, không chạy âm thầm như service.
- Không thu nhỏ vào phiên Windows khác/RDP khác.
- Kiểm tra Client console còn kết nối.
- Popup lỗi hoặc hết 15 giây luôn được xem là deny.

## 10. Checklist demo nhanh

### Server

- [ ] Python 3.12 hoạt động.
- [ ] Admin đã được tạo bằng mật khẩu riêng.
- [ ] `main.py` đang chạy.
- [ ] `/health` trả 200.
- [ ] Cổng 8000/8001 mở trong LAN lab.
- [ ] Đã cấp enroll token một lần.

### Client

- [ ] Đã enroll và nhận đúng cặp machine ID/secret.
- [ ] `Test-NetConnection` hai cổng đều thành công.
- [ ] Client chạy ở mode real trong console hiển thị.
- [ ] Máy xuất hiện online trên Server.
- [ ] Popup Yes/No xuất hiện và timeout deny.
- [ ] Sau demo đã Stop webcam/Keylogger và đóng Client bằng `Ctrl+C`.

## 11. Thu thập bằng chứng physical validation

Sau khi hai máy hoạt động, chạy trên Server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_physical_lab_validation.ps1
```

Lưu bảy ảnh và `validation_notes.md` theo `docs/REAL_MACHINE_TEST_CHECKLIST.md`. Không tạo bằng chứng giả và không để lộ password, enroll token hoặc machine secret trong ảnh.
