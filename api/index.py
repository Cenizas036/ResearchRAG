from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import logging
from huggingface_hub import AsyncInferenceClient
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ResearchRAG API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

logger = logging.getLogger("ResearchRAG.API")

class QueryRequest(BaseModel):
    query: str

@app.post("/api/query")
async def process_query(request: QueryRequest):
    """
    Serverless Function endpoint for ResearchRAG.
    Uses Hugging Face Free Inference API to generate responses.
    """
    question = request.query
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        # Fallback dummy response if no API key is provided
        return JSONResponse({
            "response": f"Mock Server Response: I received your query '{question}'. Please configure HF_TOKEN to enable live AI responses.",
            "confidence": 1.0,
            "citations": []
        })

    try:
        client = AsyncInferenceClient("Qwen/Qwen2.5-72B-Instruct", token=hf_token)
        messages = [
            {"role": "system", "content": "You are an advanced Research Assistant for ResearchRAG. Answer clearly and concisely. Use Markdown formatting."},
            {"role": "user", "content": question}
        ]
        
        response = await client.chat_completion(messages, max_tokens=800)
        answer = response.choices[0].message.content
        
        return JSONResponse({
            "response": answer,
            "confidence": 0.95,
            "citations": []
        })
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"response": f"An error occurred during generation: {str(e)}"}
        )

# Catch-all for API routing
@app.get("/api/{path:path}")
async def catch_all_api(path: str):
    return JSONResponse({"message": f"API Endpoint /api/{path} is alive."})
