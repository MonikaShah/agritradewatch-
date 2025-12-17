# utils/sms.py
import requests
from django.conf import settings

def send_fast2sms_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "otp",
        "variables_values": otp,
        "numbers": mobile
    }
    headers = {
        "authorization": settings.FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print("FAST2SMS RESPONSE:", response.text)   # 🔴 ADD THIS
    return response.json()
