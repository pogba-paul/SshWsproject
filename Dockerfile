# استخدام نسخة Ubuntu مستقرة
FROM ubuntu:22.04

# تثبيت الأدوات الضرورية
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-pip \
    sudo \
    curl \
    net-tools

# إعداد المستخدم (يمكنك تغيير اسم المستخدم وكلمة السر هنا)
RUN useradd -m -s /bin/bash geminiuser && echo "geminiuser:password123" | chpasswd && adduser geminiuser sudo
RUN mkdir /var/run/sshd

# تثبيت مكتبة الـ Websocket
RUN pip3 install websocket-server

# إنشاء سكربت التشغيل الذي يدمج SSH مع المحول
RUN echo 'import socket, threading; \
from websocket_server import WebsocketServer; \
def new_client(client, server): \
    try: \
        ssh_sock = socket.socket(); \
        ssh_sock.connect(("127.0.0.1", 22)); \
        def forward(a, b): \
            try: \
                while True: \
                    d = a.recv(4096); \
                    if not d: break; \
                    b.send(d) \
            except: pass \
        threading.Thread(target=forward, args=(client["handler"].request, ssh_sock)).start(); \
        threading.Thread(target=forward, args=(ssh_sock, client["handler"].request)).start(); \
    except: pass \
port = 10000; \
server = WebsocketServer(host="0.0.0.0", port=port); \
server.set_fn_new_client(new_client); \
server.run_forever()' > /ws_proxy.py

# البورت الافتراضي في Render هو 10000
EXPOSE 10000

# تشغيل السيرفر
CMD /usr/sbin/sshd && python3 /ws_proxy.py
