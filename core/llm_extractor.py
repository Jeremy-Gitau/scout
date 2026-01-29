"""Fast pattern-based abbreviation extractor.
Uses regex patterns to find explicit abbreviation definitions.
Optimized for speed when processing many files.
"""

import re
import os
from typing import Dict, List, Optional, Tuple
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


class LLMExtractor:
    """
    Fast pattern-based abbreviation extractor.
    Uses regex patterns to find explicit abbreviation definitions.
    """
    
    ABBREV_PATTERN = re.compile(r'\b[A-Z][A-Z0-9]{1,9}\b')
    
    # Domain-specific words to exclude beyond NLTK/fallback stopwords
    ADDITIONAL_EXCLUDES = {
        # Stop words
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE',
        'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD',
        'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO',
        'USE', 'VERY', 'WORK', 'YEAR', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT',
        'NINE', 'TEN', 'FIRST', 'SECOND', 'THIRD', 'LAST', 'NEXT', 'THEN', 'WHEN', 'WHERE',
        'WILL', 'WOULD', 'COULD', 'SHOULD', 'MUST', 'MIGHT', 'SHALL', 'MAY', 'HAVE', 'HAD',
        'FROM', 'WITH', 'WHAT', 'THAT', 'THIS', 'THERE', 'THEIR', 'WHICH', 'ABOUT', 'INTO',
        'THAN', 'THEM', 'THESE', 'THOSE', 'SOME', 'SUCH', 'ONLY', 'MORE', 'MOST', 'MANY',
        'MUCH', 'BOTH', 'EACH', 'EVERY', 'SAME', 'SUCH', 'OVER', 'UNDER', 'AGAIN', 'ONCE',
        'HERE', 'ALSO', 'BACK', 'BETWEEN', 'BEFORE', 'AFTER', 'DURING', 'WITHOUT', 'WITHIN',
        'THROUGH', 'BECAUSE', 'ANOTHER', 'SOMETHING', 'NOTHING', 'EVERYTHING', 'ANYTHING',
        'SOMEONE', 'EVERYONE', 'ANYONE', 'NOBODY', 'ALWAYS', 'NEVER', 'SOMETIMES', 'OFTEN',
        'USUALLY', 'ALREADY', 'STILL', 'YET', 'ELSE', 'THOUGH', 'ALTHOUGH', 'UNLESS', 'UNTIL',
        'WHILE', 'SINCE', 'EITHER', 'NEITHER', 'WHETHER', 'HOWEVER', 'THEREFORE', 'THUS',
        'HENCE', 'MOREOVER', 'FURTHERMORE', 'MEANWHILE', 'OTHERWISE', 'INDEED', 'RATHER',
        
        # Common nouns that might appear in caps
        'PEOPLE', 'PERSON', 'MAN', 'WOMAN', 'CHILD', 'BOY', 'GIRL', 'FAMILY', 'FRIEND',
        'TEAM', 'GROUP', 'COMPANY', 'BUSINESS', 'GOVERNMENT', 'WORLD', 'COUNTRY', 'STATE',
        'CITY', 'TOWN', 'PLACE', 'HOME', 'HOUSE', 'ROOM', 'OFFICE', 'SCHOOL', 'COLLEGE',
        'UNIVERSITY', 'HOSPITAL', 'CHURCH', 'MARKET', 'STORE', 'SHOP', 'BANK', 'HOTEL',
        'RESTAURANT', 'PARK', 'STREET', 'ROAD', 'BUILDING', 'FLOOR', 'AREA', 'REGION',
        'WATER', 'FOOD', 'MONEY', 'TIME', 'MOMENT', 'HOUR', 'MINUTE', 'SECOND', 'WEEK',
        'MONTH', 'THING', 'PART', 'PROBLEM', 'QUESTION', 'ANSWER', 'IDEA', 'FACT', 'REASON',
        'RESULT', 'CHANGE', 'POINT', 'CASE', 'LEVEL', 'KIND', 'TYPE', 'FORM', 'SORT', 'WAY',
        'SIDE', 'HAND', 'HEAD', 'FACE', 'EYE', 'BODY', 'LIFE', 'DEATH', 'BIRTH', 'AGE',
        'NAME', 'WORD', 'LINE', 'PAGE', 'BOOK', 'STORY', 'CHAPTER', 'SECTION', 'TITLE',
        'NUMBER', 'AMOUNT', 'PRICE', 'COST', 'VALUE', 'RATE', 'PERCENT', 'TOTAL', 'AVERAGE',
        
        # Place names and common proper nouns
        'AMERICA', 'AMERICAN', 'EUROPE', 'EUROPEAN', 'ASIA', 'ASIAN', 'AFRICA', 'AFRICAN',
        'AUSTRALIA', 'CHINA', 'CHINESE', 'INDIA', 'INDIAN', 'JAPAN', 'JAPANESE', 'KOREA',
        'KOREAN', 'RUSSIA', 'RUSSIAN', 'FRANCE', 'FRENCH', 'GERMANY', 'GERMAN', 'ITALY',
        'ITALIAN', 'SPAIN', 'SPANISH', 'CANADA', 'CANADIAN', 'MEXICO', 'MEXICAN', 'BRAZIL',
        'ENGLAND', 'ENGLISH', 'BRITISH', 'IRELAND', 'IRISH', 'SCOTLAND', 'SCOTTISH', 'WALES',
        'LONDON', 'PARIS', 'TOKYO', 'BEIJING', 'DELHI', 'MOSCOW', 'BERLIN', 'MADRID', 'ROME',
        'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
        'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER',
        'OCTOBER', 'NOVEMBER', 'DECEMBER', 'SPRING', 'SUMMER', 'FALL', 'AUTUMN', 'WINTER',
        
        # Common verbs/actions in caps
        'MAKE', 'TAKE', 'GIVE', 'FIND', 'TELL', 'FEEL', 'BECOME', 'LEAVE', 'BRING', 'BEGIN',
        'KEEP', 'HOLD', 'WRITE', 'STAND', 'HEAR', 'SEEM', 'TURN', 'SHOW', 'HELP', 'TALK',
        'CONTINUE', 'HAPPEN', 'CARRY', 'MOVE', 'FOLLOW', 'STOP', 'CREATE', 'SPEAK', 'READ',
        'ALLOW', 'ADD', 'SPEND', 'GROW', 'OPEN', 'WALK', 'WIN', 'OFFER', 'REMEMBER', 'LOVE',
        'CONSIDER', 'APPEAR', 'PRODUCE', 'CONTAIN', 'REDUCE', 'REQUIRE', 'DEVELOP', 'RECEIVE',
        'RETURN', 'BUILD', 'REMAIN', 'INDICATE', 'FALL', 'REACH', 'EXPLAIN', 'RAISE', 'PASS',
        'SELL', 'DECIDE', 'DRAW', 'SENT', 'EXPECT', 'STAY', 'DESCRIBE', 'SUGGEST', 'INCLUDE',
    }
    
    @classmethod
    def get_excluded_words(cls):
        """Get all words that should be excluded from abbreviation extraction."""
        return STOP_WORDS | cls.ADDITIONAL_EXCLUDES
    
    def __init__(self, min_length: int = 2, max_length: int = 10, use_llm: bool = False):
        self.min_length = min_length
        self.max_length = max_length
        self.abbreviations: Dict[str, dict] = {}
    
    def _is_likely_abbreviation(self, word: str, text: str) -> bool:
        """
        Determine if a word is likely an abbreviation vs. a common word in caps.
        """
        # Exclude NLTK stopwords and additional common words
        excluded = self.get_excluded_words()
        if word in excluded:
            return False
        
        # Single letter followed by numbers is likely an abbreviation (e.g., H2O, CO2)
        if len(word) >= 2 and word[0].isalpha() and any(c.isdigit() for c in word):
            return True
        
        # If it appears in parentheses or after a definition pattern, it's likely an abbreviation
        patterns = [
            rf'\([^)]*{re.escape(word)}[^)]*\)',  # In parentheses
            rf'{re.escape(word)}\s*[:\-—]',  # Followed by colon or dash
            rf'[:\-—]\s*{re.escape(word)}',  # After colon or dash
            rf'\({re.escape(word)}\)',  # Exactly in parentheses
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        # If it's 2-4 characters and all uppercase, likely an abbreviation
        if 2 <= len(word) <= 4:
            return True
        
        # Longer words (5+) in all caps are more likely emphasis than abbreviations
        # unless they appear with definition patterns
        if len(word) >= 5:
            return False
        
        return True
    
    def extract_from_text(self, text: str, source_file: str = "") -> Dict[str, dict]:
        """Extract abbreviations using fast pattern matching."""
        matches = self.ABBREV_PATTERN.findall(text)
        
        # Deduplicate matches first
        unique_matches = set(matches)
        
        for abbrev in unique_matches:
            # Check length and if it's likely an abbreviation
            if not (self.min_length <= len(abbrev) <= self.max_length):
                continue
            
            # Skip if it's not likely an abbreviation
            if not self._is_likely_abbreviation(abbrev, text):
                continue
            
            # Use pattern matching to find definition
            definition = self._pattern_find_definition(text, abbrev)
            
            # Only add if we found a definition or it looks like a real abbreviation (2-4 chars)
            if definition or len(abbrev) <= 4:
                # Store abbreviation info
                if abbrev not in self.abbreviations:
                    self.abbreviations[abbrev] = {
                        'definition': definition,
                        'files': [source_file] if source_file else [],
                        'count': matches.count(abbrev)  # Count occurrences in original list
                    }
                else:
                    self.abbreviations[abbrev]['count'] += matches.count(abbrev)
                    if source_file and source_file not in self.abbreviations[abbrev]['files']:
                        self.abbreviations[abbrev]['files'].append(source_file)
                    
                    if definition and not self.abbreviations[abbrev]['definition']:
                        self.abbreviations[abbrev]['definition'] = definition
        
        return self.abbreviations
    
    def _pattern_find_definition(self, text: str, abbrev: str) -> Optional[str]:
        """
        Use pattern matching to find explicit definitions.
        Fast and reliable for common patterns like \"Full Name (FN)\".
        """
        candidates = []
        sentences = self._extract_sentences_with_abbrev(text, abbrev)        
        for sentence in sentences:
            # Pattern: "Definition (ABBREV)" or "ABBREV (Definition)"
            # "Something (ABBREV)"
            match = re.search(rf'([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{1,7}})\s*\({re.escape(abbrev)}\)', sentence)
            if match:
                candidates.append((match.group(1), 1.0))  # High confidence
            
            # "ABBREV (Something)"
            match = re.search(rf'{re.escape(abbrev)}\s*\(([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{1,7}})\)', sentence)
            if match:
                candidates.append((match.group(1), 1.0))
            
            # "ABBREV: Something" or "ABBREV - Something"
            match = re.search(rf'{re.escape(abbrev)}\s*[:\-—]\s*([A-Z][^\n\.]+?)(?:[\n\.]|$)', sentence)
            if match:
                definition = match.group(1).strip()
                words = definition.split()[:10]
                candidates.append((' '.join(words), 0.9))
            
            # "ABBREV stands for/means"
            match = re.search(rf'{re.escape(abbrev)}\s+(?:stands for|means)\s+([A-Z][^\n\.]+?)(?:[\n\.]|$)', 
                            sentence, re.IGNORECASE)
            if match:
                definition = match.group(1).strip()
                words = definition.split()[:10]
                candidates.append((' '.join(words), 0.95))
        
        # Return best candidate if available
        if candidates:
            best = max(candidates, key=lambda x: x[1])
            if best[0] and len(best[0]) > 3:
                return best[0]
        
        return None
    
    def _extract_sentences_with_abbrev(self, text: str, abbrev: str) -> List[str]:
        """Extract sentences containing the abbreviation."""
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]\s+', text)
        
        # Filter sentences containing abbreviation
        relevant = []
        for sentence in sentences:
            if abbrev in sentence:
                # Clean up
                sentence = sentence.strip()
                if len(sentence) > 10:  # Avoid too short fragments
                    relevant.append(sentence)
        
        return relevant[:5]  # Limit to first 5 occurrences
    
    def get_results(self) -> Dict[str, dict]:
        """Return extracted abbreviations."""
        return self.abbreviations
    
    def clear(self):
        """Clear all extracted abbreviations."""
        self.abbreviations = {}
    
    @property
    def abbreviations_list(self) -> List[str]:
        """Return list of abbreviation strings."""
        return list(self.abbreviations.keys())
    
    def get_statistics(self) -> dict:
        """Get extraction statistics."""
        total = len(self.abbreviations)
        with_def = sum(1 for v in self.abbreviations.values() if v.get('definition'))
        without_def = total - with_def
        
        return {
            'total': total,
            'with_definitions': with_def,
            'without_definitions': without_def
        }

