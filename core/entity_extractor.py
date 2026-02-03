"""
Entity Extractor - Extract people, roles, organizations, and countries from documents
Uses hybrid approach: Pattern matching + LLM-based extraction with confidence scoring
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        HAS_SPACY = True
    except OSError:
        HAS_SPACY = False
        nlp = None
except ImportError:
    HAS_SPACY = False
    nlp = None


class EntityType(Enum):
    """Types of entities we extract"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    ROLE = "role"


class ConfidenceLevel(Enum):
    """Confidence levels for extracted entities"""
    HIGH = "high"      # 80-100%: Complete info with strong context
    MEDIUM = "medium"  # 50-79%: Partial info or weak context
    LOW = "low"        # 0-49%: Incomplete or uncertain


@dataclass
class Entity:
    """Represents an extracted entity"""
    name: str
    entity_type: EntityType
    confidence: ConfidenceLevel
    context: Optional[str] = None  # Surrounding text
    metadata: Optional[Dict[str, Any]] = None  # Additional info
    
    def to_dict(self):
        """Convert to dictionary for export"""
        return {
            'name': self.name,
            'type': self.entity_type.value,
            'confidence': self.confidence.value,
            'context': self.context,
            'metadata': self.metadata or {}
        }


@dataclass
class PersonEntity:
    """Represents a person with role and organization"""
    name: str
    role: Optional[str] = None
    organization: Optional[str] = None
    country: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    context: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for export"""
        return {
            'name': self.name,
            'role': self.role,
            'organization': self.organization,
            'country': self.country,
            'confidence': self.confidence.value,
            'context': self.context,
            'is_complete': self._is_complete()
        }
    
    def _is_complete(self) -> bool:
        """Check if all fields are populated"""
        return all([self.name, self.role, self.organization, self.country])
    
    def completeness_score(self) -> float:
        """Calculate completeness as percentage"""
        fields = [self.name, self.role, self.organization, self.country]
        populated = sum(1 for f in fields if f is not None)
        return (populated / len(fields)) * 100


class EntityExtractor:
    """Extract structured entities from documents"""
    
    # Words that are definitely not person names
    NON_PERSON_WORDS = {
        'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'from', 'by', 'about', 'as', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'advocacy', 'education', 'capacity', 'coordination', 'equity', 'governance',
        'integration', 'collaboration', 'sustainability', 'building', 'strengthening'
    }
    
    # Words that are definitely not organization names
    NON_ORG_WORDS = {
        'equity', 'sustainability', 'advocacy', 'education', 'coordination',
        'governance', 'integration', 'collaboration', 'capacity', 'building',
        'strengthen', 'ensure', 'promote', 'increase', 'improve', 'prioritize',
        'expand', 'secure', 'provide', 'support', 'develop', 'implement', 'key',
        'national', 'regional', 'local', 'main', 'primary', 'secondary',
        'equityvision', 'kes'  # Common false positives
    }
    
    # Acronyms that look like orgs but aren't
    ACRONYM_BLACKLIST = {
        'hpv', 'kes', 'pet', 'spect', 'mri', 'ct', 'usd', 'eur', 'gbp'
    }
    
    # Common organizational suffixes
    ORG_SUFFIXES = [
        'Inc', 'LLC', 'Ltd', 'Corp', 'Corporation', 'Company', 'Co',
        'Foundation', 'Institute', 'Association', 'Organization',
        'Ministry', 'Department', 'Agency', 'Authority', 'Commission',
        'University', 'College', 'Hospital', 'Center', 'Centre'
    ]
    
    # Common role/title patterns
    ROLE_PATTERNS = [
        r'\b(?:Dr|Mr|Ms|Mrs|Prof|Professor|Director|Manager|Chief|President|'
        r'CEO|CFO|CTO|Chairman|Vice President|Secretary|Minister|Commissioner|'
        r'Executive|Officer|Coordinator|Head|Lead|Senior|Principal)\b',
    ]
    
    # Country list (top 50 most common)
    COUNTRIES = {
        'Kenya', 'United States', 'USA', 'US', 'United Kingdom', 'UK', 'Britain',
        'Canada', 'Australia', 'Germany', 'France', 'Italy', 'Spain', 'China',
        'Japan', 'India', 'Brazil', 'Mexico', 'South Africa', 'Nigeria',
        'Egypt', 'Ethiopia', 'Ghana', 'Tanzania', 'Uganda', 'Rwanda',
        'Netherlands', 'Belgium', 'Switzerland', 'Sweden', 'Norway', 'Denmark',
        'Poland', 'Russia', 'Turkey', 'Israel', 'Saudi Arabia', 'UAE',
        'Singapore', 'South Korea', 'Thailand', 'Indonesia', 'Malaysia',
        'Philippines', 'Vietnam', 'Argentina', 'Chile', 'Colombia', 'Peru'
    }
    
    def __init__(self, openai_api_key: Optional[str] = None, use_llm: bool = True):
        """
        Initialize entity extractor
        
        Args:
            openai_api_key: OpenAI API key for LLM extraction
            use_llm: Whether to use LLM for extraction (requires API key)
        """
        self.use_llm = use_llm and HAS_OPENAI and openai_api_key
        self.openai_api_key = openai_api_key
        
        if self.use_llm:
            openai.api_key = openai_api_key
        
        # Compile regex patterns
        self.role_pattern = re.compile('|'.join(self.ROLE_PATTERNS), re.IGNORECASE)
        self.org_pattern = re.compile(
            r'\b(' + '|'.join(self.ORG_SUFFIXES) + r')\b',
            re.IGNORECASE
        )
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Validate if a string is likely a person name"""
        if not name or len(name) < 3:
            return False
        
        # Must have at least 2 words for a full name
        words = name.split()
        if len(words) < 2:
            return False
        
        # Check if any word is in non-person list
        if any(word.lower() in self.NON_PERSON_WORDS for word in words):
            return False
        
        # Must start with capital letter
        if not name[0].isupper():
            return False
        
        # Should not contain special characters or numbers
        if re.search(r'[•\d@#$%^&*()\[\]{}]', name):
            return False
        
        return True
    
    def _is_valid_organization(self, name: str) -> bool:
        """Validate if a string is likely an organization name"""
        if not name or len(name) < 3:
            return False
        
        # Remove leading/trailing whitespace and bullet points
        name = name.strip(' •\t\n')
        
        # Reject if starts with bullet or special chars
        if name and name[0] in '•●◦▪▫-–—':
            return False
        
        # Reject technical acronyms with slashes (e.g., PET/SPECT, MRI/CT)
        if '/' in name and len(name.split('/')) == 2:
            parts = name.split('/')
            if all(len(p) <= 6 and p.isupper() for p in parts):
                return False
        
        # Reject single common words
        words = name.split()
        
        # Check for acronyms in blacklist
        if len(words) == 1 and words[0].lower() in self.ACRONYM_BLACKLIST:
            return False
        
        # Reject medical/technical acronyms that aren't organizations
        if len(words) == 1 and len(words[0]) <= 4 and words[0].isupper():
            # Allow known org acronyms
            known_org_acronyms = {'mtrh', 'ncceap', 'who', 'cdc', 'fda', 'nih', 'un', 'eu'}
            if words[0].lower() not in known_org_acronyms:
                return False
        
        if len(words) == 1 and words[0].lower() in self.NON_ORG_WORDS:
            return False
        
        # Reject if mostly non-org words
        if len(words) <= 2:
            non_org_count = sum(1 for w in words if w.lower() in self.NON_ORG_WORDS)
            if non_org_count >= len(words):
                return False
        
        # Reject if starts with lowercase article (likely partial extraction)
        if words[0][0].islower() and words[0] in ['the', 'a', 'an']:
            return False
        
        return True
    
    def _is_valid_location(self, name: str) -> bool:
        """Validate if a string is likely a location/country"""
        if not name or len(name) < 2:
            return False
        
        # Must be in our countries list or be a known location
        if name not in self.COUNTRIES:
            # For non-country locations, should be 1-3 words
            words = name.split()
            if len(words) > 3:
                return False
            
            # Should not contain generic words
            if any(word.lower() in ['result', 'key', 'main', 'primary'] for word in words):
                return False
        
        return True
    
    def extract_entities(self, text: str, 
                        extract_people: bool = True,
                        extract_orgs: bool = True,
                        extract_locations: bool = True) -> Dict[str, List]:
        """
        Extract all entity types from text
        
        Args:
            text: Document text to analyze
            extract_people: Extract person entities
            extract_orgs: Extract organization entities
            extract_locations: Extract location/country entities
            
        Returns:
            Dictionary with entity lists by type
        """
        results = {
            'people': [],
            'organizations': [],
            'locations': [],
            'enriched_people': []  # People with roles/orgs
        }
        
        # Try LLM extraction first (most accurate)
        if self.use_llm:
            llm_results = self._extract_with_llm(text)
            if llm_results:
                results = llm_results
                return results
        
        # Fallback to pattern-based extraction
        if HAS_SPACY and nlp:
            results = self._extract_with_spacy(text)
        else:
            results = self._extract_with_patterns(text)
        
        return results
    
    def _extract_with_llm(self, text: str) -> Optional[Dict[str, List]]:
        """
        Extract entities using OpenAI GPT
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted entities or None if extraction fails
        """
        if not self.use_llm:
            return None
        
        # Truncate text if too long (GPT has token limits)
        max_chars = 12000  # ~3000 tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = f"""Extract the following entities from the text:

1. People: Names of individuals
2. Organizations: Companies, institutions, government bodies
3. Locations: Countries, cities, regions
4. People with context: For each person, identify their role/title and affiliated organization

Return the results as JSON in this format:
{{
    "people": [
        {{"name": "John Doe", "context": "surrounding text snippet"}}
    ],
    "organizations": [
        {{"name": "Ministry of Health", "context": "surrounding text"}}
    ],
    "locations": [
        {{"name": "Kenya", "type": "country", "context": "surrounding text"}}
    ],
    "enriched_people": [
        {{
            "name": "Jane Smith",
            "role": "Director",
            "organization": "WHO",
            "country": "Kenya",
            "context": "surrounding text"
        }}
    ]
}}

Only include entities you find with reasonable confidence. Use null for missing role/organization/country fields.

Text:
{text}
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Cheaper, faster model
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from documents. Extract entities accurately and comprehensively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```json?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
            
            extracted = json.loads(content)
            
            # Convert to our entity objects
            results = {
                'people': [
                    Entity(
                        name=p['name'],
                        entity_type=EntityType.PERSON,
                        confidence=ConfidenceLevel.HIGH,
                        context=p.get('context')
                    )
                    for p in extracted.get('people', [])
                ],
                'organizations': [
                    Entity(
                        name=o['name'],
                        entity_type=EntityType.ORGANIZATION,
                        confidence=ConfidenceLevel.HIGH,
                        context=o.get('context')
                    )
                    for o in extracted.get('organizations', [])
                ],
                'locations': [
                    Entity(
                        name=l['name'],
                        entity_type=EntityType.LOCATION,
                        confidence=ConfidenceLevel.HIGH,
                        context=l.get('context'),
                        metadata={'type': l.get('type', 'unknown')}
                    )
                    for l in extracted.get('locations', [])
                ],
                'enriched_people': [
                    PersonEntity(
                        name=p['name'],
                        role=p.get('role'),
                        organization=p.get('organization'),
                        country=p.get('country'),
                        confidence=self._calculate_person_confidence(p),
                        context=p.get('context')
                    )
                    for p in extracted.get('enriched_people', [])
                ]
            }
            
            return results
            
        except Exception as e:
            print(f"⚠ LLM extraction failed: {e}")
            return None
    
    def _extract_with_spacy(self, text: str) -> Dict[str, List]:
        """
        Extract entities using spaCy NER
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted entities
        """
        doc = nlp(text)
        
        results = {
            'people': [],
            'organizations': [],
            'locations': [],
            'enriched_people': []
        }
        
        # Extract basic entities with validation
        for ent in doc.ents:
            context = text[max(0, ent.start_char-50):min(len(text), ent.end_char+50)]
            
            if ent.label_ == "PERSON":
                # Validate person name
                if self._is_valid_person_name(ent.text):
                    results['people'].append(Entity(
                        name=ent.text,
                        entity_type=EntityType.PERSON,
                        confidence=ConfidenceLevel.MEDIUM,
                        context=context
                    ))
            elif ent.label_ == "ORG":
                # Validate organization name
                if self._is_valid_organization(ent.text):
                    results['organizations'].append(Entity(
                        name=ent.text,
                        entity_type=EntityType.ORGANIZATION,
                        confidence=ConfidenceLevel.MEDIUM,
                        context=context
                    ))
            elif ent.label_ in ["GPE", "LOC"]:
                # Validate location name
                if self._is_valid_location(ent.text):
                    results['locations'].append(Entity(
                        name=ent.text,
                        entity_type=EntityType.LOCATION,
                        confidence=ConfidenceLevel.MEDIUM,
                        context=context
                    ))
        
        # Try to enrich people with roles/orgs
        results['enriched_people'] = self._enrich_people_entities(text, results['people'])
        
        return results
    
    def _extract_with_patterns(self, text: str) -> Dict[str, List]:
        """
        Extract entities using regex patterns (fallback method)
        
        Args:
            text: Text to analyze
            
        Returns:
            Extracted entities
        """
        results = {
            'people': [],
            'organizations': [],
            'locations': [],
            'enriched_people': []
        }
        
        # Extract organizations by suffix matching
        sentences = text.split('.')
        for sentence in sentences:
            # Find org suffixes
            for match in self.org_pattern.finditer(sentence):
                # Get surrounding words
                start = max(0, match.start() - 50)
                end = min(len(sentence), match.end() + 20)
                org_candidate = sentence[start:end].strip()
                
                # Clean up and extract likely org name
                words = org_candidate.split()
                if len(words) >= 2:
                    org_name = ' '.join(words[:5])  # Take up to 5 words
                    org_name = org_name.strip(' •\t\n')
                    
                    # Validate organization name
                    if self._is_valid_organization(org_name):
                        results['organizations'].append(Entity(
                            name=org_name,
                            entity_type=EntityType.ORGANIZATION,
                            confidence=ConfidenceLevel.LOW,
                            context=sentence.strip()
                        ))
        
        # Extract countries
        for country in self.COUNTRIES:
            if re.search(r'\b' + re.escape(country) + r'\b', text, re.IGNORECASE):
                # Validate it's a real location mention
                if self._is_valid_location(country):
                    # Find context
                    pattern = re.compile(r'.{0,50}\b' + re.escape(country) + r'\b.{0,50}', re.IGNORECASE)
                    matches = pattern.finditer(text)
                    for match in matches:
                        results['locations'].append(Entity(
                            name=country,
                            entity_type=EntityType.LOCATION,
                            confidence=ConfidenceLevel.MEDIUM,
                            context=match.group(0).strip()
                        ))
                        break  # Only add once per country
        
        # Extract titles/roles (helps identify people)
        role_matches = self.role_pattern.finditer(text)
        for match in role_matches:
            context_start = max(0, match.start() - 20)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            # Try to find a name after the title
            words_after = text[match.end():match.end()+50].split()
            if len(words_after) >= 2:
                # Assume next 2-3 capitalized words are the name
                name_parts = []
                for word in words_after[:3]:
                    if word and word[0].isupper() and not word.isupper():
                        name_parts.append(word)
                    else:
                        break
                
                if len(name_parts) >= 2:  # Require at least 2 words for a name
                    name = ' '.join(name_parts)
                    # Validate person name
                    if self._is_valid_person_name(name):
                        results['people'].append(Entity(
                            name=name,
                            entity_type=EntityType.PERSON,
                            confidence=ConfidenceLevel.LOW,
                            context=context
                        ))
        
        return results
    
    def _enrich_people_entities(self, text: str, people: List[Entity]) -> List[PersonEntity]:
        """
        Try to find roles and organizations for people
        
        Args:
            text: Full text
            people: List of person entities
            
        Returns:
            List of enriched person entities
        """
        enriched = []
        
        for person in people:
            # Find context around person's name
            name_pattern = re.escape(person.name)
            matches = re.finditer(r'.{0,100}\b' + name_pattern + r'\b.{0,100}', text, re.IGNORECASE)
            
            for match in matches:
                context = match.group(0)
                
                # Look for role/title
                role = None
                role_match = self.role_pattern.search(context)
                if role_match:
                    role = role_match.group(0)
                
                # Look for organization
                org = None
                for ent in self.org_pattern.finditer(context):
                    # Extract likely org name
                    start = max(0, ent.start() - 30)
                    org_candidate = context[start:ent.end()].strip()
                    words = org_candidate.split()
                    if words:
                        org = ' '.join(words[-5:])  # Last 5 words including suffix
                        break
                
                # Look for country
                country = None
                for c in self.COUNTRIES:
                    if re.search(r'\b' + re.escape(c) + r'\b', context, re.IGNORECASE):
                        country = c
                        break
                
                enriched.append(PersonEntity(
                    name=person.name,
                    role=role,
                    organization=org,
                    country=country,
                    confidence=self._calculate_person_confidence({
                        'name': person.name,
                        'role': role,
                        'organization': org,
                        'country': country
                    }),
                    context=context
                ))
                break  # Only process first occurrence
        
        return enriched
    
    def _calculate_person_confidence(self, person_data: Dict) -> ConfidenceLevel:
        """
        Calculate confidence level based on completeness
        
        Args:
            person_data: Dictionary with person fields
            
        Returns:
            Confidence level
        """
        fields = [
            person_data.get('name'),
            person_data.get('role'),
            person_data.get('organization'),
            person_data.get('country')
        ]
        
        populated = sum(1 for f in fields if f is not None)
        percentage = (populated / len(fields)) * 100
        
        if percentage >= 75:
            return ConfidenceLevel.HIGH
        elif percentage >= 50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def format_results(self, results: Dict[str, List], 
                      include_low_confidence: bool = False) -> str:
        """
        Format extraction results as readable text
        
        Args:
            results: Extraction results
            include_low_confidence: Whether to include low-confidence entities
            
        Returns:
            Formatted string
        """
        output = []
        
        # People with context
        enriched = results.get('enriched_people', [])
        if enriched:
            output.append("=" * 60)
            output.append("PEOPLE (with roles & organizations)")
            output.append("=" * 60)
            
            for person in enriched:
                if not include_low_confidence and person.confidence == ConfidenceLevel.LOW:
                    continue
                
                output.append(f"\n👤 {person.name}")
                if person.role:
                    output.append(f"   Role: {person.role}")
                if person.organization:
                    output.append(f"   Organization: {person.organization}")
                if person.country:
                    output.append(f"   Country: {person.country}")
                output.append(f"   Confidence: {person.confidence.value.upper()}")
                output.append(f"   Completeness: {person.completeness_score():.0f}%")
        
        # Organizations
        orgs = results.get('organizations', [])
        if orgs:
            output.append("\n" + "=" * 60)
            output.append("ORGANIZATIONS")
            output.append("=" * 60)
            
            # Deduplicate
            seen = set()
            for org in orgs:
                if not include_low_confidence and org.confidence == ConfidenceLevel.LOW:
                    continue
                if org.name.lower() not in seen:
                    seen.add(org.name.lower())
                    output.append(f"\n🏢 {org.name}")
                    output.append(f"   Confidence: {org.confidence.value.upper()}")
        
        # Locations
        locations = results.get('locations', [])
        if locations:
            output.append("\n" + "=" * 60)
            output.append("LOCATIONS / COUNTRIES")
            output.append("=" * 60)
            
            # Deduplicate
            seen = set()
            for loc in locations:
                if not include_low_confidence and loc.confidence == ConfidenceLevel.LOW:
                    continue
                if loc.name.lower() not in seen:
                    seen.add(loc.name.lower())
                    output.append(f"\n🌍 {loc.name}")
                    output.append(f"   Confidence: {loc.confidence.value.upper()}")
        
        return '\n'.join(output) if output else "No entities found."
    
    def export_to_dict(self, results: Dict[str, List]) -> Dict:
        """
        Export results to dictionary format for JSON export
        
        Args:
            results: Extraction results
            
        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            'people': [e.to_dict() for e in results.get('people', [])],
            'organizations': [e.to_dict() for e in results.get('organizations', [])],
            'locations': [e.to_dict() for e in results.get('locations', [])],
            'enriched_people': [e.to_dict() for e in results.get('enriched_people', [])]
        }
