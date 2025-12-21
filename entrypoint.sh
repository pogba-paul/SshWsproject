#!/bin/bash

# 1. إعداد كلمة السر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# 2. تنظيف المنافذ
fuser -k -9 8080/tcp || true

# 3. تشغيل SSH في الخلفية
/usr/sbin/sshd

# 4. تشغيل Gost كعملية أساسية (الآن المسار مضمون)
/usr/local/bin/gost -L=:8080
