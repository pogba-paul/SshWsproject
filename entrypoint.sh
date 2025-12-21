#!/bin/bash

# 1. إعداد كلمة السر للسيرفر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# 2. تشغيل خدمة الـ SSH الأساسية
mkdir -p /var/run/sshd
/usr/sbin/sshd

# 3. تحميل أداة Gost وتجهيزها
# هذه الأداة ستعمل كمترجم لأي Payload ترسلها من التطبيق
curl -L https://github.com/ginuerzh/gost/releases/download/v2.11.1/gost-linux-amd64-2.11.1.gz | gunzip > /usr/local/bin/gost
chmod +x /usr/local/bin/gost

# 4. تشغيل Gost لقبول Websocket و TCP و HTTP في نفس الوقت
# هذا الأمر يجعل السيرفر يفهم الـ BMOVE والـ HEAD والروابط الخارجية
/usr/local/bin/gost -L=ws://:8080?path=/ -L=tcp://:8080
