#!/bin/bash

# 1. إعداد كلمة السر
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# 2. تشغيل SSH 
# تأكد من إنشاء مفاتيح المضيف إذا لم تكن موجودة
ssh-keygen -A
/usr/sbin/sshd

# 3. تشغيل Gost 
# أضفنا & لجعل العملية تعمل ونضمن بقاء الحاوية تعمل بـ wait أو تشغيلها مباشرة
echo "Starting Gost on port 8080..."
exec /usr/local/bin/gost -L=:8080
