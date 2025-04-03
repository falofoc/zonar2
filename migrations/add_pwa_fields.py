"""
إضافة حقول PWA وإشعارات الويب إلى جدول المستخدمين
"""
from app import app, db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import traceback

def add_columns():
    """إضافة أعمدة إلى جدول المستخدمين"""
    try:
        with app.app_context():
            # التحقق من وجود الأعمدة
            columns_exist = False
            try:
                # محاولة تنفيذ استعلام بسيط للتحقق
                from app.models import User
                result = db.session.execute(db.select(User.push_subscription)).first()
                columns_exist = True
                print("الأعمدة موجودة بالفعل.")
            except Exception as e:
                # الأعمدة غير موجودة أو خطأ آخر
                columns_exist = False
                print(f"التحقق من الأعمدة: {str(e)}")
            
            if not columns_exist:
                # إضافة الأعمدة الجديدة
                db.engine.execute("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS push_subscription TEXT,
                    ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS device_info TEXT;
                """)
                print("تمت إضافة الأعمدة بنجاح.")
            
            db.session.commit()
            print("تم تحديث قاعدة البيانات بنجاح.")
    except Exception as e:
        print(f"حدث خطأ أثناء إضافة الأعمدة: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)

if __name__ == "__main__":
    add_columns() 