"""
Test script for enhanced S1000D QA system
Tests all major components
"""
import os
import time

print("="*60)
print("Testing Enhanced S1000D QA System")
print("="*60)

# Test 1: Config
print("\n[Test 1] Testing Config Module...")
try:
    from config import config
    print(f"✓ Config loaded")
    print(f"  Environment: {config.ENVIRONMENT}")
    print(f"  Vector Store: {config.VECTOR_STORE_TYPE}")
    print(f"  OCR Enabled: {config.OCR_ENABLED}")
except Exception as e:
    print(f"✗ Config test failed: {str(e)}")
    exit(1)

# Test 2: Vector Store
print("\n[Test 2] Testing Vector Store...")
try:
    from vector_store import get_vector_store
    store = get_vector_store()
    stats = store.get_collection_stats()
    print(f"✓ Vector store initialized")
    print(f"  Collection: {stats.get('collection_name')}")
    print(f"  Documents: {stats.get('document_count')}")
    print(f"  Storage: {stats.get('persist_directory')}")
except Exception as e:
    print(f"✗ Vector store test failed: {str(e)}")
    exit(1)

# Test 3: PDF Processor
print("\n[Test 3] Testing PDF Processor...")
try:
    from pdf_processor import EnhancedPDFProcessor
    pdf_path = config.PDF_PATH
    
    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found: {pdf_path}")
        exit(1)
    
    processor = EnhancedPDFProcessor(pdf_path, enable_ocr=False)
    info = processor.get_pdf_info()
    print(f"✓ PDF processor initialized")
    print(f"  File: {info['filename']}")
    print(f"  Pages: {info['page_count']}")
    print(f"  Size: {info['file_size_mb']} MB")
except Exception as e:
    print(f"✗ PDF processor test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: OCR Processor
print("\n[Test 4] Testing OCR Processor...")
try:
    from ocr_processor import OCRProcessor
    ocr = OCRProcessor(engine="tesseract")
    print(f"✓ OCR processor initialized")
    print(f"  Engine: {ocr.engine if ocr.engine else 'Not available'}")
    print(f"  Available: {ocr.is_available()}")
except Exception as e:
    print(f"⚠ OCR processor test warning: {str(e)}")

# Test 5: Document Indexer
print("\n[Test 5] Testing Document Indexer...")
try:
    from document_indexer import DocumentIndexer
    indexer = DocumentIndexer()
    print(f"✓ Document indexer initialized")
    
    # Check if already indexed
    if stats.get('document_count', 0) > 0:
        print(f"  Status: Already indexed ({stats['document_count']} docs)")
        
        # Test search
        print("\n[Test 6] Testing Search...")
        test_query = "What is S1000D?"
        results = indexer.search(test_query, k=3)
        print(f"✓ Search test passed")
        print(f"  Query: '{test_query}'")
        print(f"  Results: {len(results)}")
        
        if results:
            print(f"\n  Top result:")
            top = results[0]
            print(f"    Score: {top['score']:.3f}")
            print(f"    Page: {top['metadata'].get('page')}")
            print(f"    Chapter: {top['metadata'].get('chapter')}")
            print(f"    Text: {top['text'][:100]}...")
    else:
        print(f"  Status: Not indexed yet")
        print(f"  Run 'python document_indexer.py --test' to index")
    
except Exception as e:
    print(f"✗ Document indexer test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: API Server (optional)
print("\n[Test 7] Testing API Server...")
try:
    from app_new import app
    print(f"✓ API application loaded")
    print(f"  Endpoints available:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            print(f"    {methods:10} {route.path}")
except Exception as e:
    print(f"✗ API server test failed: {str(e)}")

print("\n" + "="*60)
print("All Tests Completed!")
print("="*60)
print("\nNext Steps:")
print("1. Run full indexing: python document_indexer.py --no-ocr")
print("2. Start API server: python app_new.py")
print("3. Access API docs: http://localhost:8000/docs")
print("="*60)


