# Hướng dẫn nhanh TelePC cho Server và Client

TelePC dùng cho các máy Windows được cho phép trong cùng mạng LAN.

```text
Server: main.py → Web Admin + API + WebSocket Relay
Client: TelePCClient.exe hoặc client.py → máy được điều khiển
```

## 1. Chuẩn bị

### Máy Server

- Windows 10/11.
- Python 3.11 trở lên, khuyến nghị Python 3.12.
- Thư mục source TelePC.

### Máy Client

Chọn một cách:

- Dễ nhất: dùng `TelePCClient.exe`, không cần cài Python.
- Hoặc dùng `client.py` trong source repo.

Hai máy phải cùng mạng LAN. Chỉ sử dụng trên máy đã được cho phép.

## 2. Chạy Server bằng một file duy nhất

Mở PowerShell tại thư mục TelePC:

```powershell
cd "C:\Users\Administrator\Documents\MEGA\project1-remotepc"
```

Chỉ lần đầu tiên, cài thư viện:

```powershell
py -3.12 -m pip install -r requirements.txt
```

Khởi động toàn bộ Server:

```powershell
py -3.12 main.py
```

`main.py` tự thực hiện tất cả việc sau:

- Khởi tạo database.
- Lần đầu: hỏi mật khẩu và tạo tài khoản `admin`.
- Những lần sau: dùng lại tài khoản và dữ liệu cũ.
- Chạy Web Admin/API tại cổng `8000`.
- Chạy WebSocket Relay tại cổng `8001`.
- Thử mở Windows Firewall cho hai cổng trên.
- Hiển thị địa chỉ LAN để Client kết nối.

Khi nhập mật khẩu lần đầu, ký tự sẽ không hiện trên màn hình. Nhập cùng một mật khẩu hai lần, tối thiểu 8 ký tự.

Mở trình duyệt:

```text
http://localhost:8000/admin/login
```

Đăng nhập bằng:

- Username: `admin`
- Password: mật khẩu vừa tạo

Giữ cửa sổ PowerShell Server luôn mở. Nhấn `Ctrl+C` để dừng toàn bộ Server.

## 3. Lấy IP của Server

Khi chạy, `main.py` tự in địa chỉ LAN, ví dụ:

```text
http://192.168.1.10:8000/admin/login
```

Trong ví dụ này, IP Server là `192.168.1.10`. Hãy dùng IP thật được in trên máy của bạn.

Từ máy Client, kiểm tra kết nối:

```powershell
Test-NetConnection 192.168.1.10 -Port 8000
Test-NetConnection 192.168.1.10 -Port 8001
```

Cả hai kết quả cần có `TcpTestSucceeded : True`.

## 4. Cấp danh tính cho Client lần đầu

Mỗi Client cần `machine_id` và `machine_secret`. Thao tác này chỉ làm một lần cho mỗi máy.

### Bước 1 — Server tạo enroll token

Giữ `main.py` đang chạy. Mở thêm một PowerShell trên Server và dán đoạn sau:

```powershell
$Server = "http://127.0.0.1:8000"
$Credential = Get-Credential -UserName "admin"
$Login = Invoke-RestMethod -Method Post -Uri "$Server/auth/login" -ContentType "application/json" -Body (@{
  username = $Credential.UserName
  password = $Credential.GetNetworkCredential().Password
} | ConvertTo-Json)
$Enroll = Invoke-RestMethod -Method Post -Uri "$Server/api/enroll-tokens" -Headers @{
  Authorization = "Bearer $($Login.access_token)"
}
$Enroll.enroll_token
```

Sao chép enroll token vừa hiện sang máy Client. Token chỉ dùng được một lần.

### Bước 2 — Client nhận machine identity

Trên Client, thay `192.168.1.10` bằng IP Server rồi dán:

```powershell
$Server = "http://192.168.1.10:8000"
$EnrollToken = Read-Host "Nhap enroll token"
$Machine = Invoke-RestMethod -Method Post -Uri "$Server/api/agents/enroll" -ContentType "application/json" -Body (@{
  enroll_token = $EnrollToken
  hostname = $env:COMPUTERNAME
  os = "Windows"
  username = $env:USERNAME
} | ConvertTo-Json)
$env:MACHINE_TOKEN = $Machine.machine_secret
```

Không gửi hoặc chụp màn hình `machine_secret`. Nếu cần dùng lại, lưu secret trong trình quản lý mật khẩu của phòng lab.

## 5. Chạy Client

### Cách A — Dùng file EXE

Sao chép `TelePCClient.exe` vào Client, ví dụ `C:\TelePC\TelePCClient.exe`.

Trong cùng cửa sổ PowerShell vừa enroll:

```powershell
cd C:\TelePC
.\TelePCClient.exe --server 192.168.1.10 --machine-id $Machine.machine_id
```

### Cách B — Dùng source Python

Trên Client, mở PowerShell tại repo và chạy một lần:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7" "pyautogui>=0.9"
```

Sau đó chạy:

```powershell
py -3.12 client.py --server 192.168.1.10 --machine-id $Machine.machine_id
```

Nếu `MACHINE_TOKEN` chưa được đặt, `client.py` sẽ hỏi `Machine secret (input hidden)`. Dán `machine_secret` đã nhận khi enroll rồi nhấn Enter; secret không hiển thị trên màn hình.

Real input và real power tự bật trong chế độ real. Consent, phân quyền và audit log vẫn luôn được áp dụng.

Giữ cửa sổ Client mở. Máy sẽ xuất hiện tại trang `Machines` với trạng thái `online`.

## 6. Điều khiển Client từ Server

1. Mở `http://localhost:8000/admin/login`.
2. Đăng nhập.
3. Mở `Machines`.
4. Chọn máy đang `online`.
5. Nhấn `Claim Control`.
6. Chọn Screen, Applications, Processes, Files, Webcam hoặc Power.
7. Tại Client, bấm **Yes** trên popup consent trong 15 giây.

Nếu bấm **No** hoặc hết 15 giây, lệnh bị từ chối.

Giới hạn an toàn quan trọng:

- Applications chỉ gồm Zalo, Discord, VSCode, Chrome và Notepad.
- Files chỉ truy cập thư mục `C:\Remote`, `D:\Remote`, `E:\Remote`, `X:\Remote` nếu tồn tại.
- Restart và Shutdown yêu cầu lý do, consent và có thời gian chờ.
- Client luôn hiển thị console và popup; không chạy ẩn.

## 7. Dừng hệ thống

### Dừng Client

Nhấn `Ctrl+C` trong cửa sổ Client.

### Dừng Server

Nhấn `Ctrl+C` trong cửa sổ đang chạy `main.py`. API và relay sẽ được dừng cùng nhau.

## 8. Lỗi thường gặp

### Client không kết nối được

- Kiểm tra đúng IP Server.
- Kiểm tra Server vẫn đang chạy `main.py`.
- Chạy lại `Test-NetConnection` cho cổng `8000` và `8001`.
- Nếu cần, chạy PowerShell Server bằng quyền Administrator để mở Firewall.

### Báo `invalid machine secret`

Enroll lại Client để lấy danh tính mới hoặc nạp đúng secret đã lưu.

### Client không xuất hiện trên trang Machines

Giữ console Client mở và kiểm tra có dòng báo đã kết nối API/relay.

### Không có popup consent

Kiểm tra Client đang chạy trong phiên desktop có người dùng đăng nhập, không chạy dưới dạng service ẩn.

## Checklist chạy nhanh

Server:

```powershell
py -3.12 main.py
```

Client sau khi enroll:

```powershell
$env:MACHINE_TOKEN = $Machine.machine_secret
.\TelePCClient.exe --server 192.168.1.10 --machine-id $Machine.machine_id
```

Sau đó đăng nhập Web Admin → Machines → chọn máy → Claim Control → thao tác → Client bấm Yes.
