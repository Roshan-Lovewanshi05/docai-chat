from ..config import get_settings
setting = get_settings()
import cohere

from langchain_groq import ChatGroq
from  qdrant_client import AsyncQdrantClient,models
from qdrant_client import QdrantClient




def groq_client() -> ChatGroq:
    return ChatGroq(api_key=setting.GROQ_API_KEY,model=setting.LLM_GROQ_MODEL)
def groq_clientNormal() -> ChatGroq:
    return ChatGroq(api_key=setting.GROQ_API_KEY,model=setting.LLM_GROQ_MODEL_OPENAI)

def cohere_client() -> cohere.AsyncClientV2:
    return cohere.AsyncClientV2(api_key=setting.COHERE_API_KEY)

def qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient( url=setting.QDRANT_URL, 
        api_key=setting.QDRANT_API_KEY)





async def ensure_collection() -> None:
    qdr = qdrant_client()
    collection = setting.QDRANR_collection

    if not await qdr.collection_exists(collection):
        await qdr.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": models.VectorParams(
                    size=setting.EMBED_DIM,
                    distance=models.Distance.COSINE,
                    hnsw_config=models.HnswConfigDiff(
                        m=16,
                        ef_construct=100
                    )
                )
            },
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            }
        )

        print("INFO: Collection created.")

    # Create the index required for filtering by user_id
    await qdr.create_payload_index(
        collection_name=collection,
        field_name="user_id",
        field_schema=models.PayloadSchemaType.INTEGER,
        wait=True
    )

    print("INFO: user_id index is ready.")

    

    await qdr.create_payload_index(
    collection_name=collection,
    field_name="doc_id",
    field_schema=models.PayloadSchemaType.INTEGER,
    wait=True
    )

    print("INFO: doc_id index is ready.")

    await qdr.close()


