"""
Smart extractor that provides a unified interface for pattern-based extraction.
Provides fast, reliable abbreviation detection optimized for many files.
"""

from typing import Dict, Optional
from .extractor import Extractor
from .llm_extractor import LLMExtractor


class SmartExtractor:
    """
    Fast pattern-based extractor optimized for processing many files.
    Uses enhanced pattern matching for reliable abbreviation detection.
    """
    
    def __init__(self, min_length: int = 2, max_length: int = 10, prefer_llm: bool = False):
        """
        Initialize the smart extractor.
        
        Args:
            min_length: Minimum abbreviation length
            max_length: Maximum abbreviation length
            prefer_llm: Ignored (kept for compatibility)
        """
        self.min_length = min_length
        self.max_length = max_length
        
        # Always use fast LLMExtractor (pattern-only, no model loading)
        self.extractor = LLMExtractor(min_length, max_length, use_llm=False)
        self.mode = "pattern"
    
    def extract_from_text(self, text: str, source_file: str = "") -> Dict[str, dict]:
        """Extract abbreviations from text."""
        return self.extractor.extract_from_text(text, source_file)
    
    @property
    def abbreviations(self) -> Dict[str, dict]:
        """Get abbreviations dictionary (for compatibility)."""
        if hasattr(self.extractor, 'get_results'):
            return self.extractor.get_results()
        return self.extractor.abbreviations
    
    def get_results(self) -> Dict[str, dict]:
        """Get extraction results."""
        if hasattr(self.extractor, 'get_results'):
            return self.extractor.get_results()
        return self.extractor.abbreviations
    
    def get_statistics(self) -> Dict:
        """Get statistics about extracted abbreviations."""
        if hasattr(self.extractor, 'get_statistics'):
            return self.extractor.get_statistics()
        
        # Calculate statistics manually
        abbrevs = self.abbreviations
        with_def = sum(1 for info in abbrevs.values() if info.get('definition'))
        without_def = len(abbrevs) - with_def
        coverage = (with_def / len(abbrevs) * 100) if abbrevs else 0
        
        return {
            'total_abbreviations': len(abbrevs),
            'with_definitions': with_def,
            'without_definitions': without_def,
            'coverage_percent': round(coverage, 1)
        }
    
    def is_using_llm(self) -> bool:
        """Check if using LLM-based extraction."""
        return self.mode == "llm"
    
    def clear(self):
        """Clear all extracted abbreviations."""
        if hasattr(self.extractor, 'clear'):
            self.extractor.clear()
        else:
            self.extractor.abbreviations = {}
