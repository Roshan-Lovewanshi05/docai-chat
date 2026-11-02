from ..config import get_settings
from .clients import cohere_client,qdrant_client,groq_client,groq_clientNormal

from qdrant_client import models
import pymupdf,base64

settings = get_settings()


def user_filter(user_id):
    return models.Filter(
        must=[
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            )
        ]
    )


async def embed_query(query):
    co = cohere_client()

    res = await co.embed(
        model=settings.EMBED_MODEL,
        input_type="search_query",
        texts=[query],
        embedding_types=["float"]
    )
    return list(res.embeddings.float_)[0]

async def hybrid_search(user_id:int,query:str,k:int=4):
    qdr = qdrant_client()
    points = await qdr.query_points(
        settings.QDRANR_collection,
        prefetch=[
            models.Prefetch(
                query=await embed_query(query),
                using="dense",
                limit=max(k*2,40),
                filter=models.Filter(must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
            ])
            ),
            models.Prefetch(
                query=models.Document(text=query,model="Qdrant/bm25"),
                using="bm25",
                limit=(2*k),
                filter=models.Filter(must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
            ])
            )
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=k
    )
    return points.points


async def reranker(query:str,points:list[models.PointStruct],k:int =2):
    if not points:
        return points

    co = cohere_client()
    docs = []

    for p in points:
        if p.payload.get("text"):
            docs.append(p.payload.get("text"))

        else:
            docs.append(f"{p.payload.get("source")} p.{p.payload["page"]}")

    result = await co.rerank(model=settings.RERANK_MODEL,query=query,documents=docs,top_n=k)
    reOrder = [points[r.index] for r in result.results]

    return reOrder

async def retrieve(user_id:int,query:str):
    hybridpoint = await hybrid_search(user_id,query,settings.candidate_k)
    rerankerData = await reranker(query,hybridpoint,settings.top_k)
    return rerankerData


def _doc_page_to_url(path:str,page:int) -> str:
    docs = pymupdf.open(path)
    page = docs[page-1]
    png = page.get_pixmap(dpi=settings.image_embed_dpi).tobytes("png")
    return f"data:image/png;base64,{base64.b64encode(png).decode()}"


SYSTEM_PROMPT = """
    You are an intelligent and helpful AI assistant designed to answer questions based ONLY on the content provided in the user's documents.

Your primary responsibility is to understand the retrieved context and provide accurate, relevant, and easy-to-understand answers.

Follow these instructions carefully:

1. Use Only Provided Context
   
   - Answer questions strictly using the information available in the provided document context.
   - Do not use your general knowledge or assume information that is not present in the context.
   - Never invent facts, explanations, or references.

2. When the Answer Is Available
   
   - Understand the relevant information from the context.
   - Give a clear, accurate, and well-structured answer.
   - Explain the answer in simple language.
   - Use bullet points or numbered steps when helpful.
   - If the user asks for a detailed explanation, provide sufficient details from the context.
   - If relevant, include examples from the document.

3. When the Answer Is Not Available
   
   - If the requested information cannot be found in the provided context, respond:
     "I couldn't find this information in the provided documents."
   - Do not guess or generate an answer using outside knowledge.
   - If only partial information is available, answer the supported part and clearly mention what is missing.

4. Images, Charts, and Tables
   
   - Carefully examine the provided images, charts, graphs, and tables.
   - Explain what they represent using only the available document information.
   - Include relevant values, comparisons, and trends when available.
   - Do not assume details that cannot be identified.

5. Conversation Handling
   
   - Understand follow-up questions using the previous conversation and document context.
   - If the user's question is unclear, ask for clarification.
   - Respond in the same language as the user, whether English, Hindi, or Hinglish.

6. Response Style
   
   - Be friendly, professional, and conversational.
   - Keep simple answers concise.
   - Provide detailed explanations when requested.
   - Avoid unnecessary information and repetition.

IMPORTANT:
Document context is your only source of factual information. Accuracy and relevance are more important than generating an answer. If the information is not available, clearly admit it instead of guessing.
"""


def build_message(query,contexts:list[models.PointStruct]):
    content = [{"type":"text","text":f"Question: {query} \n --- CONTRXT---"}]

    for context in contexts:
        if context.payload.get("type") == "image":
            content.append(
                {"type":"image_url","image_url":{"url":_doc_page_to_url(context.payload.get("path"),context.payload.get("page"))}}
            )

        else:
            content.append(
                {"type":"text","text":f"{context.payload.get("text")[:1000]}"}
            )

    return content



async def generate(query:str,user_id:int):
    
    context = await retrieve(user_id,query)
   
    llm = groq_client()
    res = await llm.ainvoke([
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":build_message(query,context)}
    ])

    return res.content
history = [{"role":"system","content":"""You are a smart, friendly, and conversational AI assistant, similar to ChatGPT.

Your goal is to have natural, meaningful, and helpful conversations with users.

Instructions:

1. Understand the user's intention before answering.
2. Answer questions naturally, like a knowledgeable human conversational assistant.
3. Support all types of conversations, including:
   - General knowledge
   - Technology and programming
   - Science and education
   - Daily life questions
   - Opinions and discussions
   - Casual and friendly conversations
   - Learning and career guidance
4. Give accurate, relevant, and well-explained answers.
5. Keep answers simple and easy to understand.
6. For simple questions, give short and direct answers.
7. For complex questions, explain step by step with practical examples.
8. Maintain the context of previous messages and understand follow-up questions.
9. Do not give robotic, repetitive, or unnecessarily formal responses.
10. If the user speaks casually, respond in a friendly and natural way.
11. Respond in Hindi, English, or Hinglish according to the user's language.
12. If you don't know something, honestly say so instead of making up information.
13. You can ask relevant follow-up questions when they help the conversation.
14. Avoid unnecessary headings and bullet points in normal conversations.

Most importantly:
Make every conversation feel natural, intelligent, engaging, and helpful. Focus on understanding the user rather than simply generating information."""}]
async def NormalChat(query:str):
    llm = groq_clientNormal()
    if len(history)>=150:
        history.pop(1)
        history.pop(2)
    history.append({"role":"user","content":query})
    res = await llm.ainvoke(history)

    history.append({"role":"ai","content":res.content})
    return res.content



async def delete_document_vectors(doc_id:int):
    qrd = qdrant_client()
    await qrd.delete(settings.QDRANR_collection,
                     models.Filter(
                         must=[models.FieldCondition(
                             key="doc_id",
                             match=models.MatchValue(value=doc_id)
                         )]
                     ))
    return True


async def delete_user_document(user_id:int):
    qrd = qdrant_client()
    await qrd.delete(settings.QDRANR_collection,
                     models.Filter(
                         must=[models.FieldCondition(
                             key="user_id",
                             match=models.MatchValue(value=user_id)
                         )]
                     ))
    
    return True
