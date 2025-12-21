FROM ubuntu:22.04

# تثبيت SSH والخدمات الأساسية مع حزم إضافية لدعم Gost
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    net-tools \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# إعداد مجلد تشغيل SSH وضبط الإعدادات
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# فتح المنفذ 8080 (الذي سيستخدمه Koyeb) والمنفذ 22
EXPOSE 22 8080

# إضافة سكربت التشغيل وتغيير صلاحياته
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# نقطة الانطلاق
ENTRYPOINT ["/entrypoint.sh"]
