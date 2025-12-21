#!/bin/bash
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# تنظيف شامل للمنافذ
fuser -k -9 8080/tcp || true
fuser -k -9 22/tcp || true

# تشغيل SSH على المنفذ 22
/usr/sbin/sshd

# تشغيل Gost ليعمل كـ "جسر"
# سيستمع على 8080 (منفذ Koyeb) ويوجه لـ 22 (SSH)
/usr/local/bin/gost -L=:8080 -F=forward://127.0.0.1:22
