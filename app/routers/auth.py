from fastapi import APIRouter,Depends,HTTPException,status

from datetime import datetime ,timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
import random
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from starlette.concurrency import run_in_threadpool
import jwt
from email.message import EmailMessage
from ..models import User,Documnet,Otp_store
from ..security import hash_pass,verify_pass,grt_current_user

from ..schemas import OTPDATA,verifyOTPDATA,RegisterDTO,LoginDto,UserOut,reset_Password,delete_DTO
from ..db import get_db
from ..rag.retrieve import delete_user_document
from ..config import get_settings
import os
import shutil
setting = get_settings()


router = APIRouter(tags=["auth"])

@router.post("/otp")
async def sendOtp(data:OTPDATA,session:AsyncSession=Depends(get_db)):
    
    inotpTable = (await session.scalars(select(Otp_store).where(Otp_store.email == data.email))).first()

    if inotpTable:
       
        await session.delete(inotpTable)
        await session.commit()


    gen_otp = random.randint(10000,99999)
    SENDER = setting.Sender_email

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = setting.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": data.email}],
        sender = {"name":"DocAI", "email":SENDER},
        subject="Your DocAI OTP",
        text_content = (f"Your OTP is :{gen_otp}. This OTP is valid for 5 minutes.")

    )


    
    try:
        await run_in_threadpool(api_instance.send_transac_email,email)
    except Exception as e:
        print("Resend email error:",str(e))
        raise HTTPException(status_code=500,detail="Unable to send OTP email")

   

    userOtpstore = Otp_store(email=data.email,otp=str(gen_otp),expires_at=datetime.now()+ timedelta(minutes=5))

    session.add(userOtpstore)
    await session.commit()
    await session.refresh(userOtpstore)

    
    return {"status":True}

@router.post("/verifyOtp")
async def verifyOtp(data:verifyOTPDATA,session:AsyncSession=Depends(get_db)):
    otpData =  (await session.scalars(select(Otp_store).where(Otp_store.email == data.email))).first()

    if not otpData:
        
        return {"status" : False}

    if otpData.otp != data.otp or otpData.expires_at < datetime.now():
        
        return {"status":False}
    
    


    await session.delete(otpData)
    await session.commit()
   
    return {"status" : True}



@router.post("/setpassword")
async def register(data:RegisterDTO,session : AsyncSession=Depends(get_db)):
    existing = (await session.scalars(select(User).where(User.email == data.email))).first()

    if existing:
        return {
            "status":False,
            "message":"You already registered"
        }


    user =  User(email=data.email, hashed_password=hash_pass(data.password),username=data.username)

    session.add(user)
    await session.commit()
    await session.refresh(user) 
   
    return {"status":True,
            "message":"registration complete"}


@router.post("/login")
async def login(user:LoginDto,db:AsyncSession=Depends(get_db)):
    isUser = await db.execute(select(User).where(User.email == user.email))
    isUser = isUser.scalar_one_or_none()

    if not isUser:
        return {"status":False,
                "message":"You entered wrong username"}

    if not verify_pass(user.password,isUser.hashed_password):
        return {
            "status":False,
            "message":"You entered wrong password"
        }

    token = jwt.encode({"_id":isUser.id},setting.jwt_secret,setting.jwt_algorithm)

    return {"status":True,"message":token}


@router.get("/me",response_model=UserOut)
async def me(user: User = Depends(grt_current_user)):
    return {
        "id":user.id,
        "name":user.username,
        "email":user.email
    }




   


    
@router.delete("/delete-account")
async def deleteAccount(data:delete_DTO, user: User = Depends(grt_current_user), session: AsyncSession = Depends(get_db)):
    isUser = await session.get(User,user.id)
    
    if not isUser:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    
    user_id = isUser.id
    if not verify_pass(data.password, isUser.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You entered wrong password")
    await delete_user_document(isUser.id)

    await session.execute(delete(Documnet).where(Documnet.user_id==isUser.id))
    await session.commit()

    await session.delete(isUser)
    await session.commit()


    user_folder = os.path.join(setting.UPLOAD_DIR,str(user_id))
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
    

    return {
        "status":"delete"
    }

@router.put("/reset_password")
async def reset_password(data:reset_Password,session:AsyncSession=Depends(get_db)):
     user = (await session.execute(select(User).where(data.email == User.email))).scalar_one_or_none()

     if not user:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You entered wrong username")

     user.hashed_password = hash_pass(data.password)
     await session.commit()
     await session.refresh(user) 

     return {"status":True, "message":"reset password"}
         
