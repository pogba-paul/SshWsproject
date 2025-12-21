FROM ubuntu:latest

# تثبيت SSH والخدمات الأساسية
RUN apt-get update && apt-get install -y \
    openssh-server \
    shellinabox \
    sudo \
    curl \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# إعداد مجلد تشغيل SSH
RUN mkdir /var/run/sshd

# السماح بدخول الروت عبر SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# نفتح المنفذ 22 للـ SSH والمنفذ 8080 للـ Websocket
EXPOSE 22 8080

# إضافة سكربت التشغيل
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
