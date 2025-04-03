# ZONAR زونار

<div dir="rtl">

## نظام تتبع أسعار أمازون السعودية

زونار هو تطبيق ويب متكامل لتتبع أسعار المنتجات على موقع أمازون السعودية. يتيح للمستخدمين إضافة منتجات للمراقبة والحصول على إشعارات عند تغير الأسعار أو وصولها للسعر المستهدف.

</div>

---

## Amazon Saudi Arabia Price Tracker

ZONAR is a comprehensive web application for tracking product prices on Amazon Saudi Arabia. It allows users to add products for monitoring and receive notifications when prices change or reach target prices.

---

<div dir="rtl">

## المميزات الرئيسية

- تتبع أسعار منتجات أمازون السعودية
- إشعارات تلقائية لتغيرات الأسعار
- تحديد سعر مستهدف لكل منتج
- تاريخ تغير الأسعار مع رسم بياني
- واجهة سهلة الاستخدام بتصميم متجاوب
- دعم اللغتين العربية والإنجليزية
- وضع تصفح ليلي (داكن)
- تخزين الصور محلياً لتجنب مشاكل انتهاء الروابط
- خدمة مجدولة للتحقق التلقائي من الأسعار
- تبويب مخصص لمشاهدة أفضل العروض

</div>

## Key Features

- Track Amazon.sa product prices
- Automatic price change notifications
- Set target price for each product
- Price history with charts
- User-friendly responsive interface
- Arabic and English language support
- Dark mode
- Local image storage to avoid link expiration issues
- Scheduled service for automatic price checking
- Dedicated tab for viewing best deals

---

<div dir="rtl">

## متطلبات النظام

- Python 3.8 أو أحدث
- SQLite (للتطوير المحلي) أو MySQL/PostgreSQL (للإنتاج)
- خادم SMTP لإرسال البريد الإلكتروني (اختياري)

</div>

## System Requirements

- Python 3.8 or higher
- SQLite (for local development) or MySQL/PostgreSQL (for production)
- SMTP server for sending emails (optional)

---

<div dir="rtl">

## دليل الإعداد والتشغيل

### 1. استنساخ المشروع

```bash
git clone https://github.com/falofoc/zonar2.git
cd zonar2
```

### 2. إنشاء البيئة الافتراضية

```bash
# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
# في نظام Windows
venv\Scripts\activate
# في نظام macOS أو Linux
source venv/bin/activate
```

### 3. تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة

قم بإنشاء ملف `.env` في المجلد الرئيسي للمشروع:

```
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///instance/amazon_tracker.db
MAIL_SERVER=smtp.yourmailserver.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=no-reply@yourdomain.com
```

### 5. إنشاء قاعدة البيانات

```bash
flask db upgrade
```

### 6. تشغيل التطبيق

```bash
# للتطوير المحلي
flask run --debug

# للإنتاج
gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000
```

التطبيق سيكون متاحاً على الرابط: http://localhost:5000 (للتطوير) أو http://localhost:8000 (للإنتاج)

### 7. تحديث الصور المخزنة محلياً

لتحميل صور المنتجات وتخزينها في قاعدة البيانات:

```bash
python update_images.py
```

### 8. إعداد المهام المجدولة (الخدمة المجدولة)

#### باستخدام cron (لأنظمة Linux/macOS)

أضف هذه السطور إلى ملف crontab:

```bash
# تحرير ملف crontab
crontab -e

# أضف هذا السطر لتشغيل فحص الأسعار كل 6 ساعات
0 */6 * * * cd /path/to/zonar2 && /path/to/zonar2/venv/bin/python scheduler.py >> /path/to/zonar2/logs/cron.log 2>&1
```

#### باستخدام Supervisor (مناسب للإنتاج)

قم بتثبيت وإعداد Supervisor:

```bash
# تثبيت Supervisor
pip install supervisor

# إنشاء ملف تهيئة
cat > /etc/supervisor/conf.d/zonar.conf << EOF
[program:zonar_webapp]
command=/path/to/zonar2/venv/bin/gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000
directory=/path/to/zonar2
user=www-data
autostart=true
autorestart=true
redirect_stderr=true

[program:zonar_scheduler]
command=/path/to/zonar2/venv/bin/python scheduler.py
directory=/path/to/zonar2
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/path/to/zonar2/logs/scheduler.log
EOF

# تحديث وإعادة تشغيل Supervisor
supervisorctl reread
supervisorctl update
supervisorctl status
```

#### باستخدام Task Scheduler (لنظام Windows)

1. افتح Task Scheduler من لوحة التحكم
2. أنشئ مهمة جديدة تعمل كل 6 ساعات
3. أضف الأمر:
   ```
   cmd /c "cd /d D:\path\to\zonar2 && D:\path\to\zonar2\venv\Scripts\python.exe scheduler.py >> D:\path\to\zonar2\logs\scheduler.log 2>&1"
   ```

</div>

## Setup and Running Guide

### 1. Clone the Repository

```bash
git clone https://github.com/falofoc/zonar2.git
cd zonar2
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS or Linux
source venv/bin/activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project's root directory:

```
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///instance/amazon_tracker.db
MAIL_SERVER=smtp.yourmailserver.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=no-reply@yourdomain.com
```

### 5. Create the Database

```bash
flask db upgrade
```

### 6. Run the Application

```bash
# For local development
flask run --debug

# For production
gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000
```

The application will be available at: http://localhost:5000 (for development) or http://localhost:8000 (for production)

### 7. Update Locally Stored Images

To download product images and store them in the database:

```bash
python update_images.py
```

### 8. Set Up Scheduled Tasks (Cron Service)

#### Using cron (on Linux/macOS)

Add these lines to your crontab file:

```bash
# Edit crontab file
crontab -e

# Add this line to run price checking every 6 hours
0 */6 * * * cd /path/to/zonar2 && /path/to/zonar2/venv/bin/python scheduler.py >> /path/to/zonar2/logs/cron.log 2>&1
```

#### Using Supervisor (recommended for production)

Install and configure Supervisor:

```bash
# Install Supervisor
pip install supervisor

# Create configuration file
cat > /etc/supervisor/conf.d/zonar.conf << EOF
[program:zonar_webapp]
command=/path/to/zonar2/venv/bin/gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000
directory=/path/to/zonar2
user=www-data
autostart=true
autorestart=true
redirect_stderr=true

[program:zonar_scheduler]
command=/path/to/zonar2/venv/bin/python scheduler.py
directory=/path/to/zonar2
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/path/to/zonar2/logs/scheduler.log
EOF

# Update and restart Supervisor
supervisorctl reread
supervisorctl update
supervisorctl status
```

#### Using Task Scheduler (on Windows)

1. Open Task Scheduler from Control Panel
2. Create a new task that runs every 6 hours
3. Add the command:
   ```
   cmd /c "cd /d D:\path\to\zonar2 && D:\path\to\zonar2\venv\Scripts\python.exe scheduler.py >> D:\path\to\zonar2\logs\scheduler.log 2>&1"
   ```

---

<div dir="rtl">

## ملاحظات هامة

- تم تصميم نظام زونار للتتبع فقط، وليس مرتبطًا بموقع أمازون
- أسعار المنتجات قد تتغير في أي وقت، فالنظام يعطي مؤشر فقط ويحتاج للفحص الدوري
- تأكد من أن البيئة المستضيفة تسمح بتشغيل مهام Cron لضمان تحديث الأسعار بانتظام
- يحتاج معالج الصور إلى مكتبات Python الإضافية التي قد تتطلب حزم تطوير إضافية على الخادم

</div>

## Important Notes

- ZONAR is designed for tracking only and is not affiliated with Amazon
- Product prices may change at any time, the system gives an indication only and requires periodic checking
- Make sure your hosting environment allows running Cron jobs to ensure regular price updates
- The image processor requires additional Python libraries that may require extra development packages on the server

---

<div dir="rtl">

## المكتبات المستخدمة

</div>

## Dependencies

- Flask
- SQLAlchemy
- Flask-Login
- Flask-Migrate
- Flask-Mail
- BeautifulSoup4
- Requests
- Gunicorn (for production)
- Supervisor (optional, for process management)

---

<div dir="rtl">

## جهات الاتصال والدعم

للاستفسارات أو الدعم، الرجاء التواصل عبر:

- البريد الإلكتروني: contact@example.com
- GitHub Issues: https://github.com/falofoc/zonar2/issues

</div>

## Contact and Support

For inquiries or support, please contact:

- Email: contact@example.com
- GitHub Issues: https://github.com/falofoc/zonar2/issues
