"""
Enhanced S1000D QA API with ChromaDB, OCR, and advanced PDF processing
This is the new version integrating all enhanced components
"""
import os
import json
import traceback
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import ollama

# Import new modules
from config import config
from vector_store import get_vector_store
from document_indexer import DocumentIndexer
from pdf_processor import EnhancedPDFProcessor
from logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute", "1000/hour"])

# Create FastAPI app
app = FastAPI(
    title="S1000D QA API - Enhanced",
    description="Enhanced API for querying S1000D documentation with ChromaDB, OCR, and advanced processing",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-XSRF-TOKEN"],
    max_age=3600,
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if "server" in response.headers:
        del response.headers["server"]
    return response

# Global state
indexer: Optional[DocumentIndexer] = None
index_status = {
    "is_indexed": False,
    "index_stats": {},
    "last_indexed": None
}

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    translate: bool = False
    page: int = 1
    page_size: int = 10
    language: str = "en"
    filter_chapter: Optional[str] = None
    filter_content_type: Optional[str] = None
    min_importance: Optional[int] = None
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v.strip()) > 5000:
            raise ValueError('Query too long (max 5000 characters)')
        return v.strip()

class AIQueryRequest(BaseModel):
    query: str
    context_limit: int = 15
    translate: bool = False
    language: str = "en"
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class AIQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    processing_time: float
    model_used: str = "llama3.2:3b"

class QueryResponse(BaseModel):
    answers: List[Dict[str, Any]]
    answer_count: int
    total_results: int
    current_page: int
    total_pages: int
    search_time: float

class IndexRequest(BaseModel):
    start_page: Optional[int] = 1
    end_page: Optional[int] = None
    force_reindex: bool = False

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global indexer, index_status

    logger.info("Starting Enhanced S1000D QA API v2.0")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Vector Store: {config.VECTOR_STORE_TYPE}")
    logger.info(f"OCR Enabled: {config.OCR_ENABLED}")
    logger.info(f"PDF Path: {config.PDF_PATH}")

    print("\n" + "="*60)
    print("Starting Enhanced S1000D QA API v2.0")
    print("="*60)
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Vector Store: {config.VECTOR_STORE_TYPE}")
    print(f"OCR Enabled: {config.OCR_ENABLED}")
    print(f"PDF Path: {config.PDF_PATH}")
    print("="*60 + "\n")
    
    try:
        # Initialize indexer
        indexer = DocumentIndexer()
        
        # Check if already indexed
        vector_store = get_vector_store()
        stats = vector_store.get_collection_stats()
        
        if stats.get("document_count", 0) > 0:
            print(f"Found existing index with {stats['document_count']} documents")
            index_status["is_indexed"] = True
            index_status["index_stats"] = stats
            print("Skipping indexing (already indexed)")
        else:
            print("No existing index found")
            print("Use /reindex endpoint to index documents")
        
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        traceback.print_exc()

# Health check endpoint
@app.get("/health")
@limiter.exempt
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": config.ENVIRONMENT,
        "vector_store": config.VECTOR_STORE_TYPE,
        "ocr_enabled": config.OCR_ENABLED,
        "indexed": index_status["is_indexed"],
        "models": {
            "embedding": config.EMBEDDING_MODEL,
            "llm": "llama3.2:3b (local)"
        }
    }

# Index status endpoint
@app.get("/index-status")
async def get_index_status():
    """Get current index status"""
    return {
        "status": "ok",
        "is_indexed": index_status["is_indexed"],
        "stats": index_status["index_stats"],
        "last_indexed": index_status["last_indexed"],
        "pdf_path": config.PDF_PATH,
        "pdf_exists": os.path.exists(config.PDF_PATH)
    }

# Reindex endpoint
@app.post("/reindex")
async def reindex_documents(request: IndexRequest):
    """Reindex PDF documents"""
    global indexer, index_status
    
    if not indexer:
        raise HTTPException(status_code=500, detail="Indexer not initialized")
    
    try:
        print("\n" + "="*60)
        print("Starting document reindexing...")
        print("="*60 + "\n")
        
        # Delete existing collection if force reindex
        if request.force_reindex:
            print("Force reindex requested - deleting existing collection")
            indexer.vector_store.delete_collection()
            # Reinitialize
            indexer = DocumentIndexer()
        
        # Process and index
        stats = indexer.process_and_index(
            start_page=request.start_page,
            end_page=request.end_page
        )
        
        # Update status
        index_status["is_indexed"] = True
        index_status["index_stats"] = stats
        index_status["last_indexed"] = time.time()
        
        return {
            "status": "success",
            "message": "Documents indexed successfully",
            "stats": stats
        }
    
    except Exception as e:
        print(f"Error during reindexing: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")

# Search endpoint
@app.post("/query", response_model=QueryResponse)
@limiter.limit("50/minute")
async def handle_query(request: QueryRequest):
    """Handle search query"""
    logger = get_logger()

    if not indexer or not index_status["is_indexed"]:
        logger.warning("Query attempted but index not available")
        raise HTTPException(
            status_code=503,
            detail="Index not available. Please run /reindex first"
        )

    try:
        start_time = time.time()
        logger.info(f"Processing query: '{request.query[:50]}...' (page: {request.page}, size: {request.page_size})")
        
        # Search
        results = indexer.search(
            query=request.query,
            k=request.page_size * request.page,
            filter_by_chapter=request.filter_chapter,
            filter_by_content_type=request.filter_content_type,
            min_importance=request.min_importance
        )
        
        search_time = time.time() - start_time
        
        # Paginate results
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_results = results[start_idx:end_idx]
        
        # Format results
        answers = []
        for result in page_results:
            answers.append({
                "text": result["text"],
                "page": result["metadata"].get("page", 0),
                "module": result["metadata"].get("chapter", ""),
                "score": float(result["score"]),
                "content_type": result["metadata"].get("content_type", "text"),
                "importance": result["metadata"].get("importance", 1)
            })
        
        total_pages = max(1, (len(results) + request.page_size - 1) // request.page_size)
        
        return QueryResponse(
            answers=answers,
            answer_count=len(answers),
            total_results=len(results),
            current_page=request.page,
            total_pages=total_pages,
            search_time=search_time
        )
    
    except Exception as e:
        print(f"Error in query: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# AI Query endpoint
@app.post("/ai-query", response_model=AIQueryResponse)
@limiter.limit("20/minute")
async def ai_query_documents(request: AIQueryRequest):
    """AI-powered query with LLM"""
    if not indexer or not index_status["is_indexed"]:
        raise HTTPException(
            status_code=503,
            detail="Index not available. Please run /reindex first"
        )
    
    try:
        start_time = time.time()
        
        # Search for relevant context
        results = indexer.search(
            query=request.query,
            k=request.context_limit
        )
        
        # Build context for LLM
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(
                f"[Document {i+1}]\n"
                f"Chapter: {result['metadata'].get('chapter', 'Unknown')}\n"
                f"Page: {result['metadata'].get('page', 'Unknown')}\n"
                f"Content: {result['text']}\n"
            )
        
        context = "\n".join(context_parts)
        
        # Generate response with Ollama
        prompt = f"""You are an expert assistant for S1000D documentation.

Context from S1000D documentation:
{context}

User question: {request.query}

Please provide a clear, accurate answer based on the context provided. If the information is not in the context, say so."""
        
        try:
            response = ollama.chat(
                model='llama3.2:3b',
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                options={
                    'temperature': 0.5,
                    'num_predict': 500
                }
            )
            answer = response['message']['content']
        except Exception as e:
            print(f"Ollama error: {str(e)}")
            answer = f"Sorry, I encountered an error generating a response: {str(e)}"
        
        processing_time = time.time() - start_time
        
        # Format sources
        sources = [
            {
                "page": result["metadata"].get("page", 0),
                "chapter": result["metadata"].get("chapter", ""),
                "score": float(result["score"]),
                "content_type": result["metadata"].get("content_type", "text")
            }
            for result in results[:5]
        ]
        
        return AIQueryResponse(
            answer=answer,
            sources=sources,
            processing_time=processing_time,
            model_used="llama3.2:3b (local)"
        )
    
    except Exception as e:
        print(f"Error in AI query: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI query failed: {str(e)}")

# Root endpoint
@app.get("/")
@limiter.exempt
def read_root():
    """Root endpoint"""
    return {
        "message": "S1000D QA API - Enhanced Version 2.0",
        "docs": "/docs",
        "health": "/health",
        "status": "/index-status"
    }

if __name__ == "__main__":
    uvicorn.run("app_new:app", host="0.0.0.0", port=8000, reload=True)

