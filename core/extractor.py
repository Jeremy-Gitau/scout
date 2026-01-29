"""
Extractor module for identifying abbreviations and their definitions.
Uses pattern matching to find acronyms and their expansions.
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

try:
    import nltk
    from nltk.corpus import stopwords
    try:
        STOP_WORDS = set(word.upper() for word in stopwords.words('english'))
        HAS_NLTK = True
    except LookupError:
        # Try to download with SSL fix
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            nltk.download('stopwords', quiet=True)
            STOP_WORDS = set(word.upper() for word in stopwords.words('english'))
            HAS_NLTK = True
        except:
            # Fallback to basic stopwords if download fails
            HAS_NLTK = False
            STOP_WORDS = {
                'THE', 'BE', 'TO', 'OF', 'AND', 'A', 'IN', 'THAT', 'HAVE', 'I',
                'IT', 'FOR', 'NOT', 'ON', 'WITH', 'HE', 'AS', 'YOU', 'DO', 'AT',
                'THIS', 'BUT', 'HIS', 'BY', 'FROM', 'THEY', 'WE', 'SAY', 'HER', 'SHE',
                'OR', 'AN', 'WILL', 'MY', 'ONE', 'ALL', 'WOULD', 'THERE', 'THEIR', 'WHAT',
                'SO', 'UP', 'OUT', 'IF', 'ABOUT', 'WHO', 'GET', 'WHICH', 'GO', 'ME',
                'WHEN', 'MAKE', 'CAN', 'LIKE', 'TIME', 'NO', 'JUST', 'HIM', 'KNOW', 'TAKE',
                'PEOPLE', 'INTO', 'YEAR', 'YOUR', 'GOOD', 'SOME', 'COULD', 'THEM', 'SEE', 'OTHER',
                'THAN', 'THEN', 'NOW', 'LOOK', 'ONLY', 'COME', 'ITS', 'OVER', 'THINK', 'ALSO',
                'BACK', 'AFTER', 'USE', 'TWO', 'HOW', 'OUR', 'WORK', 'FIRST', 'WELL', 'WAY',
                'EVEN', 'NEW', 'WANT', 'BECAUSE', 'ANY', 'THESE', 'GIVE', 'DAY', 'MOST', 'US',
            }
            print("⚠ NLTK stopwords unavailable, using basic fallback list")
except ImportError:
    HAS_NLTK = False
    # Basic fallback stopwords
    STOP_WORDS = {
        'THE', 'BE', 'TO', 'OF', 'AND', 'A', 'IN', 'THAT', 'HAVE', 'I',
        'IT', 'FOR', 'NOT', 'ON', 'WITH', 'HE', 'AS', 'YOU', 'DO', 'AT',
        'THIS', 'BUT', 'HIS', 'BY', 'FROM', 'THEY', 'WE', 'SAY', 'HER', 'SHE',
        'OR', 'AN', 'WILL', 'MY', 'ONE', 'ALL', 'WOULD', 'THERE', 'THEIR', 'WHAT',
        'SO', 'UP', 'OUT', 'IF', 'ABOUT', 'WHO', 'GET', 'WHICH', 'GO', 'ME',
        'WHEN', 'MAKE', 'CAN', 'LIKE', 'TIME', 'NO', 'JUST', 'HIM', 'KNOW', 'TAKE',
        'PEOPLE', 'INTO', 'YEAR', 'YOUR', 'GOOD', 'SOME', 'COULD', 'THEM', 'SEE', 'OTHER',
        'THAN', 'THEN', 'NOW', 'LOOK', 'ONLY', 'COME', 'ITS', 'OVER', 'THINK', 'ALSO',
        'BACK', 'AFTER', 'USE', 'TWO', 'HOW', 'OUR', 'WORK', 'FIRST', 'WELL', 'WAY',
        'EVEN', 'NEW', 'WANT', 'BECAUSE', 'ANY', 'THESE', 'GIVE', 'DAY', 'MOST', 'US',
    }


class Extractor:
    """Extracts abbreviations and definitions from text."""
    
    # Pattern for detecting abbreviations (2-10 uppercase letters, may include numbers)
    ABBREV_PATTERN = re.compile(r'\b[A-Z][A-Z0-9]{1,9}\b')
    
    # Domain-specific words to exclude beyond NLTK stopwords
    ADDITIONAL_EXCLUDES = {
        # Numbers
        'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN',
        'EIGHTEEN', 'NINETEEN', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY',
        'EIGHTY', 'NINETY', 'HUNDRED', 'THOUSAND', 'MILLION', 'BILLION',
        
        # Ordinals
        'ELEVENTH', 'TWELFTH', 'THIRTEENTH', 'FOURTEENTH', 'FIFTEENTH', 'SIXTEENTH',
        'SEVENTEENTH', 'EIGHTEENTH', 'NINETEENTH', 'TWENTIETH',
        
        # Legal/government terms
        'PARLIAMENT', 'SENATE', 'ASSEMBLY', 'COUNCIL', 'COURT', 'JUDGE', 'JUSTICE',
        'PRESIDENT', 'MINISTER', 'SECRETARY', 'OFFICER', 'COMMISSION', 'COMMITTEE',
        'BOARD', 'AUTHORITY', 'DEPARTMENT', 'AGENCY', 'SERVICE', 'REPUBLIC',
        'CONSTITUTION', 'COUNTY', 'NATIONAL', 'PUBLIC', 'EXECUTIVE', 'LEGISLATIVE',
        'JUDICIAL', 'FEDERAL', 'LOCAL', 'ELECTORAL', 'DEVOLVED', 'PRINCIPLES',
        'RIGHTS', 'LAWS', 'OFFICES', 'OATH', 'REVENUE', 'FINANCE', 'BUDGET',
        
        # Places
        'KENYA', 'AMERICA', 'AMERICAN', 'EUROPE', 'EUROPEAN', 'ASIA', 'ASIAN',
        'AFRICA', 'AFRICAN', 'AUSTRALIA', 'CHINA', 'CHINESE', 'INDIA', 'INDIAN',
        'JAPAN', 'JAPANESE', 'KOREA', 'KOREAN', 'RUSSIA', 'RUSSIAN', 'FRANCE',
        'FRENCH', 'GERMANY', 'GERMAN', 'ITALY', 'ITALIAN', 'SPAIN', 'SPANISH',
        'CANADA', 'CANADIAN', 'MEXICO', 'MEXICAN', 'BRAZIL', 'ENGLAND', 'ENGLISH',
        'BRITISH', 'LONDON', 'PARIS', 'TOKYO', 'NAIROBI',
        
        # Days/months
        'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
        'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER',
        'OCTOBER', 'NOVEMBER', 'DECEMBER',
        
        # Common nouns
        'LAND', 'DEBT', 'ROLE', 'SEAL', 'FLAG', 'ARMS', 'COAT', 'GOD',
    }
    
    @classmethod
    def get_excluded_words(cls):
        return STOP_WORDS | cls.ADDITIONAL_EXCLUDES
    
    def __init__(self, min_length: int = 2, max_length: int = 10):
        self.min_length = min_length
        self.max_length = max_length
        self.abbreviations: Dict[str, dict] = {}
    
    def _is_likely_abbreviation(self, word: str, text: str) -> bool:
        """Check if word is likely an abbreviation."""
        excluded = self.get_excluded_words()
        if word in excluded:
            return False
        
        # Has numbers = likely abbreviation
        if any(c.isdigit() for c in word):
            return True
        
        # Check for definition patterns
        patterns = [
            rf'\([^)]*{re.escape(word)}[^)]*\)',
            rf'{re.escape(word)}\s*[:\-—]',
            rf'[:\-—]\s*{re.escape(word)}',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        # Short words (2-4 chars) are likely abbreviations
        if 2 <= len(word) <= 4:
            return True
        
        # Long words in caps are probably emphasis, not abbreviations
        return False
    
    def extract_from_text(self, text: str, source_file: str = "") -> Dict[str, dict]:
        """
        Extract abbreviations and their definitions from text.
        
        Args:
            text: Text content to analyze
            source_file: Source file name for tracking
            
        Returns:
            Dictionary of abbreviations with definitions and metadata
        """
        # Find all potential abbreviations
        matches = self.ABBREV_PATTERN.findall(text)
        
        for abbrev in matches:
            # Filter by length and likelihood
            if not (self.min_length <= len(abbrev) <= self.max_length):
                continue
            
            if not self._is_likely_abbreviation(abbrev, text):
                continue
            
            # Try to find definition
            definition = self._find_definition(text, abbrev)
            
            # Only add if we found a definition or it's a short word (likely real abbreviation)
            if definition or len(abbrev) <= 4:
                # Store or update abbreviation info
                if abbrev not in self.abbreviations:
                    self.abbreviations[abbrev] = {
                        'definition': definition,
                        'files': [source_file] if source_file else [],
                        'count': 1
                    }
                else:
                    self.abbreviations[abbrev]['count'] += 1
                    if source_file and source_file not in self.abbreviations[abbrev]['files']:
                        self.abbreviations[abbrev]['files'].append(source_file)
                    
                    # Update definition if we found a better one
                    if definition and not self.abbreviations[abbrev]['definition']:
                        self.abbreviations[abbrev]['definition'] = definition
        
        return self.abbreviations
    
    def _find_definition(self, text: str, abbrev: str) -> Optional[str]:
        """
        Find the definition for an abbreviation in text.
        
        Args:
            text: Text to search
            abbrev: Abbreviation to find definition for
            
        Returns:
            Definition string or None
        """
        # Clean the text first - remove markdown headers and multiple newlines
        text = re.sub(r'\n#+\s+.*?\n', '\n', text)  # Remove markdown headers
        text = re.sub(r'\n{2,}', '\n', text)  # Collapse multiple newlines
        
        # Pattern 1: "Definition (ABBREV)" - most common pattern
        # Improved to avoid section headers by ensuring it's on the same line
        pattern1 = rf'([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{0,7}})\s*\({re.escape(abbrev)}\)'
        match = re.search(pattern1, text)
        if match:
            definition = match.group(1).strip()
            # Verify it's not just a section title (usually all caps or very short)
            if len(definition) > 3 and not definition.isupper():
                return definition
        
        # Pattern 2: "ABBREV (Definition)"
        pattern2 = rf'{re.escape(abbrev)}\s*\(([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{0,7}})\)'
        match = re.search(pattern2, text)
        if match:
            definition = match.group(1).strip()
            if len(definition) > 3 and not definition.isupper():
                return definition
        
        # Pattern 3: "ABBREV: Definition" or "ABBREV - Definition"
        # Improved to get full definition on same line
        pattern3 = rf'{re.escape(abbrev)}\s*[:\-—]\s*([A-Z][^\n\.]+?)(?:[\n\.]|$)'
        match = re.search(pattern3, text)
        if match:
            definition = match.group(1).strip()
            # Limit to reasonable length
            words = definition.split()[:10]
            result = ' '.join(words).strip()
            if len(result) > 3:
                return result
        
        # Pattern 4: "ABBREV stands for" or "ABBREV means"
        pattern4 = rf'{re.escape(abbrev)}\s+(?:stands for|means)\s+([A-Z][^\n\.]+?)(?:[\n\.]|$)'
        match = re.search(pattern4, text, re.IGNORECASE)
        if match:
            definition = match.group(1).strip()
            words = definition.split()[:10]
            return ' '.join(words).strip()
        
        # Pattern 5: First letter matching (e.g., "API" from "Application Programming Interface")
        # Only use this as last resort since it can be inaccurate
        definition = self._find_first_letter_match(text, abbrev)
        if definition:
            return definition
        
        return None
    
    def _find_first_letter_match(self, text: str, abbrev: str) -> Optional[str]:
        """
        Find definition by matching first letters of consecutive words.
        
        Args:
            text: Text to search
            abbrev: Abbreviation
            
        Returns:
            Matched definition or None
        """
        # Split text into sentences to avoid matching across sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Look for sequences of capitalized words
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', sentence)
            
            for word_sequence in words:
                word_list = word_sequence.split()
                
                # Try all possible sub-sequences matching abbreviation length
                for i in range(len(word_list) - len(abbrev) + 1):
                    sequence = word_list[i:i + len(abbrev)]
                    
                    # Check if first letters match
                    if len(sequence) == len(abbrev):
                        first_letters = ''.join(word[0] for word in sequence)
                        
                        if first_letters == abbrev:
                            result = ' '.join(sequence)
                            # Verify it's a reasonable definition (not too generic)
                            if len(result) > len(abbrev) + 2:
                                return result
        
        return None
    
    def get_sorted_abbreviations(self, sort_by: str = 'alpha') -> List[Tuple[str, dict]]:
        """
        Get abbreviations sorted by specified criteria.
        
        Args:
            sort_by: Sort criteria ('alpha', 'count', 'files')
            
        Returns:
            List of (abbreviation, info) tuples
        """
        if sort_by == 'alpha':
            return sorted(self.abbreviations.items())
        elif sort_by == 'count':
            return sorted(self.abbreviations.items(), 
                         key=lambda x: x[1]['count'], 
                         reverse=True)
        elif sort_by == 'files':
            return sorted(self.abbreviations.items(), 
                         key=lambda x: len(x[1]['files']), 
                         reverse=True)
        else:
            return list(self.abbreviations.items())
    
    def filter_abbreviations(self, query: str) -> Dict[str, dict]:
        """
        Filter abbreviations by search query.
        
        Args:
            query: Search query
            
        Returns:
            Filtered abbreviations dictionary
        """
        query = query.lower()
        filtered = {}
        
        for abbrev, info in self.abbreviations.items():
            # Search in abbreviation or definition
            if (query in abbrev.lower() or 
                (info['definition'] and query in info['definition'].lower())):
                filtered[abbrev] = info
        
        return filtered
    
    def get_statistics(self) -> dict:
        """
        Get statistics about extracted abbreviations.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.abbreviations)
        with_definitions = sum(1 for info in self.abbreviations.values() 
                              if info['definition'])
        without_definitions = total - with_definitions
        
        return {
            'total_abbreviations': total,
            'with_definitions': with_definitions,
            'without_definitions': without_definitions,
            'coverage_percent': round((with_definitions / total * 100) if total > 0 else 0, 1)
        }
    
    def clear(self):
        """Clear all stored abbreviations."""
        self.abbreviations.clear()
