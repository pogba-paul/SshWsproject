FROM ubuntu:22.04

# تثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    openssh-server sudo curl net-tools psmisc ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# تحميل وتثبيت Gost مباشرة داخل الصورة
RUN curl -L https://github.com/ginuerzh/gost/releases/download/v2.11.1/gost-linux-amd64-2.11.1.gz | gunzip > /usr/local/bin/gost && \
    chmod +x /usr/local/bin/gost

# إعداد SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 8080 22

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
