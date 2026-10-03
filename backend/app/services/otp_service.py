import random
import string
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.redis import get_redis
from app.config import setting
from starlette.concurrency import run_in_threadpool
from twilio.rest import Client


class OTPService:
    @staticmethod
    def generate_otp() -> str:
        return ''.join(random.choices(string.digits, k=6))

    async def send_otp(self, phone_number: str) -> dict:
        redis = get_redis()
        if redis is not None:
            await redis.delete(f"otp:{phone_number}")

        code = self.generate_otp()

        otp_data = {
            "code": code,
            "attempts": 0,
            "max_attempts": 3,
        }

        if redis is not None:
            await redis.setex(f"otp:{phone_number}", 600, json.dumps(otp_data))
        else:
            return {"success": False, "message": "OTP storage unavailable"}

        try:
            await run_in_threadpool(self._dispatch_sms, phone_number, code)
            return {"success": True, "message": f"OTP sent to {phone_number}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send OTP: {str(e)}"}

    @staticmethod
    def _dispatch_sms(phone_number: str, code: str) -> None:
        client = Client(setting.TWILIO_API_KEY, setting.TWILIO_API_SECRET, setting.TWILIO_ACCOUNT_SID)
        client.messages.create(
            body=f"BingeSaga PVT LTD . Your OTP is: {code}. Valid for 10 minutes.",
            from_=setting.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )

    async def verify_otp(self, phone_number: str, code: str) -> dict:
        redis = get_redis()
        if redis is None:
            return {"valid": False, "error": "OTP storage unavailable"}

        otp_data_str = await redis.get(f"otp:{phone_number}")

        if not otp_data_str:
            return {"valid": False, "error": "No OTP found for this phone or OTP expired"}

        otp_data = json.loads(otp_data_str)

        if otp_data["attempts"] >= otp_data["max_attempts"]:
            await redis.delete(f"otp:{phone_number}")
            return {"valid": False, "error": "Too many wrong attempts"}

        if otp_data["code"] != code:
            otp_data["attempts"] += 1
            ttl = await redis.ttl(f"otp:{phone_number}")
            await redis.setex(f"otp:{phone_number}", ttl, json.dumps(otp_data))
            remaining = otp_data["max_attempts"] - otp_data["attempts"]
            return {"valid": False, "error": f"Wrong OTP. {remaining} attempts remaining"}

        await redis.delete(f"otp:{phone_number}")
        return {"valid": True}


otp_service = OTPService()
