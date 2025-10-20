"""
Simplified S1000D QA API for Batuhan
Minimal dependencies, easy to understand, XML-first approach
Total: ~150 lines of simple, readable code
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import lxml.etree as ET
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import uvicorn

app = FastAPI(title="S1000D QA - Simple", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class SimpleIndexer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.documents = []
        self.metadata = []
        self.tfidf_matrix = None
    
    def index_xml_files(self, xml_dir: str):
        """Index all XML files in directory"""
        print(f"Indexing XML files from: {xml_dir}")
        
        for xml_file in Path(xml_dir).glob("**/*.XML"):
            try:
                tree = ET.parse(str(xml_file))
                
                # Extract all text content
                text_parts = tree.xpath('//text()')
                text = ' '.join([t.strip() for t in text_parts if t.strip()])
                
                if text:
                    self.documents.append(text)
                    self.metadata.append({
                        'file': xml_file.name,
                        'type': 'xml',
                        'path': str(xml_file)
                    })
            except Exception as e:
                print(f"Error parsing {xml_file.name}: {e}")
        
        # Build TF-IDF matrix
        if self.documents:
            print(f"Building TF-IDF index for {len(self.documents)} documents...")
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            print("Indexing complete!")
    
    def index_pdf_fallback(self, pdf_path: str):
        """Index PDF as fallback (simple extraction)"""
        import fitz  # PyMuPDF
        
        print(f"Indexing PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            if text.strip():
                self.documents.append(text)
                self.metadata.append({
                    'page': page_num + 1,
                    'type': 'pdf',
                    'path': pdf_path
                })
        
        doc.close()
        
        # Rebuild index
        if self.documents:
            print(f"Building TF-IDF index for {len(self.documents)} documents...")
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            print("Indexing complete!")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using TF-IDF"""
        if self.tfidf_matrix is None:
            return []
        
        # Transform query
        query_vec = self.vectorizer.transform([query])
        
        # Calculate similarity
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        # Get top results
        top_indices = scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0.01:  # Minimum relevance threshold
                results.append({
                    'text': self.documents[idx][:500] + '...',
                    'score': float(scores[idx]),
                    'metadata': self.metadata[idx]
                })
        
        return results

# Global indexer instance
indexer = SimpleIndexer()

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    query: str

# Endpoints
@app.get("/health")
def health_check():
    """Health check"""
    return {
        "status": "ok",
        "indexed_documents": len(indexer.documents),
        "index_ready": indexer.tfidf_matrix is not None
    }

@app.get("/stats")
def get_stats():
    """Get indexing statistics"""
    xml_count = sum(1 for m in indexer.metadata if m['type'] == 'xml')
    pdf_count = sum(1 for m in indexer.metadata if m['type'] == 'pdf')
    
    return {
        "total_documents": len(indexer.documents),
        "xml_documents": xml_count,
        "pdf_documents": pdf_count,
        "vocabulary_size": len(indexer.vectorizer.vocabulary_) if indexer.tfidf_matrix is not None else 0
    }

@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    """Search indexed documents"""
    if indexer.tfidf_matrix is None:
        raise HTTPException(status_code=503, detail="Index not ready")
    
    results = indexer.search(request.query, request.top_k)
    
    return SearchResponse(
        results=results,
        count=len(results),
        query=request.query
    )

@app.post("/index-xml")
def index_xml(xml_dir: str):
    """Index XML files from directory"""
    if not Path(xml_dir).exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    indexer.index_xml_files(xml_dir)
    
    return {
        "status": "success",
        "indexed": len(indexer.documents)
    }

@app.post("/index-pdf")
def index_pdf(pdf_path: str):
    """Index PDF file as fallback"""
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    indexer.index_pdf_fallback(pdf_path)
    
    return {
        "status": "success",
        "indexed": len(indexer.documents)
    }

# Startup: Auto-index if paths exist
@app.on_event("startup")
def startup_event():
    """Auto-index on startup"""
    print("\n" + "="*60)
    print("Starting Simple S1000D QA API")
    print("="*60)
    
    # Try to index XML files first
    xml_dir = "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Bike Data Set for Release number 6 R2"
    if Path(xml_dir).exists():
        print("\n📁 Found XML directory, indexing...")
        indexer.index_xml_files(xml_dir)
    
    # If no XML or need more content, try PDF
    if len(indexer.documents) < 100:
        pdf_path = "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"
        if Path(pdf_path).exists():
            print("\n📄 Indexing PDF as fallback...")
            indexer.index_pdf_fallback(pdf_path)
    
    print("\n" + "="*60)
    print(f"✅ Indexing complete: {len(indexer.documents)} documents")
    print("="*60 + "\n")

if __name__ == "__main__":
    uvicorn.run("app_simple:app", host="0.0.0.0", port=8000, reload=True)

