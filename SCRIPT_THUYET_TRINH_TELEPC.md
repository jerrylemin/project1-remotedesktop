# Script thuyết trình đồ án TelePC

Thời lượng mục tiêu: 7–10 phút.

Trước khi thuyết trình, thay thông tin thành viên, MSSV và lớp trên slide đầu.

## Slide 1 — Giới thiệu đề tài

Em xin kính chào thầy cô và các bạn.

Nhóm em xin trình bày đồ án TelePC — ứng dụng web hỗ trợ điều khiển máy tính từ xa trong phòng lab.

Mục tiêu của TelePC không chỉ là kết nối và điều khiển máy tính, mà còn bảo đảm ba yếu tố: người dùng tại máy Client nhìn thấy thao tác, các lệnh nhạy cảm phải được đồng ý và toàn bộ quá trình có thể truy vết bằng audit log.

Trong phần trình bày này, em sẽ giới thiệu bài toán, kiến trúc, cơ chế bảo mật, các chức năng chính và kết quả kiểm thử của hệ thống.

## Slide 2 — Vấn đề và động lực

Trong một phòng lab có nhiều máy, kỹ thuật viên thường phải di chuyển đến từng máy để kiểm tra lỗi hoặc hỗ trợ người sử dụng.

Việc này tốn thời gian, đặc biệt khi nhiều máy gặp vấn đề cùng lúc. Người quản trị cũng khó theo dõi trạng thái toàn bộ phòng máy trên một giao diện thống nhất.

TelePC được xây dựng để giải quyết bài toán đó. Người quản trị có thể xem máy nào đang online, chọn đúng máy cần hỗ trợ và thực hiện thao tác từ xa ngay trên trình duyệt.

Tuy nhiên, hệ thống vẫn phải bảo đảm người ngồi tại máy Client biết và đồng ý với các thao tác nhạy cảm.

## Slide 3 — Phạm vi dự án

TelePC gồm năm thành phần chính.

Thứ nhất là Admin Web, nơi người quản trị đăng nhập và điều khiển máy.

Thứ hai là API Server, chịu trách nhiệm xác thực, phân quyền và lưu audit log.

Thứ ba là WebSocket Relay, truyền dữ liệu thời gian thực giữa trình duyệt và Client.

Thứ tư là Client Agent chạy trên máy được quản lý.

Cuối cùng là consent popup, cho phép người dùng tại Client bấm Yes hoặc No trước khi lệnh nhạy cảm được thực thi.

Năm thành phần này tạo thành một luồng điều khiển rõ ràng và có trách nhiệm.

## Slide 4 — Kiến trúc tổng thể

Sơ đồ trên slide thể hiện luồng chính của hệ thống.

Admin thao tác trên trình duyệt. Yêu cầu đi vào API Server để kiểm tra đăng nhập, quyền truy cập và phiên điều khiển.

Sau đó, WebSocket Relay chuyển lệnh theo thời gian thực đến TelePCClient trên đúng máy đích. Client hiển thị consent khi cần và chỉ thực thi trên máy Windows sau khi được chấp thuận.

Kết quả được gửi ngược lại theo cùng luồng để giao diện hiển thị và Server ghi audit.

Việc tách API và relay giúp hệ thống phân biệt rõ phần kiểm soát quyền với phần truyền dữ liệu realtime.

## Slide 5 — Luồng kết nối Client

Để một Client xuất hiện trên dashboard, hệ thống thực hiện bốn bước.

Đầu tiên, Client được cấp machine ID và machine secret riêng. Tiếp theo, Agent dùng thông tin đó để kết nối WebSocket Relay.

Server kiểm tra secret và trạng thái của máy. Chỉ khi xác thực thành công, máy mới được đánh dấu online và xuất hiện trên dashboard.

Nếu machine secret sai hoặc máy đã bị vô hiệu hóa, kết nối bị từ chối và sự kiện được ghi lại.

Nhờ vậy, người dùng không thể tùy ý tạo một Client giả rồi xuất hiện trong danh sách máy thật.

## Slide 6 — Xác thực và phân quyền

TelePC kiểm tra quyền theo nhiều lớp thay vì chỉ dựa vào đăng nhập.

Lớp đầu tiên là tài khoản và mật khẩu. Sau đó hệ thống kiểm tra role, ví dụ Admin, Teacher hoặc Auditor.

Tiếp theo là machine grant, nghĩa là một tài khoản chỉ được thao tác trên những máy đã được cấp quyền.

Cuối cùng là owner permission. Tại một thời điểm, một máy chỉ có một phiên điều khiển chính để tránh hai người gửi lệnh xung đột.

Admin có toàn quyền. Teacher chỉ điều khiển các máy được cấp grant. Auditor chủ yếu xem trạng thái và audit log, không gửi lệnh điều khiển.

## Slide 7 — Quy trình consent

Đây là cơ chế an toàn quan trọng nhất của TelePC.

Khi Admin gửi một lệnh nhạy cảm, Server tạo consent request gắn với chính xác nội dung của lệnh đó. Client nhận yêu cầu và hiển thị popup Yes hoặc No.

Người dùng có 15 giây để quyết định. Nếu chọn No hoặc không trả lời trong 15 giây, hệ thống tự động từ chối và lệnh không được thực thi.

Chỉ khi chọn Yes, đúng payload đã được duyệt mới được thực thi một lần.

Cơ chế này hạn chế việc phát lại consent cũ hoặc thay đổi nội dung lệnh sau khi người dùng đã đồng ý.

## Slide 8 — Điều khiển ứng dụng

Module Application Control không cho phép chạy chương trình tùy ý.

Hệ thống chỉ hỗ trợ năm ứng dụng trong whitelist gồm Zalo, Discord, VSCode, Chrome và Notepad.

Giao diện hiển thị ứng dụng đã cài hay còn thiếu, đang chạy hay đã dừng và mức sử dụng CPU.

Khi Admin chọn Start hoặc Stop, Client tiếp tục kiểm tra whitelist và yêu cầu consent trước khi thực hiện.

Cách làm này đơn giản cho người sử dụng và đồng thời ngăn việc gửi trực tiếp một câu lệnh tùy ý tới hệ điều hành.

## Slide 9 — Điều khiển tiến trình

Application Control làm việc ở mức ứng dụng quen thuộc, còn Process Control cho phép quan sát sâu hơn.

Module này hiển thị toàn bộ tiến trình đang chạy cùng với PID, CPU và RAM. Khi cần, Admin có thể yêu cầu dừng một process thông qua consent.

Tuy nhiên, các tiến trình hệ thống quan trọng như lsass, winlogon, csrss hoặc services luôn bị chặn.

Như vậy, Process Control cung cấp thông tin chi tiết để hỗ trợ kỹ thuật nhưng vẫn có giới hạn nhằm tránh làm mất ổn định hệ điều hành.

## Slide 10 — Whitelist file

TelePC không cho phép duyệt toàn bộ ổ đĩa của Client.

Hệ thống chỉ truy cập các thư mục Remote đã tồn tại, cụ thể là C Remote, D Remote, E Remote hoặc X Remote.

Mọi đường dẫn đều được kiểm tra tại phía Agent. Các trường hợp path traversal, đường dẫn UNC hoặc symlink thoát ra ngoài thư mục cho phép đều bị từ chối.

Điều này tạo ra một ranh giới file rõ ràng. Admin vẫn có thể hỗ trợ trao đổi file trong khu vực lab, nhưng không thể duyệt tùy ý dữ liệu khác trên máy Client.

## Slide 11 — Webcam và Keylogger Lab Module

Với Webcam, Client liệt kê các camera thật đang có. Admin chọn đúng thiết bị trước khi yêu cầu bật hoặc tắt và thao tác vẫn phải qua consent.

Keylogger Lab Module chỉ phục vụ trình diễn trong môi trường lab được cấp phép. Module này yêu cầu consent tại máy Client, có thời gian sống giới hạn, có nút Stop rõ ràng và có cơ chế xử lý ngữ cảnh nhạy cảm.

Điểm quan trọng là cả hai chức năng đều không chạy âm thầm. Console Client và trạng thái điều khiển luôn được hiển thị, đồng thời các hành động được ghi audit.

## Slide 12 — Audit logging

Audit log giúp trả lời ba câu hỏi: ai đã gửi lệnh, máy nào nhận lệnh và kết quả cuối cùng là gì.

Hệ thống ghi lại các trạng thái request, approved, denied, timeout, executed và failed.

Ví dụ trên slide cho thấy một lệnh có thể được chấp thuận và thực thi, bị người dùng từ chối hoặc hết thời gian consent nên không chạy.

Nhờ có vòng đời đầy đủ, người quản trị có thể kiểm tra sự cố, đối chiếu thao tác và chứng minh rằng một lệnh nhạy cảm không được thực hiện khi chưa có sự đồng ý.

## Slide 13 — Kiểm thử và đánh giá

Hệ thống đã vượt qua các cổng kiểm thử tự động chính.

Compileall đạt, Ruff đạt, bộ pytest vượt mốc 147 test, smoke test đạt và quá trình build file EXE cũng thành công.

Điểm đánh giá hiện tại là 96 trên 100. Phần chức năng và kiểm thử tự động đã hoàn thành, nhưng nhóm chưa claim 100 điểm vì còn thiếu bằng chứng chạy thực tế trên máy Windows vật lý.

Việc giữ điểm ở mức 96 thể hiện kết quả trung thực: phần mềm đã sẵn sàng, nhưng vẫn cần hoàn tất bước xác minh cuối trên thiết bị thật.

## Slide 14 — Kết luận và kế hoạch demo

Qua đồ án này, nhóm đã xây dựng được một hệ thống điều khiển máy tính từ xa qua web với kết nối realtime, phân quyền theo máy, consent tại Client, whitelist và audit log đầy đủ.

Trong phần demo, nhóm sẽ khởi động Server chỉ bằng file `main.py`, kết nối Client, claim quyền điều khiển và thực hiện một thao tác có consent để minh họa toàn bộ luồng.

Bước cuối để đạt trạng thái hoàn thiện 100 trên 100 là chạy script physical validation trên máy Windows thật và lưu đủ bằng chứng.

Thông điệp chính của TelePC là: kết nối được, người dùng đồng thuận và mọi thao tác đều truy vết được.

Nhóm em xin cảm ơn thầy cô và các bạn đã lắng nghe. Nhóm em xin sẵn sàng trả lời câu hỏi.

## Câu trả lời ngắn cho phần phản biện

### Tại sao dùng WebSocket thay vì chỉ dùng HTTP?

WebSocket duy trì kết nối hai chiều, phù hợp với trạng thái online, truyền lệnh và dữ liệu màn hình theo thời gian thực. HTTP vẫn được dùng cho đăng nhập, phân quyền và các API quản lý.

### Nếu consent hết 15 giây thì sao?

Hệ thống tự động deny. Lệnh không được chuyển sang bước thực thi và kết quả timeout được ghi audit.

### TelePC có chạy ẩn trên Client không?

Không. Client giữ console hiển thị, các chức năng nhạy cảm có popup consent và dự án không triển khai stealth hoặc persistence ẩn.

### Vì sao chỉ đạt 96/100?

Các cổng tự động đã đạt, nhưng nhóm chưa có đủ ảnh và ghi chú xác minh trên máy Windows vật lý. Nhóm chỉ claim 100/100 sau khi hoàn thành bằng chứng này.

### Server cần chạy những file nào?

Trong sử dụng bình thường chỉ cần chạy `py -3.12 main.py`. File này tự khởi tạo database, tạo admin lần đầu, chạy API, relay và quản lý dừng toàn bộ tiến trình.
