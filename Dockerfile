FROM python:3.9-slim

# تثبيت الأدوات اللازمة للنظام (procps ضرورية لإدارة العمليات ps aux)
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات أولاً (للاستفادة من كاش الـ Docker)
COPY requirements.txt .

# تثبيت المكتبات من ملف requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع إلى الحاوية
COPY . .

# فتح البورت (يتوافق مع بورت Flask في السكربت)
EXPOSE 8080

# أمر تشغيل البوت
CMD ["python", "main.py"]
