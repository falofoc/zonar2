# الروبوت التلقائي لأمازون السعودية - ملخص

تم إنشاء روبوت تلقائي لموقع تتبع أسعار أمازون السعودية، مهمته العثور على أفضل المنتجات المخفضة وإضافتها تلقائيًا للموقع. يقوم الروبوت بالتالي:

1. يبحث يوميًا عن منتجات أمازون المخفضة بنسبة 10% أو أكثر
2. يختار أفضل 10 منتجات ويضيفها للموقع
3. يضيف المنتجات باسم مستخدم مخصص "amazon_bot"
4. يميز المنتجات المضافة بواسطة الروبوت بعبارة "العروض اليومية:"

## الملفات المضافة

1. `amazon_bot_direct.py` - الملف الرئيسي للروبوت الذي يتصل مباشرة بقاعدة البيانات
2. `bot_scheduler_direct.py` - المجدول الذي يشغل الروبوت يوميًا في الساعة 9:00 صباحًا
3. `setup_bot.py` - أداة الإعداد التي تساعد في تثبيت الروبوت كخدمة نظام
4. `amazon_bot.service` - ملف خدمة systemd (يتم إنشاؤه بواسطة أداة الإعداد)
5. `AMAZON_BOT_README.md` - دليل شامل حول كيفية استخدام وتهيئة الروبوت

## كيفية الاستخدام

1. تثبيت الحزم المطلوبة: `pip install -r requirements.txt`
2. تشغيل أداة الإعداد: `python setup_bot.py`
3. اتباع التعليمات لتثبيت الروبوت كخدمة
4. بدء تشغيل الخدمة: `sudo systemctl start amazon_bot.service`

## تتبع النشاط

يمكن مراقبة نشاط الروبوت من خلال:

1. ملفات السجل في مجلد `logs/`
2. فحص المنتجات المضافة بواسطة الروبوت (تحمل بادئة "العروض اليومية:")
3. فحص حالة الخدمة: `sudo systemctl status amazon_bot.service`

## الميزات الرئيسية

- البحث المتقدم عن منتجات مخفضة من مصادر متعددة (صفحات العروض، الفئات المحددة)
- تحقق تلقائي من خصومات المنتجات
- اختيار عشوائي للمنتجات ذات الخصومات الأعلى
- تسجيل مفصل لجميع العمليات
- تشغيل مجدول تلقائيًا
- تثبيت بسيط كخدمة نظام

---

# Amazon Saudi Arabia Automated Bot - Summary

An automated bot has been created for the Amazon Saudi Arabia price tracking site, with the task of finding the best discounted products and automatically adding them to the site. The bot does the following:

1. Daily searches for Amazon products discounted by 10% or more
2. Selects the top 10 products and adds them to the site
3. Adds products under a dedicated user name "amazon_bot"
4. Marks bot-added products with the phrase "العروض اليومية:" (Daily Deals)

## Added Files

1. `amazon_bot_direct.py` - Main bot file that connects directly to the database
2. `bot_scheduler_direct.py` - Scheduler that runs the bot daily at 9:00 AM
3. `setup_bot.py` - Setup tool that helps install the bot as a system service
4. `amazon_bot.service` - systemd service file (created by the setup tool)
5. `AMAZON_BOT_README.md` - Comprehensive guide on how to use and configure the bot

## How to Use

1. Install required packages: `pip install -r requirements.txt`
2. Run setup tool: `python setup_bot.py`
3. Follow instructions to install bot as a service
4. Start the service: `sudo systemctl start amazon_bot.service`

## Activity Tracking

The bot's activity can be monitored through:

1. Log files in the `logs/` directory
2. Checking products added by the bot (marked with "العروض اليومية:")
3. Checking service status: `sudo systemctl status amazon_bot.service`

## Key Features

- Advanced search for discounted products from multiple sources (deal pages, specific categories)
- Automatic verification of product discounts
- Random selection of products with the highest discounts
- Detailed logging of all operations
- Automatic scheduled execution
- Simple installation as a system service 