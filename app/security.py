from pwdlib import PasswordHash
import jwt
from fastapi import Request
from .models import User
from .db import get_db
from sqlalchemy import select
from .config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException,status,Request,Depends

settings = get_settings()



hashalgo = PasswordHash.recommended()
def hash_pass(password:str) ->str:
    return hashalgo.hash(password)

def verify_pass(password:str,hash_pass:str) -> bool:
    return hashalgo.verify(password,hash_pass)



async def grt_current_user(request:Request,session:AsyncSession=Depends(get_db)) -> User:


    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token = request.headers.get("authorization","")
    token = token.split(" ")[-1]
  
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error":"You are Unauthorized !"})
        
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:
        raise credentials_error
    

    user_id = data.get("_id")
    user = await session.get(User, user_id)
    if user is None:
        raise credentials_error
    
    return user