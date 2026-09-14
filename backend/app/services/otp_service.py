import random
import string
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import redis
from app.config import setting
from twilio.rest import Client

class OTPService:
    def __init__(self , redis_url : str):
        self.redis = redis.from_url(redis_url)
    
    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_otp(self, phone_number: str) -> dict:
        """
        Generate and store OTP in Redis
        Auto-deletes after 10 mins
        
        Returns: {"success": bool, "message": str}
        """
        # Invalidate previous OTP for this phone
        self.redis.delete(f"otp:{phone_number}")
        
        # Generate new OTP
        code = self.generate_otp()
        
        # Store in Redis with 10 min TTL
        otp_data = {
            "code": code,
            "attempts": 0,
            "max_attempts": 3
        }

        self.redis.setex(
            f"otp:{phone_number}",
            600,  # 10 mins in seconds
            json.dumps(otp_data)
        )
        
        try:
            client = Client(setting.TWILIO_API_KEY, setting.TWILIO_API_SECRET ,  setting.TWILIO_ACCOUNT_SID)
            message = client.messages.create(
                body=f"Letterboxd PVT LTD . Your OTP is: {code}. Valid for 10 minutes.",
                from_=setting.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            return {
                "success": True,
                "message": f"OTP sent to {phone_number}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send OTP: {str(e)}"
            }
    
    def verify_otp(self, phone_number: str, code: str) -> dict:
        """
        Verify OTP code from Redis
        
        Returns: {"valid": bool, "error": str}
        """
        # Get OTP from Redis
        otp_data_str = self.redis.get(f"otp:{phone_number}")
        
        if not otp_data_str:
            return {"valid": False, "error": "No OTP found for this phone or OTP expired"}
        
        otp_data = json.loads(otp_data_str)
        
        # Check if max attempts exceeded
        if otp_data["attempts"] >= otp_data["max_attempts"]:
            self.redis.delete(f"otp:{phone_number}")
            return {"valid": False, "error": "Too many wrong attempts"}
        
        # Check code
        if otp_data["code"] != code:
            otp_data["attempts"] += 1
            # Update in Redis with remaining TTL
            ttl = self.redis.ttl(f"otp:{phone_number}")
            self.redis.setex(
                f"otp:{phone_number}",
                ttl,
                json.dumps(otp_data)
            )
            remaining = otp_data["max_attempts"] - otp_data["attempts"]
            return {"valid": False, "error": f"Wrong OTP. {remaining} attempts remaining"}
        
        # SUCCESS
        self.redis.delete(f"otp:{phone_number}")  # Clean up after verification
        
        return {"valid": True}

# Initialize service
otp_service = OTPService(setting.REDIS_URL)