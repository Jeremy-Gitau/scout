from typing import Dict, Optional
from .extractor import Extractor
from .llm_extractor import LLMExtractor

class SmartExtractor:
    def __init__(self, min_length: int = 2, max_length: int = 10, prefer_llm: bool = False, use_textblob: bool = False):
        
        self.min_length = min_length
        self.max_length = max_length
        
        # Use LLMExtractor with optional TextBlob enhancement
        self.extractor = LLMExtractor(min_length, max_length, use_llm=False, use_textblob=use_textblob)
        self.mode = "textblob" if use_textblob else "pattern"
    
    def extract_from_text(self, text: str, source_file: str = "") -> Dict[str, dict]:
        
        return self.extractor.extract_from_text(text, source_file)
    
    @property
    def abbreviations(self) -> Dict[str, dict]:
        
        if hasattr(self.extractor, 'get_results'):
            return self.extractor.get_results()
        return self.extractor.abbreviations
    
    def get_results(self) -> Dict[str, dict]:
        
        if hasattr(self.extractor, 'get_results'):
            return self.extractor.get_results()
        return self.extractor.abbreviations
    
    def get_statistics(self) -> Dict:
        
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
        
        return self.mode == "llm"
    
    def clear(self):
        
        if hasattr(self.extractor, 'clear'):
            self.extractor.clear()
        else:
            self.extractor.abbreviations = {}
