from pydantic import BaseModel

class SendOTPRequest(BaseModel):
    phone_number: str

class VerifyOTPRequest(BaseModel):
    phone_number: str
    code: str

class OTPResponse(BaseModel):
    message: str