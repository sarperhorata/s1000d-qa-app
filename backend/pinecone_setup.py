import pinecone
from pinecone import Pinecone, ServerlessSpec
import openai
from tqdm import tqdm
import json
import os
from typing import List, Dict, Any
import PyPDF2
import re

# Pinecone configuration
PINECONE_API_KEY = "pcsk_4kXPC7_R9tgkfgiqXmjDw8Usd6K2WVDkeJHfEZpY5TnuLk4G5WNyfv22PALd12QVtzqNX2"
PINECONE_ENVIRONMENT = "gcp-starter"  # Free tier environment
INDEX_NAME = "s1000d-docs"
PINECONE_INDEX_URL = "https://s1000dv2-p9v7xql.svc.aped-4627-b74a.pinecone.io"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def initialize_pinecone():
    """Initialize Pinecone with the API key and environment"""
    try:
        # Initialize Pinecone client
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, if not create it
        if INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=INDEX_NAME,
                dimension=1536,  # OpenAI ada-002 embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        return pc.Index(INDEX_NAME, url=PINECONE_INDEX_URL)
    except Exception as e:
        print(f"Error initializing Pinecone: {str(e)}")
        raise

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI's API"""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        raise

def process_pdf_content(pdf_path: str) -> List[Dict[str, Any]]:
    """Process PDF content and return structured data"""
    documents = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text and text.strip():
                    # Extract chapter information
                    chapter_match = re.search(r'Chapter\s+(\d+\.\d+(?:\.\d+)?)', text)
                    chapter = chapter_match.group(1) if chapter_match else "Unknown"
                    
                    # Create document structure
                    doc = {
                        "text": text,
                        "metadata": {
                            "page": page_num + 1,
                            "chapter": chapter,
                            "type": "text"
                        }
                    }
                    documents.append(doc)
                    
                    # TODO: Add processing for tables, figures, and code blocks
                    # This will be implemented in the next phase
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise
    
    return documents

def upload_to_pinecone(documents: List[Dict[str, Any]], index):
    """Upload documents to Pinecone"""
    try:
        for i, doc in enumerate(tqdm(documents, desc="Uploading to Pinecone")):
            # Get embedding for the text
            embedding = get_embedding(doc["text"])
            
            # Prepare metadata
            metadata = {
                **doc["metadata"],
                "text": doc["text"][:1000]  # Store first 1000 chars of text in metadata
            }
            
            # Upload to Pinecone
            index.upsert(
                vectors=[(f"doc_{i}", embedding, metadata)]
            )
            
    except Exception as e:
        print(f"Error uploading to Pinecone: {str(e)}")
        raise

def search_pinecone(query: str, index, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search Pinecone index with a query"""
    try:
        # Get query embedding
        query_embedding = get_embedding(query)
        
        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results.matches
    
    except Exception as e:
        print(f"Error searching Pinecone: {str(e)}")
        raise

if __name__ == "__main__":
    # Initialize Pinecone
    index = initialize_pinecone()
    
    # Process PDF and upload to Pinecone
    pdf_path = "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"
    documents = process_pdf_content(pdf_path)
    upload_to_pinecone(documents, index)
    
    print("Setup completed successfully!") 