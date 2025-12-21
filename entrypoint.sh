#!/bin/bash

# 1. تعيين كلمة السر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# 2. إيقاف أي خدمة قد تحاول استخدام المنفذ 8080 (لحل مشكلة bind: address already in use)
fuser -k 8080/tcp || true
service shellinabox stop || true

# 3. تشغيل SSH
mkdir -p /var/run/sshd
/usr/sbin/sshd

# 4. تثبيت Gost (إذا لم يكن موجوداً)
if [ ! -f /usr/local/bin/gost ]; then
    curl -L https://github.com/ginuerzh/gost/releases/download/v2.11.1/gost-linux-amd64-2.11.1.gz | gunzip > /usr/local/bin/gost
    chmod +x /usr/local/bin/gost
fi

# 5. تشغيل Gost كعملية أساسية (بدون & في النهاية لضمان بقاء الحاوية تعمل)
# سيستقبل السيرفر الآن Websocket و TCP و HTTP على منفذ 8080
/usr/local/bin/gost -L=ws://:8080?path=/ -L=tcp://:8080
