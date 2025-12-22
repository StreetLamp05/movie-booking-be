import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.append('/app')

from wsgi import app
from src.app import db
from src.app.models.users import User

def delete_old_users():
    PROTECTED_USER_EMAIL = os.getenv("PROTECTED_USER_EMAIL", "protected@example.com")
    DAYS_THRESHOLD = 3

    with app.app_context():
        all_users = User.query.filter(User.is_admin == False).all()
        print(f"found {len(all_users)} non-admin users.")

        now = datetime.now(timezone.utc)
        threshold_date = now - timedelta(days=DAYS_THRESHOLD) + timedelta(minutes=5)
        
        users_to_delete = []

        for user in all_users:
            is_old_enough = user.created_at < threshold_date
            is_not_protected = user.email != PROTECTED_USER_EMAIL
            
            print(f"{user.email} | Created: {user.created_at} | Older than threshold: {is_old_enough}")

            if is_old_enough and is_not_protected:
                users_to_delete.append(user)

        if not users_to_delete:
            print("no users matched the deletion criteria.")
            return

        print(f"deleting {len(users_to_delete)} users")
        for user in users_to_delete:
            print(f"Deleting user: {user.email}")
            db.session.delete(user)

        try:
            db.session.commit()
            print("Successfully deleted users.")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to delete users: {e}")

if __name__ == "__main__":
    delete_old_users()