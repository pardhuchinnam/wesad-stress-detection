"""Verify Fitbit configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 60)
print("🔍 Verifying Fitbit Configuration")
print("=" * 60)

client_id = os.getenv('FITBIT_CLIENT_ID')
client_secret = os.getenv('FITBIT_CLIENT_SECRET')
redirect_uri = os.getenv('FITBIT_REDIRECT_URI')

print(f"\n✅ FITBIT_CLIENT_ID: {client_id}")
print(f"✅ FITBIT_CLIENT_SECRET: {client_secret}")
print(f"✅ FITBIT_REDIRECT_URI: {redirect_uri}")

# Verify values match Fitbit dev portal
expected_id = "23TPTZ"
expected_secret = "15d43743280229db30d528e72a295e53"
expected_uri = "http://127.0.0.1:5000/fitbit-callback"

print("\n" + "=" * 60)
print("🔄 Checking Against Fitbit Dev Portal")
print("=" * 60)

if client_id == expected_id:
    print(f"✅ Client ID matches: {expected_id}")
else:
    print(f"❌ Client ID mismatch!")
    print(f"   Expected: {expected_id}")
    print(f"   Got: {client_id}")

if client_secret == expected_secret:
    print(f"✅ Client Secret matches: {expected_secret[:10]}...")
else:
    print(f"❌ Client Secret mismatch!")
    print(f"   Expected: {expected_secret}")
    print(f"   Got: {client_secret}")

if redirect_uri == expected_uri:
    print(f"✅ Redirect URI matches: {expected_uri}")
else:
    print(f"❌ Redirect URI mismatch!")
    print(f"   Expected: {expected_uri}")
    print(f"   Got: {redirect_uri}")

print("\n" + "=" * 60)

if client_id == expected_id and client_secret == expected_secret and redirect_uri == expected_uri:
    print("✅ ALL CONFIGURATION CORRECT!")
    print("🚀 You can now start your app: python app.py")
else:
    print("❌ Please update your .env file with correct values")

print("=" * 60 + "\n")
