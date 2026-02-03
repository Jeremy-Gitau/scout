# Entity Extraction Feature

## Overview

Scout now includes a powerful entity extraction mode that can identify and extract structured information from documents:

- **People** with their roles, organizations, and countries
- **Organizations** (companies, institutions, government bodies)
- **Locations** (countries, regions, cities)

## Key Features

### 1. **Hybrid Extraction Approach**
   - **Pattern-based**: Fast, works offline, good for well-formatted documents
   - **spaCy NER**: Better accuracy with Named Entity Recognition
   - **LLM-powered**: Highest accuracy using GPT-4o-mini (requires OpenAI API key)

### 2. **Confidence Scoring**
   - **HIGH**: Complete information with strong context (75-100% completeness)
   - **MEDIUM**: Partial information or weak context (50-74% completeness)
   - **LOW**: Incomplete or uncertain (<50% completeness)

### 3. **Completeness Tracking**
   For people entities, tracks presence of:
   - Name ✓
   - Role (optional)
   - Organization (optional)
   - Country (optional)

### 4. **Multiple Export Formats**
   - JSON (structured data)
   - CSV (spreadsheet)
   - TXT (formatted report)
   - Excel (coming soon)

## Usage Guide

### Basic Workflow

1. **Switch to Entity Mode**
   - Click the "👥 Entities" button in the header

2. **Select Documents**
   - Click "📁 Select Folder" to scan multiple documents
   - OR "📄 Select File" to process a single document

3. **Configure Settings** (Optional)
   - Enter OpenAI API key for LLM extraction
   - Toggle extraction types (People, Organizations, Locations)
   - Enable "Show low confidence" to include uncertain matches

4. **Extract Entities**
   - Click "🔍 Extract Entities"
   - Wait for processing to complete
   - View results color-coded by confidence:
     - 🟢 Green = HIGH confidence
     - 🟡 Yellow = MEDIUM confidence
     - 🔴 Red = LOW confidence

5. **Export Results**
   - Click "💾 Export Entities"
   - Choose format (JSON/CSV/TXT)
   - Save to desired location

### Using LLM Extraction

For best results with complex documents:

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Enter the key in the "OpenAI API Key" field
3. Check "🤖 Use LLM (higher accuracy)"
4. Click "💾 Save Key" to store for the session
5. Run extraction as normal

**Note**: LLM extraction uses GPT-4o-mini which costs ~$0.15 per 1M input tokens and ~$0.60 per 1M output tokens.

### Tips for Best Results

#### Document Types
- **Best**: Press releases, news articles, policy briefs, government reports
- **Good**: Academic papers, business documents, meeting minutes
- **Limited**: Technical documentation, legal contracts (may lack person context)

#### Extraction Modes
- **Pattern/spaCy** (default): Fast, free, good for well-structured docs
- **LLM**: Slower, costs API fees, excellent for complex/ambiguous docs

#### Filtering Results
- Uncheck "⚠️ Show low confidence" to hide uncertain matches
- Review MEDIUM confidence results manually
- HIGH confidence results are generally reliable

## Examples

### Example 1: Policy Brief
Input document mentions:
- "Dr. Jane Smith, Director of Health at the Ministry of Health, Kenya..."

Extracted:
```
👤 Dr. Jane Smith
   Role: Director
   Organization: Ministry of Health
   Country: Kenya
   Confidence: HIGH
   Completeness: 100%
```

### Example 2: Academic Paper
Input document has:
- "...according to John Doe (2023)..."

Extracted:
```
👤 John Doe
   Role: -
   Organization: -
   Country: -
   Confidence: MEDIUM
   Completeness: 25%
```

### Example 3: News Article
Input mentions:
- "The World Health Organization announced..."
- "Officials from Kenya and Tanzania met..."

Extracted:
```
🏢 World Health Organization
   Confidence: HIGH

🌍 Kenya
   Confidence: HIGH

🌍 Tanzania
   Confidence: HIGH
```

## Technical Details

### Architecture
```
EntityExtractor
├── Pattern-based extraction (regex, keywords)
├── spaCy NER (if available)
└── OpenAI GPT-4o-mini (if API key provided)
```

### Data Model
```python
PersonEntity:
  - name: str
  - role: Optional[str]
  - organization: Optional[str]
  - country: Optional[str]
  - confidence: ConfidenceLevel
  - context: Optional[str]  # Surrounding text snippet

Entity:
  - name: str
  - entity_type: EntityType (PERSON/ORGANIZATION/LOCATION)
  - confidence: ConfidenceLevel
  - context: Optional[str]
```

### API Integration
The LLM extraction sends prompts to OpenAI's API:
- Model: `gpt-4o-mini`
- Temperature: 0.1 (for consistency)
- Max tokens: 2000 (per request)
- Input limit: ~12,000 characters per document

## Troubleshooting

### "No entities found"
- Document may be too short (<50 characters)
- Try enabling "Show low confidence"
- Switch to LLM extraction for better results

### LLM extraction fails
- Check API key is correct
- Ensure you have API credits available
- Check internet connection
- Review logs for specific error messages

### Incorrect extractions
- LOW/MEDIUM confidence results may be inaccurate
- LLM mode generally more accurate than pattern matching
- Consider the document type and structure

### Slow performance
- Pattern/spaCy mode is fastest
- LLM mode requires API calls (slower but more accurate)
- Large documents are automatically truncated to 12,000 characters

## Best Practices

1. **Start with pattern matching**: It's free and fast
2. **Use LLM for important documents**: When accuracy matters
3. **Review MEDIUM confidence**: May need manual verification
4. **Export early, export often**: Save results as you work
5. **Check completeness scores**: Higher is better for people entities

## Limitations

- Person name detection depends on proper capitalization
- Role/org/country extraction requires context in the text
- Some ambiguous names may be missed or misclassified
- Non-English names may have lower accuracy (especially without LLM)
- Very long documents are truncated (first ~12,000 characters)

## Future Enhancements

Planned improvements:
- Relationship extraction (who works with whom)
- Entity linking (connecting same entities across documents)
- Custom entity types (e.g., projects, events)
- Batch processing with progress tracking
- Entity validation and enrichment from external databases
- Support for more languages
