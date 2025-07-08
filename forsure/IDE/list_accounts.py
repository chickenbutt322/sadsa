
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from datetime import datetime

def list_all_accounts():
    """Display all user accounts with their details"""
    with app.app_context():
        try:
            users = User.query.all()
            
            if not users:
                print("No accounts found in the database.")
                return
            
            print(f"\n{'='*80}")
            print(f"TOTAL ACCOUNTS: {len(users)}")
            print(f"{'='*80}")
            
            verified_count = 0
            unverified_count = 0
            
            for i, user in enumerate(users, 1):
                status = "✅ VERIFIED" if user.email_verified else "❌ UNVERIFIED"
                if user.email_verified:
                    verified_count += 1
                else:
                    unverified_count += 1
                
                print(f"\n{i}. USERNAME: {user.username}")
                print(f"   EMAIL: {user.email}")
                print(f"   STATUS: {status}")
                print(f"   CREATED: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Unknown'}")
                print(f"   2FA ENABLED: {'Yes' if user.is_2fa_enabled else 'No'}")
                if user.first_name or user.last_name:
                    print(f"   NAME: {user.first_name or ''} {user.last_name or ''}".strip())
                print(f"   USER ID: {user.id}")
            
            print(f"\n{'='*80}")
            print(f"SUMMARY:")
            print(f"  Verified accounts: {verified_count}")
            print(f"  Unverified accounts: {unverified_count}")
            print(f"  Total accounts: {len(users)}")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"Error listing accounts: {e}")

if __name__ == '__main__':
    list_all_accounts()
