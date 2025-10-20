"""
Document Indexer for S1000D QA application
Orchestrates PDF processing, chunking, and indexing with vector store
"""
import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import config
from pdf_processor import EnhancedPDFProcessor, ContentBlock
from vector_store import get_vector_store, VectorStore
from azure_storage import setup_azure_storage_for_pdf


class ContentAwareChunker:
    """Content-aware chunking strategy for different content types"""
    
    def __init__(self):
        """Initialize chunker with different strategies for different content types"""
        # Text chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
        )
        
        # Heading chunking (smaller, less overlap)
        self.heading_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n", " "]
        )
        
        # List chunking (preserve list structure)
        self.list_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n"]
        )
    
    def chunk_content_block(self, block: ContentBlock) -> List[Dict[str, Any]]:
        """
        Chunk a content block based on its type
        
        Args:
            block: Content block to chunk
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Tables and diagrams are not chunked (keep complete)
        if block.content_type in ["table", "diagram"]:
            chunks.append({
                "text": block.text,
                "metadata": {
                    "page": block.page,
                    "chapter": block.chapter,
                    "content_type": block.content_type,
                    "importance": block.importance,
                    "chunked": False,
                    **block.metadata
                }
            })
            return chunks
        
        # Choose splitter based on content type
        if block.content_type == "heading":
            splitter = self.heading_splitter
        elif block.content_type == "list":
            splitter = self.list_splitter
        else:
            splitter = self.text_splitter
        
        # Split text
        text_chunks = splitter.split_text(block.text)
        
        # Create chunks with metadata
        for i, text_chunk in enumerate(text_chunks):
            chunks.append({
                "text": text_chunk,
                "metadata": {
                    "page": block.page,
                    "chapter": block.chapter,
                    "content_type": block.content_type,
                    "importance": block.importance,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "chunked": True,
                    **block.metadata
                }
            })
        
        return chunks
    
    def chunk_blocks(self, blocks: List[ContentBlock]) -> List[Dict[str, Any]]:
        """
        Chunk multiple content blocks
        
        Args:
            blocks: List of content blocks
            
        Returns:
            List of all chunks
        """
        all_chunks = []
        
        for block in blocks:
            block_chunks = self.chunk_content_block(block)
            all_chunks.extend(block_chunks)
        
        return all_chunks


class DocumentIndexer:
    """Orchestrates document processing and indexing"""
    
    def __init__(
        self,
        pdf_path: str = None,
        vector_store: VectorStore = None,
        enable_ocr: bool = None
    ):
        """
        Initialize document indexer
        
        Args:
            pdf_path: Path to PDF file
            vector_store: Vector store instance
            enable_ocr: Enable OCR for images
        """
        # Setup PDF path (from config or Azure)
        self.pdf_path = pdf_path or self._setup_pdf_path()
        
        # Initialize vector store
        self.vector_store = vector_store or get_vector_store()
        
        # Initialize PDF processor
        self.pdf_processor = EnhancedPDFProcessor(
            self.pdf_path,
            enable_ocr=enable_ocr if enable_ocr is not None else config.OCR_ENABLED
        )
        
        # Initialize chunker
        self.chunker = ContentAwareChunker()
        
        # Statistics
        self.stats = {
            "total_pages": 0,
            "total_blocks": 0,
            "total_chunks": 0,
            "processing_time": 0,
            "indexing_time": 0
        }
    
    def _setup_pdf_path(self) -> str:
        """Setup PDF path from config or Azure"""
        # Try config path first
        pdf_path = config.PDF_PATH
        
        if os.path.exists(pdf_path):
            return pdf_path
        
        # Try Azure if running in Azure environment
        if config.is_azure():
            print("Attempting to download PDF from Azure Blob Storage...")
            azure_pdf_path = setup_azure_storage_for_pdf()
            if azure_pdf_path:
                return azure_pdf_path
        
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    def process_and_index(
        self,
        start_page: int = 1,
        end_page: Optional[int] = None,
        batch_size: int = None
    ) -> Dict[str, Any]:
        """
        Process PDF and index documents
        
        Args:
            start_page: Starting page (1-indexed)
            end_page: Ending page (None for all)
            batch_size: Batch size for indexing
            
        Returns:
            Statistics dictionary
        """
        batch_size = batch_size or config.BATCH_SIZE
        
        print(f"\n{'='*60}")
        print(f"Document Indexing Started")
        print(f"{'='*60}")
        print(f"PDF: {os.path.basename(self.pdf_path)}")
        print(f"Vector Store: {type(self.vector_store).__name__}")
        print(f"OCR Enabled: {self.pdf_processor.enable_ocr}")
        print(f"{'='*60}\n")
        
        # Get PDF info
        pdf_info = self.pdf_processor.get_pdf_info()
        self.stats["total_pages"] = pdf_info.get("page_count", 0)
        
        # Process PDF
        print("Phase 1: Processing PDF...")
        start_time = time.time()
        
        blocks = self.pdf_processor.process_pdf(
            start_page=start_page,
            end_page=end_page
        )
        
        processing_time = time.time() - start_time
        self.stats["processing_time"] = processing_time
        self.stats["total_blocks"] = len(blocks)
        
        print(f"\nProcessing complete in {processing_time:.2f}s")
        print(f"Extracted {len(blocks)} content blocks")
        
        # Content type distribution
        content_types = {}
        for block in blocks:
            content_types[block.content_type] = content_types.get(block.content_type, 0) + 1
        
        print("\nContent Type Distribution:")
        for content_type, count in sorted(content_types.items()):
            print(f"  {content_type}: {count}")
        
        # Chunk blocks
        print("\nPhase 2: Chunking content...")
        chunks = self.chunker.chunk_blocks(blocks)
        self.stats["total_chunks"] = len(chunks)
        
        print(f"Created {len(chunks)} chunks")
        
        # Index chunks
        print("\nPhase 3: Indexing to vector store...")
        start_time = time.time()
        
        # Prepare data for indexing
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Index in batches
        total_indexed = 0
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            
            batch_texts = texts[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]
            
            self.vector_store.add_documents(
                texts=batch_texts,
                metadatas=batch_metadatas
            )
            
            total_indexed += len(batch_texts)
            print(f"Indexed {total_indexed}/{len(texts)} chunks...")
        
        indexing_time = time.time() - start_time
        self.stats["indexing_time"] = indexing_time
        
        print(f"\nIndexing complete in {indexing_time:.2f}s")
        
        # Final statistics
        total_time = processing_time + indexing_time
        
        print(f"\n{'='*60}")
        print(f"Indexing Complete!")
        print(f"{'='*60}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Pages processed: {self.stats['total_pages']}")
        print(f"Content blocks: {self.stats['total_blocks']}")
        print(f"Chunks created: {self.stats['total_chunks']}")
        print(f"Processing rate: {self.stats['total_pages']/processing_time:.2f} pages/sec")
        print(f"Indexing rate: {self.stats['total_chunks']/indexing_time:.2f} chunks/sec")
        print(f"{'='*60}\n")
        
        return self.stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        return self.stats
    
    def search(
        self,
        query: str,
        k: int = 10,
        filter_by_chapter: Optional[str] = None,
        filter_by_content_type: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search indexed documents
        
        Args:
            query: Search query
            k: Number of results
            filter_by_chapter: Filter by chapter
            filter_by_content_type: Filter by content type
            min_importance: Minimum importance score
            
        Returns:
            List of search results
        """
        # Build filter
        filter_dict = {}
        if filter_by_chapter:
            filter_dict["chapter"] = filter_by_chapter
        if filter_by_content_type:
            filter_dict["content_type"] = filter_by_content_type
        if min_importance:
            filter_dict["importance"] = {"$gte": min_importance}
        
        # Search
        results = self.vector_store.search(
            query=query,
            k=k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        return results


# Command-line interface for testing
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Index S1000D PDF documents")
    parser.add_argument("--pdf", type=str, help="Path to PDF file")
    parser.add_argument("--start-page", type=int, default=1, help="Start page")
    parser.add_argument("--end-page", type=int, help="End page")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR")
    parser.add_argument("--test", action="store_true", help="Test mode (first 10 pages)")
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        print("Running in TEST mode (first 10 pages only)\n")
        args.end_page = 10
    
    # Initialize indexer
    try:
        indexer = DocumentIndexer(
            pdf_path=args.pdf,
            enable_ocr=not args.no_ocr
        )
        
        # Process and index
        stats = indexer.process_and_index(
            start_page=args.start_page,
            end_page=args.end_page
        )
        
        # Test search
        print("\n" + "="*60)
        print("Testing Search Functionality")
        print("="*60)
        
        test_queries = [
            "What is S1000D?",
            "Business rules",
            "Data module code"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = indexer.search(query, k=3)
            
            for i, result in enumerate(results[:3]):
                print(f"\n  Result {i+1}:")
                print(f"    Score: {result['score']:.3f}")
                print(f"    Page: {result['metadata'].get('page')}")
                print(f"    Chapter: {result['metadata'].get('chapter')}")
                print(f"    Type: {result['metadata'].get('content_type')}")
                print(f"    Text: {result['text'][:100]}...")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


