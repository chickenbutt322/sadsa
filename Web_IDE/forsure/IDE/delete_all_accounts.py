
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Project, ProjectFile, CodeSnippet

def delete_all_accounts():
    """Delete all user accounts and related data"""
    with app.app_context():
        try:
            # Delete all related data first (foreign key constraints)
            CodeSnippet.query.delete()
            ProjectFile.query.delete()
            Project.query.delete()
            
            # Delete all users
            users = User.query.all()
            user_count = len(users)
            
            for user in users:
                print(f"Deleting user: {user.username} ({user.email})")
                db.session.delete(user)
            
            db.session.commit()
            print(f"Successfully deleted {user_count} accounts and all related data")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting accounts: {e}")

if __name__ == '__main__':
    confirm = input("Are you sure you want to delete ALL user accounts? This cannot be undone. Type 'DELETE ALL' to confirm: ")
    if confirm == 'DELETE ALL':
        delete_all_accounts()
    else:
        print("Operation cancelled")
