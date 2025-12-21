FROM ubuntu:22.04

# تثبيت الأدوات اللازمة بما فيها psmisc لعمل أمر fuser
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    net-tools \
    psmisc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# سنبقى على EXPOSE 8080 لأن Koyeb يحتاجها
EXPOSE 8080 22

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
