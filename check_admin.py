from app import app, db
from app.models import User

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        print(f"User found: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is admin: {user.is_admin}")
        print(f"Email verified: {user.email_verified}")
        print(f"Check password '123456': {user.check_password('123456')}")
    else:
        print("Admin user not found")
        print("Creating admin user...")
        admin = User(
            username='admin',
            email='admin@zonar.local',
            is_admin=True,
            email_verified=True
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!") 