#!/bin/bash

# تعيين كلمة سر للروت (يمكنك تغيير 'root123' لأي شيء تريده)
USER_PASS=${SSH_PASSWORD:-"root123"}
echo "root:$USER_PASS" | chpasswd

# تشغيل خدمة SSH
/usr/sbin/sshd

# تشغيل Shellinabox لتحويل الـ SSH إلى Websocket على المنفذ 8080
# هذا ما سيسمح لك بالاتصال عبر بروتوكول WS
shellinaboxd -t -s /:SSH --port=8080 --disable-ssl
