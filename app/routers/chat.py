from fastapi import APIRouter,Depends

from ..models import User
from ..schemas import ChatRequest,ChatResponse
from ..security import grt_current_user

from ..rag.retrieve import generate,NormalChat


router = APIRouter()



@router.post("/chat",response_model=ChatResponse)
async def chat(req:ChatRequest,user:User=Depends(grt_current_user)):
    
    ans = await generate(req.question,user.id)
    

    return ChatResponse(answer=ans)

@router.post("/normalchat",response_model=ChatResponse)
async def chat(req:ChatRequest,user:User=Depends(grt_current_user)):
    
    
    ans = await NormalChat(req.question)

    return ChatResponse(answer=ans)