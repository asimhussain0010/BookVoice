"""
Text Extractor Service
Extracts text from various eBook formats (PDF, EPUB, DOCX, TXT)
"""

import os
import re
import chardet
from typing import Tuple, Optional
from pathlib import Path
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import docx
from app.config import settings


class TextExtractor:
    """Handles text extraction from various file formats"""
    
    def __init__(self):
        self.max_chars = settings.TTS_MAX_CHARS
    
    def extract(self, file_path: str, file_type: str) -> Tuple[str, int, int]:
        """
        Extract text from file based on type
        
        Args:
            file_path: Path to the file
            file_type: File extension (pdf, epub, txt, docx)
            
        Returns:
            Tuple of (extracted_text, word_count, character_count)
            
        Raises:
            ValueError: If file type is not supported
            Exception: If extraction fails
        """
        file_type = file_type.lower().replace('.', '')
        
        extractors = {
            'pdf': self._extract_from_pdf,
            'epub': self._extract_from_epub,
            'txt': self._extract_from_txt,
            'docx': self._extract_from_docx,
        }
        
        if file_type not in extractors:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        text = extractors[file_type](file_path)
        
        # Clean and validate text
        text = self._clean_text(text)
        
        if len(text) > self.max_chars:
            raise ValueError(
                f"Text exceeds maximum length of {self.max_chars} characters. "
                f"Current length: {len(text)}"
            )
        
        word_count = len(text.split())
        char_count = len(text)
        
        return text, word_count, char_count
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
                        
        except Exception as e:
            raise Exception(f"Failed to extract PDF: {str(e)}")
        
        return '\n\n'.join(text)
    
    def _extract_from_epub(self, file_path: str) -> str:
        """Extract text from EPUB file"""
        text = []
        
        try:
            book = epub.read_epub(file_path)
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    page_text = soup.get_text()
                    if page_text:
                        text.append(page_text)
                        
        except Exception as e:
            raise Exception(f"Failed to extract EPUB: {str(e)}")
        
        return '\n\n'.join(text)
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            # Detect encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
            
            # Read file with detected encoding
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                text = file.read()
                
            return text
            
        except Exception as e:
            raise Exception(f"Failed to extract TXT: {str(e)}")
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text = []
        
        try:
            doc = docx.Document(file_path)
            
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text.append(paragraph.text)
                    
        except Exception as e:
            raise Exception(f"Failed to extract DOCX: {str(e)}")
        
        return '\n\n'.join(text)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        Remove excessive whitespace, special characters, etc.
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def preview_text(self, text: str, max_length: int = 500) -> str:
        """
        Generate a preview of the text
        
        Args:
            text: Full text content
            max_length: Maximum preview length
            
        Returns:
            Preview text
        """
        if len(text) <= max_length:
            return text
        
        preview = text[:max_length]
        
        # Try to end at a sentence boundary
        last_period = preview.rfind('.')
        if last_period > max_length * 0.7:  # At least 70% of preview
            preview = preview[:last_period + 1]
        
        return preview + "..."