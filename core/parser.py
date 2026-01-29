"""
Parser module for reading document content.
Handles multiple document formats with cross-platform compatibility.
"""

from pathlib import Path
from typing import Optional
import re


class Parser:
    """Parses various document formats and extracts text content."""
    
    def __init__(self):
        self.current_file: Optional[Path] = None
        self.content: str = ""
    
    def parse_file(self, file_path: Path) -> str:
        """
        Parse a document file and extract its text content.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        self.current_file = file_path
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.txt':
                return self._parse_txt(file_path)
            elif extension in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif extension == '.pdf':
                return self._parse_pdf(file_path)
            else:
                return ""
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return ""
    
    def _parse_txt(self, file_path: Path) -> str:
        """
        Parse plain text files with multiple encoding support.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File contents as string
        """
        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading {file_path} with {encoding}: {e}")
                continue
        
        return ""
    
    def _parse_docx(self, file_path: Path) -> str:
        """
        Parse DOCX files using python-docx.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            from docx import Document
            
            doc = Document(str(file_path))
            full_text = []
            
            # Extract paragraphs
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            
            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text.append(cell.text)
            
            return '\n'.join(full_text)
        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            return ""
        except Exception as e:
            print(f"Error parsing DOCX {file_path}: {e}")
            return ""
    
    def _parse_pdf(self, file_path: Path) -> str:
        """
        Parse PDF files using PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(str(file_path))
            full_text = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            return '\n'.join(full_text)
        except ImportError:
            print("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return ""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        
        return text.strip()
    
    @staticmethod
    def split_into_sentences(text: str) -> list:
        """
        Split text into sentences for better context analysis.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
