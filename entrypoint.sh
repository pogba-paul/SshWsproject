#!/bin/bash

# 1. تعيين كلمة السر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# 2. قتل أي عملية تستخدم المنفذ 8080 بقوة (SIGKILL)
fuser -k -9 8080/tcp || true

# 3. تشغيل SSH
/usr/sbin/sshd

# 4. تحميل Gost
if [ ! -f /usr/local/bin/gost ]; then
    curl -L https://github.com/ginuerzh/gost/releases/download/v2.11.1/gost-linux-amd64-2.11.1.gz | gunzip > /usr/local/bin/gost
    chmod +x /usr/local/bin/gost
fi

# 5. تشغيل Gost
# أضفنا تأخير بسيط (sleep) للتأكد من أن النظام حرر المنفذ تماماً
sleep 2
/usr/local/bin/gost -L=:8080
