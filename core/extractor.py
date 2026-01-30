import re
import requests
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

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

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        HAS_SPACY = True
    except OSError:
        HAS_SPACY = False
        nlp = None
        print("⚠ spaCy model not found. Install with: python -m spacy download en_core_web_sm")
except ImportError:
    HAS_SPACY = False
    nlp = None
    print("⚠ spaCy not installed. Some features disabled.")

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    model = AutoModel.from_pretrained("bert-base-uncased")
    HAS_BERT = True
except ImportError:
    HAS_BERT = False
    tokenizer = None
    model = None
    print("⚠ Transformers/BERT not installed. Semantic matching disabled.")
except Exception as e:
    HAS_BERT = False
    tokenizer = None
    model = None
    print(f"⚠ BERT loading failed: {e}")

class Extractor:
    
    
    # Pattern for standard abbreviations (2-10 uppercase letters, may include numbers)
    ABBREV_PATTERN = re.compile(r'\b[A-Z][A-Z0-9]{1,9}\b')
    
    # Pattern for dotted abbreviations (e.g., U.S.A., Ph.D.)
    DOTTED_PATTERN = re.compile(r'\b[A-Z](?:\.[A-Z])+\.?\b')
    
    # Pattern for hyphenated abbreviations (e.g., UTF-8, X-Ray)
    HYPHENATED_PATTERN = re.compile(r'\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b')
    
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
    
    def __init__(self, min_length: int = 2, max_length: int = 10, use_api: bool = False):
        self.min_length = min_length
        self.max_length = max_length
        self.use_api = use_api
        self.abbreviations: Dict[str, dict] = {}
        self.api_cache: Dict[str, Optional[str]] = {}
    
    def _is_named_entity(self, word: str, text: str) -> bool:
        if not HAS_SPACY or not nlp:
            return False
        
        try:
            # Sample context around the word
            pattern = rf'.{{0,100}}\b{re.escape(word)}\b.{{0,100}}'
            match = re.search(pattern, text)
            if not match:
                return False
            
            doc = nlp(match.group(0))
            for ent in doc.ents:
                if word in ent.text:
                    # Filter out ORG, PRODUCT, GPE (likely legitimate abbreviations)
                    if ent.label_ in ['PERSON', 'NORP', 'FAC', 'LOC', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
                        return True
            return False
        except:
            return False
    
    def _validate_with_api(self, abbrev: str) -> Optional[str]:
        if not self.use_api:
            return None
        
        if abbrev in self.api_cache:
            return self.api_cache[abbrev]
        
        try:
            # Acronym Finder API (free tier)
            url = f"http://www.acronymfinder.com/api?term={abbrev}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                # Parse the API response (simplified - adjust based on actual API)
                data = response.json() if response.headers.get('content-type') == 'application/json' else None
                if data and isinstance(data, list) and len(data) > 0:
                    definition = data[0].get('definition', None)
                    self.api_cache[abbrev] = definition
                    return definition
        except:
            pass
        
        self.api_cache[abbrev] = None
        return None
    
    def _calculate_confidence_score(self, abbrev: str, definition: Optional[str], 
                                     text: str, position: int) -> float:
        score = 0.5  # Base score
        
        # Higher score if definition found
        if definition:
            score += 0.3
            
            # Check for explicit definition patterns
            if re.search(rf'\bstands for\b.*{re.escape(definition)}', text, re.IGNORECASE):
                score += 0.15
            if re.search(rf'\bmeans\b.*{re.escape(definition)}', text, re.IGNORECASE):
                score += 0.15
            
            # Use BERT semantic similarity if available
            if HAS_BERT and tokenizer and model:
                similarity = self._calculate_semantic_similarity(abbrev, definition)
                if similarity > 0.7:
                    score += 0.2
                elif similarity > 0.5:
                    score += 0.1
        
        # Higher score for first occurrence (likely introduced properly)
        if position < len(text) * 0.2:  # First 20% of document
            score += 0.1
        
        # Higher score if contains digits (technical abbreviations)
        if any(c.isdigit() for c in abbrev):
            score += 0.1
        
        # Higher score for short abbreviations (2-4 chars)
        if 2 <= len(abbrev) <= 4:
            score += 0.05
        
        # Lower score if too long (likely not abbreviation)
        if len(abbrev) > 7:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _calculate_semantic_similarity(self, abbrev: str, definition: str) -> float:
        if not HAS_BERT or not tokenizer or not model:
            return 0.0
        
        try:
            # Get embeddings for abbreviation and definition
            abbrev_embedding = self._get_bert_embedding(abbrev)
            definition_embedding = self._get_bert_embedding(definition)
            
            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                abbrev_embedding, definition_embedding, dim=0
            ).item()
            
            return max(0.0, similarity)
        except:
            return 0.0
    
    def _get_bert_embedding(self, text: str):
        if not HAS_BERT or not tokenizer or not model:
            return None
        
        # Tokenize and get embeddings
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Use mean pooling of last hidden state
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        return embeddings
    
    def _is_in_glossary_section(self, text: str, abbrev: str) -> bool:
        # Check if abbreviation appears in a glossary/abbreviations section
        glossary_patterns = [
            r'(?:glossary|abbreviations|acronyms|definitions)\s*\n',
            r'(?:list of )?(?:abbreviations|acronyms)',
            r'appendix.*(?:abbreviations|acronyms)',
        ]
        
        for pattern in glossary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Check if abbreviation appears within 500 chars after glossary header
                glossary_start = match.end()
                glossary_text = text[glossary_start:glossary_start + 500]
                if abbrev in glossary_text:
                    return True
        
        return False
    
    def _is_likely_abbreviation(self, word: str, text: str) -> bool:
        excluded = self.get_excluded_words()
        if word in excluded:
            return False
        
        # Check if it's a named entity (filter out)
        if self._is_named_entity(word, text):
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
        
        # Check if in glossary section
        if self._is_in_glossary_section(text, word):
            return True
        
        # Short words (2-4 chars) are likely abbreviations
        if 2 <= len(word) <= 4:
            return True
        
        # Long words in caps are probably emphasis, not abbreviations
        return False
    
    def extract_from_text(self, text: str, source_file: str = "") -> Dict[str, dict]:
        
        # Find all potential abbreviations using multiple patterns
        matches = []
        
        # Standard abbreviations
        matches.extend([(m.group(), m.start()) for m in self.ABBREV_PATTERN.finditer(text)])
        
        # Dotted abbreviations (e.g., U.S.A., Ph.D.)
        dotted_matches = self.DOTTED_PATTERN.findall(text)
        for match in dotted_matches:
            # Normalize by removing dots
            normalized = match.replace('.', '')
            if self.min_length <= len(normalized) <= self.max_length:
                pos = text.find(match)
                matches.append((normalized, pos))
        
        # Hyphenated abbreviations (e.g., UTF-8, X-Ray)
        hyphenated_matches = self.HYPHENATED_PATTERN.findall(text)
        for match in hyphenated_matches:
            if self.min_length <= len(match.replace('-', '')) <= self.max_length:
                pos = text.find(match)
                matches.append((match, pos))
        
        # Count frequencies for filtering
        abbrev_counts = Counter([m[0] for m in matches])
        
        for abbrev, position in matches:
            # Filter by length
            clean_abbrev = abbrev.replace('-', '').replace('.', '')
            if not (self.min_length <= len(clean_abbrev) <= self.max_length):
                continue
            
            # Frequency-based filtering (too common or too rare)
            freq = abbrev_counts[abbrev]
            if freq > 50:  # Too common, likely not abbreviation
                continue
            if freq == 1 and len(abbrev) > 5:  # Too rare and long
                continue
            
            if not self._is_likely_abbreviation(abbrev, text):
                continue
            
            # Try to find definition
            definition = self._find_definition(text, abbrev)
            
            # Try API validation if enabled and no definition found
            if not definition and self.use_api:
                api_def = self._validate_with_api(abbrev)
                if api_def:
                    definition = api_def
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(abbrev, definition, text, position)
            
            # Only add if confidence is high enough
            if confidence >= 0.4:
                # Store or update abbreviation info
                if abbrev not in self.abbreviations:
                    self.abbreviations[abbrev] = {
                        'definition': definition,
                        'files': [source_file] if source_file else [],
                        'count': freq,
                        'confidence': confidence,
                        'first_position': position
                    }
                else:
                    self.abbreviations[abbrev]['count'] += freq
                    if source_file and source_file not in self.abbreviations[abbrev]['files']:
                        self.abbreviations[abbrev]['files'].append(source_file)
                    
                    # Update definition if we found a better one
                    if definition and not self.abbreviations[abbrev]['definition']:
                        self.abbreviations[abbrev]['definition'] = definition
                    
                    # Update confidence if higher
                    if confidence > self.abbreviations[abbrev].get('confidence', 0):
                        self.abbreviations[abbrev]['confidence'] = confidence
        
        return self.abbreviations
    
    def _find_definition(self, text: str, abbrev: str) -> Optional[str]:
        
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
        
        query = query.lower()
        filtered = {}
        
        for abbrev, info in self.abbreviations.items():
            # Search in abbreviation or definition
            if (query in abbrev.lower() or 
                (info['definition'] and query in info['definition'].lower())):
                filtered[abbrev] = info
        
        return filtered
    
    def get_statistics(self) -> dict:
        
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
        
        self.abbreviations.clear()
