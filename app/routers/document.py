from fastapi import APIRouter,Depends,File,UploadFile,HTTPException,status
import hashlib
import os
from sqlalchemy import select
from ..models import User,Documnet
from ..db import get_db
from ..security import grt_current_user
from ..config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from ..rag.ingest import process_pdf
from ..rag.retrieve import delete_document_vectors


setting = get_settings()

router = APIRouter()

async def  fond_by_hash(session:AsyncSession,user_id:int,file_hash:str):
    loader = await session.execute(select(Documnet).where(Documnet.file_hash==file_hash,Documnet.user_id==user_id))

    onefile = loader.scalar_one_or_none()
    return onefile



@router.post("/upload")
async def upload(file:UploadFile = File(...),user:User = Depends(grt_current_user),session: AsyncSession=Depends(get_db)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF files are supported")

    content = await file.read()

    file_hash = hashlib.sha256(content).hexdigest()
    isFile = await fond_by_hash(session,user.id,file_hash)

    if isFile:
        return {"status":"Dublicate"}

    user_dir = os.path.join(setting.UPLOAD_DIR,str(user.id))
    os.makedirs(user_dir,exist_ok=True)
    path = os.path.join(user_dir,file.filename)
    with open(path,"wb") as f:
        f.write(content)

    doc = Documnet(user_id=user.id,filename = file.filename,file_hash = file_hash,path=path,status="processing")

    

    pages =  await process_pdf(user.id,doc.id,path,file.filename)
    doc.status = "ready"
    doc.pages = pages

   

    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    return {"status":"succesully"}



@router.get("/read")
async def read(user: User = Depends(grt_current_user), session: AsyncSession = Depends(get_db)):
    files= (await session.scalars(select(Documnet).where(Documnet.user_id == user.id))).all()

    f_list = []
    for file in files:
        f_list.append({"file":file.filename,"id":file.id})


    
    return {"files":f_list}

                
    
@router.delete("/delete/{doc_id}")
async def delete(doc_id: int, user: User = Depends(grt_current_user), session: AsyncSession = Depends(get_db)):
    doc = await session.get(Documnet, doc_id)
    if not doc or doc.user_id != user.id:
        
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    


    await delete_document_vectors(doc_id) 
   

    if doc.path.startswith(setting.UPLOAD_DIR) and os.path.exists(doc.path):
        os.remove(doc.path)                      
    await session.delete(doc)
    await session.commit()
    return {"deleted": doc_id}







