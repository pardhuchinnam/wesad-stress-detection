"""Verify .env configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 60)
print("🔍 Checking .env Configuration")
print("=" * 60)

# Check all required variables
checks = {
    'MAIL_SERVER': os.getenv('MAIL_SERVER'),
    'MAIL_PORT': os.getenv('MAIL_PORT'),
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
}

all_good = True

for key, value in checks.items():
    if value:
        if key == 'MAIL_PASSWORD':
            print(f"✅ {key}: {value}")  # Show actual password for verification
            if value == "your_16_char_app_password_here":
                print(f"   ⚠️ WARNING: Still using placeholder!")
                all_good = False
            elif value == "eakd fxgw ivzl ptue":
                print(f"   ✅ Correct Gmail App Password set!")
        else:
            print(f"✅ {key}: {value}")
    else:
        print(f"❌ {key}: NOT SET")
        all_good = False

print("=" * 60)

if all_good:
    print("✅ Configuration looks good! You can run test_email.py")
else:
    print("❌ Please fix the issues above before running test_email.py")

print("=" * 60 + "\n")
