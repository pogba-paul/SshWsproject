#!/bin/bash

# تعيين كلمة السر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# تشغيل SSH
/usr/sbin/sshd

# تثبيت وتشغيل GOST (لتحويل المنافذ وقبول أي Payload)
curl -L https://github.com/ginuerzh/gost/releases/download/v2.11.1/gost-linux-amd64-2.11.1.gz | gunzip > /usr/local/bin/gost
chmod +x /usr/local/bin/gost

# تشغيل النفق على المنفذ 8080 ليدعم SSH و WS معاً
/usr/local/bin/gost -L=ws://:8080?path=/
