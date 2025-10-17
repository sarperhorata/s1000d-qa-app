"""
OCR Processor module for S1000D QA application
Handles text extraction from images using Tesseract or EasyOCR
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io
import numpy as np

from config import config

# OCR engines
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Tesseract not available. Install with: pip install pytesseract")

try:
    import easyocr
    EASYOCR_AVAILABLE = False  # Set to False by default for faster startup
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available. Install with: pip install easyocr")


class OCRProcessor:
    """OCR processor for extracting text from images"""
    
    def __init__(self, engine: str = None, languages: List[str] = None):
        """
        Initialize OCR processor
        
        Args:
            engine: OCR engine to use ('tesseract' or 'easyocr')
            languages: List of language codes for OCR
        """
        self.engine = engine or config.OCR_ENGINE
        self.languages = languages or config.OCR_LANGUAGES
        self.reader = None
        
        if self.engine == "easyocr" and EASYOCR_AVAILABLE:
            print(f"Initializing EasyOCR with languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=False)
            print("EasyOCR initialized")
        elif self.engine == "tesseract" and TESSERACT_AVAILABLE:
            print(f"Using Tesseract OCR with languages: {self.languages}")
        else:
            print(f"OCR engine '{self.engine}' not available, OCR will be disabled")
            self.engine = None
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.engine is not None
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize if too small (minimum 300px width)
        width, height = image.size
        if width < 300:
            scale_factor = 300 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to numpy array for further processing
        img_array = np.array(image)
        
        # Simple thresholding to improve contrast
        threshold = 128
        img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)
    
    def extract_text_tesseract(self, image: Image.Image) -> str:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: PIL Image
            
        Returns:
            Extracted text
        """
        if not TESSERACT_AVAILABLE:
            return ""
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Extract text
            lang_str = '+'.join(self.languages)
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_str,
                config='--psm 6'  # Assume uniform text block
            )
            
            return text.strip()
        
        except Exception as e:
            print(f"Tesseract OCR error: {str(e)}")
            return ""
    
    def extract_text_easyocr(self, image: Image.Image) -> str:
        """
        Extract text using EasyOCR
        
        Args:
            image: PIL Image
            
        Returns:
            Extracted text
        """
        if not EASYOCR_AVAILABLE or self.reader is None:
            return ""
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Convert to numpy array
            img_array = np.array(processed_image)
            
            # Extract text
            results = self.reader.readtext(img_array)
            
            # Combine all detected text
            text_parts = [result[1] for result in results]
            text = ' '.join(text_parts)
            
            return text.strip()
        
        except Exception as e:
            print(f"EasyOCR error: {str(e)}")
            return ""
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from image using configured OCR engine
        
        Args:
            image: PIL Image
            
        Returns:
            Extracted text
        """
        if not self.is_available():
            return ""
        
        if self.engine == "tesseract":
            return self.extract_text_tesseract(image)
        elif self.engine == "easyocr":
            return self.extract_text_easyocr(image)
        
        return ""
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Extracted text
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return self.extract_text(image)
        except Exception as e:
            print(f"Error loading image from bytes: {str(e)}")
            return ""
    
    def is_text_heavy_image(self, image: Image.Image, threshold: float = 0.3) -> bool:
        """
        Heuristic to determine if an image contains significant text
        
        Args:
            image: PIL Image
            threshold: Minimum ratio of non-white pixels to consider text-heavy
            
        Returns:
            True if image likely contains text
        """
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            img_array = np.array(gray_image)
            
            # Calculate ratio of non-white pixels
            non_white_pixels = np.sum(img_array < 240)
            total_pixels = img_array.size
            ratio = non_white_pixels / total_pixels
            
            # If significant portion is non-white, likely contains text/diagram
            return ratio > threshold
        
        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return False
    
    def should_apply_ocr(self, image: Image.Image, image_size_bytes: int) -> bool:
        """
        Determine if OCR should be applied to an image
        
        Args:
            image: PIL Image
            image_size_bytes: Size of image in bytes
            
        Returns:
            True if OCR should be applied
        """
        # Skip very small images (likely icons)
        if image.size[0] < 100 or image.size[1] < 100:
            return False
        
        # Skip very large images (likely photos, not diagrams)
        if image_size_bytes > 5 * 1024 * 1024:  # 5MB
            return False
        
        # Check if image is text-heavy
        return self.is_text_heavy_image(image)
    
    def extract_with_metadata(
        self,
        image: Image.Image,
        page_number: int,
        image_index: int
    ) -> Dict[str, Any]:
        """
        Extract text with metadata
        
        Args:
            image: PIL Image
            page_number: Page number in PDF
            image_index: Index of image on page
            
        Returns:
            Dictionary with text and metadata
        """
        text = self.extract_text(image)
        
        return {
            'text': text,
            'page': page_number,
            'image_index': image_index,
            'has_text': len(text.strip()) > 0,
            'word_count': len(text.split()) if text else 0,
            'image_size': image.size,
            'ocr_engine': self.engine
        }


# Test function
if __name__ == "__main__":
    print("Testing OCR Processor...")
    
    # Test with Tesseract
    processor = OCRProcessor(engine="tesseract")
    
    if processor.is_available():
        print(f"OCR engine '{processor.engine}' is available")
        
        # Create a test image with text
        from PIL import ImageDraw, ImageFont
        
        # Create blank image
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw text
        text = "S1000D Technical Documentation"
        draw.text((10, 30), text, fill='black')
        
        # Test OCR
        extracted_text = processor.extract_text(img)
        print(f"Extracted text: '{extracted_text}'")
        
        # Test heuristics
        is_text_heavy = processor.is_text_heavy_image(img)
        print(f"Is text-heavy: {is_text_heavy}")
        
    else:
        print("OCR not available - tests skipped")

