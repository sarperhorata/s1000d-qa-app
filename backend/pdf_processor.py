"""
Enhanced PDF Processor for S1000D QA application
Handles PDF processing with layout detection, content classification, and OCR
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import fitz  # PyMuPDF
from PIL import Image
import io

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("pdfplumber not available. Install with: pip install pdfplumber")

from config import config
from ocr_processor import OCRProcessor


@dataclass
class ContentBlock:
    """Represents a block of content from PDF"""
    text: str
    content_type: str  # text, table, diagram, figure, heading
    page: int
    chapter: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # x0, y0, x1, y1
    importance: int = 1  # 1-5, where 5 is most important
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EnhancedPDFProcessor:
    """Enhanced PDF processor with layout analysis and content classification"""
    
    def __init__(
        self,
        pdf_path: str,
        enable_ocr: bool = None,
        ocr_engine: str = None
    ):
        """
        Initialize PDF processor
        
        Args:
            pdf_path: Path to PDF file
            enable_ocr: Enable OCR for images
            ocr_engine: OCR engine to use
        """
        self.pdf_path = pdf_path
        self.enable_ocr = enable_ocr if enable_ocr is not None else config.OCR_ENABLED
        
        # Initialize OCR processor if enabled
        self.ocr_processor = None
        if self.enable_ocr:
            self.ocr_processor = OCRProcessor(engine=ocr_engine)
        
        # Chapter/section pattern for S1000D
        self.chapter_pattern = re.compile(r'Chapter\s+(\d+\.?\d*\.?\d*\.?\d*)')
        self.section_pattern = re.compile(r'(\d+\.?\d*\.?\d*\.?\d*)\s+[A-Z]')
        
        # Important keywords for S1000D
        self.important_keywords = [
            'business rules', 'data module', 'publication module',
            'applicability', 'brex', 'csdb', 'ietm', 'common source database'
        ]
    
    def detect_content_type(self, text: str, block_info: Dict[str, Any] = None) -> str:
        """
        Detect the type of content block
        
        Args:
            text: Text content
            block_info: Additional block information
            
        Returns:
            Content type (text, table, heading, list)
        """
        if not text or len(text.strip()) < 3:
            return "text"
        
        text_lower = text.lower().strip()
        
        # Check for headings
        if len(text) < 100 and (
            self.chapter_pattern.search(text) or
            self.section_pattern.search(text) or
            text.isupper() or
            (block_info and block_info.get('font_size', 0) > 14)
        ):
            return "heading"
        
        # Check for lists
        if re.match(r'^\s*[\d\-\•\*]\s+', text) or text_lower.startswith(('- ', '• ', '* ')):
            return "list"
        
        # Check for tables (heuristic)
        if '\t' in text or text.count('|') > 3:
            return "table"
        
        return "text"
    
    def calculate_importance(self, content_block: ContentBlock) -> int:
        """
        Calculate importance score for content block
        
        Args:
            content_block: Content block
            
        Returns:
            Importance score (1-5)
        """
        importance = 1
        text_lower = content_block.text.lower()
        
        # Headings are important
        if content_block.content_type == "heading":
            importance = 4
        
        # Chapter markers are very important
        if self.chapter_pattern.search(content_block.text):
            importance = 5
        
        # Important keywords increase importance
        keyword_count = sum(1 for keyword in self.important_keywords if keyword in text_lower)
        if keyword_count > 0:
            importance = min(5, importance + keyword_count)
        
        # Tables with structured data are important
        if content_block.content_type == "table":
            importance = max(importance, 3)
        
        return importance
    
    def extract_chapter_info(self, text: str, current_chapter: str = "Unknown") -> str:
        """
        Extract chapter/section information from text
        
        Args:
            text: Text content
            current_chapter: Current chapter context
            
        Returns:
            Chapter identifier
        """
        # Try to find chapter number
        chapter_match = self.chapter_pattern.search(text)
        if chapter_match:
            return chapter_match.group(1)
        
        # Try to find section number
        section_match = self.section_pattern.search(text)
        if section_match:
            return section_match.group(1)
        
        return current_chapter
    
    def extract_text_blocks_pymupdf(self, page: fitz.Page, page_num: int) -> List[ContentBlock]:
        """
        Extract text blocks from page using PyMuPDF
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of content blocks
        """
        blocks = []
        current_chapter = "Unknown"
        
        # Get text blocks with positions
        text_blocks = page.get_text("blocks")
        
        for block in text_blocks:
            # block format: (x0, y0, x1, y1, "text", block_no, block_type)
            if len(block) < 5:
                continue
            
            x0, y0, x1, y1, text = block[:5]
            
            if not text or not text.strip():
                continue
            
            # Extract chapter info
            chapter = self.extract_chapter_info(text, current_chapter)
            if chapter != "Unknown":
                current_chapter = chapter
            
            # Detect content type
            content_type = self.detect_content_type(text)
            
            # Create content block
            content_block = ContentBlock(
                text=text.strip(),
                content_type=content_type,
                page=page_num,
                chapter=current_chapter,
                bbox=(x0, y0, x1, y1)
            )
            
            # Calculate importance
            content_block.importance = self.calculate_importance(content_block)
            
            blocks.append(content_block)
        
        return blocks
    
    def extract_tables_pdfplumber(self, pdf_path: str, page_num: int) -> List[ContentBlock]:
        """
        Extract tables from page using pdfplumber
        
        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed)
            
        Returns:
            List of table content blocks
        """
        if not PDFPLUMBER_AVAILABLE:
            return []
        
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num <= len(pdf.pages):
                    page = pdf.pages[page_num - 1]
                    extracted_tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(extracted_tables):
                        if not table:
                            continue
                        
                        # Convert table to text
                        table_text = "\n".join([
                            " | ".join([str(cell) if cell else "" for cell in row])
                            for row in table
                        ])
                        
                        content_block = ContentBlock(
                            text=table_text,
                            content_type="table",
                            page=page_num,
                            chapter="Unknown",  # Will be updated by context
                            metadata={"table_index": table_idx, "rows": len(table)}
                        )
                        content_block.importance = 3  # Tables are moderately important
                        
                        tables.append(content_block)
        
        except Exception as e:
            print(f"Error extracting tables from page {page_num}: {str(e)}")
        
        return tables
    
    def extract_images_with_ocr(
        self,
        page: fitz.Page,
        page_num: int,
        current_chapter: str = "Unknown"
    ) -> List[ContentBlock]:
        """
        Extract images and apply OCR if needed
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            current_chapter: Current chapter context
            
        Returns:
            List of image content blocks with OCR text
        """
        if not self.enable_ocr or not self.ocr_processor or not self.ocr_processor.is_available():
            return []
        
        image_blocks = []
        
        try:
            # Get images from page
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = page.parent.extract_image(xref)
                    
                    if not base_image:
                        continue
                    
                    image_bytes = base_image["image"]
                    image_ext = base_image.get("ext", "png")
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Convert to RGB if necessary
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    # Check if OCR should be applied
                    if self.ocr_processor.should_apply_ocr(pil_image, len(image_bytes)):
                        # Extract text using OCR
                        ocr_text = self.ocr_processor.extract_text(pil_image)
                        
                        if ocr_text and len(ocr_text.strip()) > 10:
                            content_block = ContentBlock(
                                text=ocr_text,
                                content_type="diagram",
                                page=page_num,
                                chapter=current_chapter,
                                metadata={
                                    "image_index": img_index,
                                    "image_format": image_ext,
                                    "image_size": len(image_bytes),
                                    "ocr_applied": True
                                }
                            )
                            content_block.importance = 3  # Diagrams with text are important
                            image_blocks.append(content_block)
                
                except Exception as e:
                    print(f"Error processing image {img_index} on page {page_num}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error extracting images from page {page_num}: {str(e)}")
        
        return image_blocks
    
    def process_page(self, page_num: int) -> List[ContentBlock]:
        """
        Process a single page and extract all content blocks
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            List of content blocks from the page
        """
        all_blocks = []
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(self.pdf_path)
            
            if page_num > len(doc):
                doc.close()
                return []
            
            page = doc[page_num - 1]  # 0-indexed
            
            # Extract text blocks
            text_blocks = self.extract_text_blocks_pymupdf(page, page_num)
            all_blocks.extend(text_blocks)
            
            # Get current chapter from text blocks
            current_chapter = "Unknown"
            for block in text_blocks:
                if block.chapter != "Unknown":
                    current_chapter = block.chapter
                    break
            
            # Update chapter for all blocks on this page
            for block in all_blocks:
                if block.chapter == "Unknown":
                    block.chapter = current_chapter
            
            # Extract images with OCR
            if self.enable_ocr:
                image_blocks = self.extract_images_with_ocr(page, page_num, current_chapter)
                all_blocks.extend(image_blocks)
            
            doc.close()
            
            # Extract tables (separate pass with pdfplumber)
            if PDFPLUMBER_AVAILABLE:
                table_blocks = self.extract_tables_pdfplumber(self.pdf_path, page_num)
                # Update chapter for table blocks
                for block in table_blocks:
                    block.chapter = current_chapter
                all_blocks.extend(table_blocks)
        
        except Exception as e:
            print(f"Error processing page {page_num}: {str(e)}")
        
        return all_blocks
    
    def process_pdf(
        self,
        start_page: int = 1,
        end_page: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[ContentBlock]:
        """
        Process entire PDF or page range
        
        Args:
            start_page: Starting page (1-indexed)
            end_page: Ending page (1-indexed, None for last page)
            progress_callback: Callback function for progress updates
            
        Returns:
            List of all content blocks
        """
        all_blocks = []
        
        try:
            # Get total pages
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            doc.close()
            
            if end_page is None:
                end_page = total_pages
            
            end_page = min(end_page, total_pages)
            
            print(f"Processing PDF: {self.pdf_path}")
            print(f"Pages {start_page} to {end_page} of {total_pages}")
            
            # Process each page
            for page_num in range(start_page, end_page + 1):
                if page_num % 50 == 0:
                    print(f"Processing page {page_num}/{end_page}...")
                
                page_blocks = self.process_page(page_num)
                all_blocks.extend(page_blocks)
                
                # Call progress callback
                if progress_callback:
                    progress_callback(page_num, end_page)
            
            print(f"Completed processing. Extracted {len(all_blocks)} content blocks")
        
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
        
        return all_blocks
    
    def get_pdf_info(self) -> Dict[str, Any]:
        """
        Get PDF metadata and information
        
        Returns:
            Dictionary with PDF information
        """
        try:
            doc = fitz.open(self.pdf_path)
            
            info = {
                "filename": os.path.basename(self.pdf_path),
                "page_count": len(doc),
                "metadata": doc.metadata,
                "file_size_mb": round(os.path.getsize(self.pdf_path) / (1024 * 1024), 2)
            }
            
            doc.close()
            return info
        
        except Exception as e:
            print(f"Error getting PDF info: {str(e)}")
            return {}


# Test function
if __name__ == "__main__":
    import sys
    
    # Test PDF path
    pdf_path = "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"
    
    if not os.path.exists(pdf_path):
        print(f"Test PDF not found: {pdf_path}")
        sys.exit(1)
    
    print("Testing Enhanced PDF Processor...")
    
    # Initialize processor
    processor = EnhancedPDFProcessor(pdf_path, enable_ocr=True)
    
    # Get PDF info
    info = processor.get_pdf_info()
    print(f"\nPDF Info: {info}")
    
    # Process first 5 pages as test
    print("\nProcessing first 5 pages...")
    blocks = processor.process_pdf(start_page=1, end_page=5)
    
    print(f"\nExtracted {len(blocks)} content blocks")
    
    # Show sample blocks
    print("\nSample content blocks:")
    for i, block in enumerate(blocks[:10]):
        print(f"\n--- Block {i+1} ---")
        print(f"Type: {block.content_type}")
        print(f"Page: {block.page}")
        print(f"Chapter: {block.chapter}")
        print(f"Importance: {block.importance}")
        print(f"Text: {block.text[:100]}...")

