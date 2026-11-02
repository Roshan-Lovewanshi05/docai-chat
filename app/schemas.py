from pydantic import Field

from pydantic import BaseModel,EmailStr,ConfigDict

from datetime import datetime

class OTPDATA(BaseModel):
    email:str

class verifyOTPDATA(BaseModel):
    email:str
    otp:str


class RegisterDTO(BaseModel):
    email:str
    username:str
    password:str=Field(min_length=6)


class LoginDto(BaseModel):
    email:str
    password:str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    name:str
    email:str
    



class Token(BaseModel):
    access_token : str


class ChatRequest(BaseModel):
    question:str

class ChatResponse(BaseModel):
    answer:str


class delete_DTO(BaseModel):
    password:str

class reset_Password(BaseModel):
    email:str
    password:str=Field(min_length=6)