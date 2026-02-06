"""
Custom AI-powered extraction module for Scout.
Allows users to extract any data from documents using custom prompts and various AI models.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Supported AI models for custom extraction"""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"


class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    # Future: ANTHROPIC = "anthropic"
    # Future: GOOGLE = "google"


@dataclass
class CustomExtractionResult:
    """Result from custom extraction"""
    source_file: str
    extracted_data: Dict[str, Any]
    raw_response: str
    model_used: str
    prompt_used: str
    success: bool
    error_message: Optional[str] = None


class CustomExtractor:
    """
    Custom extractor that uses AI models with user-defined prompts
    to extract any type of data from documents.
    """
    
    def __init__(self, api_key: str, model: str, provider: str = "openai"):
        """
        Initialize the custom extractor.
        
        Args:
            api_key: API key for the AI provider
            model: Model identifier (e.g., "gpt-4o-mini")
            provider: AI provider name (default: "openai")
        """
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self._client = None
        
    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Install with: pip install openai")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                raise
        return self._client
    
    def extract(self, text: str, prompt: str, source_file: str = "") -> CustomExtractionResult:
        """
        Extract data from text using the custom prompt.
        
        Args:
            text: Text content to extract from
            prompt: Custom extraction prompt from user
            source_file: Source file path (for tracking)
            
        Returns:
            CustomExtractionResult with extracted data
        """
        if self.provider == "openai":
            return self._extract_with_openai(text, prompt, source_file)
        else:
            error_msg = f"Provider '{self.provider}' not yet supported"
            logger.error(error_msg)
            return CustomExtractionResult(
                source_file=source_file,
                extracted_data={},
                raw_response="",
                model_used=self.model,
                prompt_used=prompt,
                success=False,
                error_message=error_msg
            )
    
    def _extract_with_openai(self, text: str, prompt: str, source_file: str) -> CustomExtractionResult:
        """
        Extract data using OpenAI API.
        
        Args:
            text: Text to extract from
            prompt: Custom extraction prompt
            source_file: Source file path
            
        Returns:
            CustomExtractionResult
        """
        try:
            client = self._get_openai_client()
            
            # Build the system message with instructions
            system_message = """You are an expert data extraction specialist with exceptional accuracy and attention to detail.

## YOUR ROLE:
Extract specific information from documents according to user instructions. Your extractions must be precise, verifiable, and structured.

## CORE PRINCIPLES:
1. ACCURACY FIRST: Only extract information explicitly stated in the text. Never infer, assume, or hallucinate data.
2. COMPLETE EXTRACTION: Find all instances of requested information, not just the first occurrence.
3. PRESERVE CONTEXT: Maintain the original meaning and context of extracted information.
4. STRUCTURED OUTPUT: Return well-organized JSON that matches the requested schema exactly.

## OUTPUT REQUIREMENTS:
- Valid JSON format only (no markdown, no code blocks)
- Use descriptive, specific key names
- Use arrays for multiple items of the same type
- Use null for missing optional fields, omit if unknown
- Include metadata when relevant (confidence, source location)

## QUALITY GUARDRAILS:
- If no matching information exists, return {}
- If information is ambiguous, include it with a note in a 'notes' field
- Remove duplicates within the same extraction
- Standardize formats (dates, phone numbers, currencies) when possible
- Flag partial or uncertain extractions explicitly

## ERROR HANDLING:
- If the text is too short or irrelevant, return {"error": "insufficient_content"}
- If the extraction task is unclear, return {"error": "unclear_instructions"}
- Never leave the response empty or malformed"""
            
            # Build the user message with the custom prompt and text
            user_message = f"""{prompt}

TEXT TO ANALYZE:
{text[:8000]}"""  # Limit text to avoid token limits
            
            # Make API call
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000,
                response_format={"type": "json_object"}  # Enforce JSON response
            )
            
            # Parse response
            raw_response = response.choices[0].message.content
            extracted_data = json.loads(raw_response)
            
            logger.info(f"Successfully extracted data from {source_file} using {self.model}")
            
            return CustomExtractionResult(
                source_file=source_file,
                extracted_data=extracted_data,
                raw_response=raw_response,
                model_used=self.model,
                prompt_used=prompt,
                success=True
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse AI response as JSON: {e}"
            logger.error(error_msg)
            return CustomExtractionResult(
                source_file=source_file,
                extracted_data={},
                raw_response=raw_response if 'raw_response' in locals() else "",
                model_used=self.model,
                prompt_used=prompt,
                success=False,
                error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            return CustomExtractionResult(
                source_file=source_file,
                extracted_data={},
                raw_response="",
                model_used=self.model,
                prompt_used=prompt,
                success=False,
                error_message=error_msg
            )
    
    @staticmethod
    def get_available_models() -> List[tuple]:
        """
        Get list of available models.
        
        Returns:
            List of (model_id, display_name) tuples
        """
        return [
            (AIModel.GPT_4O_MINI.value, "GPT-4o Mini (Fast & Affordable)"),
            (AIModel.GPT_4O.value, "GPT-4o (Recommended)"),
            (AIModel.GPT_4_TURBO.value, "GPT-4 Turbo"),
            (AIModel.GPT_4.value, "GPT-4"),
            (AIModel.GPT_35_TURBO.value, "GPT-3.5 Turbo (Legacy)"),
        ]
    
    @staticmethod
    def get_example_prompts() -> List[tuple]:
        """
        Get list of example prompts for users.
        
        Returns:
            List of (name, prompt) tuples
        """
        return [
            ("Custom", ""),
            
            ("Dates & Deadlines", """## TASK: Extract temporal information

Identify and extract all dates, deadlines, and time-sensitive information from the document.

## EXTRACTION CRITERIA:
- Explicit dates (e.g., "January 15, 2024", "12/31/23")
- Relative time references (e.g., "next week", "in 30 days")
- Deadlines with associated tasks or deliverables
- Scheduled events with times and durations
- Recurring patterns (e.g., "every Monday", "quarterly")

## OUTPUT SCHEMA:
{
  "dates": [{"date": "YYYY-MM-DD or original format", "context": "what this date refers to", "type": "deadline|event|reference"}],
  "deadlines": [{"date": "YYYY-MM-DD", "description": "what is due", "priority": "high|medium|low|unknown"}],
  "events": [{"date": "YYYY-MM-DD", "time": "HH:MM or null", "title": "event name", "duration": "length or null"}],
  "recurring": [{"pattern": "frequency description", "activity": "what recurs"}]
}

## GUARDRAILS:
- Standardize dates to YYYY-MM-DD when possible
- If year is missing, note it in context
- Mark uncertain dates with "approx_" prefix
- Skip vague references like "soon" unless paired with specific context"""),
            
            ("Prices & Products", """## TASK: Extract product and pricing information

Identify all products, services, prices, and quantities mentioned in the document.

## EXTRACTION CRITERIA:
- Product/service names and descriptions
- Prices in any currency format
- Quantities, units, and measurements
- SKUs, model numbers, or product codes
- Discounts, taxes, or additional fees
- Package deals or bundled offerings

## OUTPUT SCHEMA:
{
  "products": [
    {
      "name": "product name",
      "description": "brief description or null",
      "price": "numerical value",
      "currency": "USD|EUR|etc",
      "quantity": "number or null",
      "unit": "each|dozen|kg|etc",
      "sku": "product code or null",
      "discount": "percentage or amount or null"
    }
  ],
  "total_amounts": [{"label": "subtotal|tax|total", "amount": "value", "currency": "USD"}]
}

## GUARDRAILS:
- Always include currency symbol or code
- Separate base price from discounts
- Note if price is per unit or total
- Flag promotional or temporary pricing
- If quantity is implicit ("3 for $10"), calculate unit price

## EXAMPLE:
Input: "MacBook Pro 16\" at $2,499 (20% off), qty: 2"
Output: {"products": [{"name": "MacBook Pro 16\"", "price": 2499, "currency": "USD", "quantity": 2, "discount": "20%"}]}"""),
            
            ("Contact Information", """## TASK: Extract contact details

Identify all contact information including people, emails, phone numbers, addresses, and web URLs.

## EXTRACTION CRITERIA:
- Email addresses (validate format)
- Phone numbers (all formats: +1-555-0100, (555) 0100, etc.)
- Physical addresses (street, city, state, zip, country)
- Websites and social media URLs
- Names associated with contact info when available
- Fax numbers and alternative contact methods

## OUTPUT SCHEMA:
{
  "contacts": [
    {
      "name": "person or organization name or null",
      "role": "title/position or null",
      "emails": ["email1@domain.com"],
      "phones": [{"number": "formatted number", "type": "mobile|office|fax|unknown"}],
      "address": {"street": "", "city": "", "state": "", "zip": "", "country": ""},
      "websites": ["https://example.com"],
      "social_media": {"platform": "username or url"}
    }
  ],
  "standalone_emails": ["email addresses without associated names"],
  "standalone_phones": ["phone numbers without context"]
}

## GUARDRAILS:
- Validate email format (must contain @ and domain)
- Standardize phone numbers to E.164 when possible (+1234567890)
- Keep international prefixes (country codes)
- Group contact details by person/entity when clustered together
- Mark personal vs business emails if distinguishable
- Include extension numbers for office phones

## EXAMPLE:
Input: "Contact John Doe at john@company.com or +1-555-0123 (office)"
Output: {"contacts": [{"name": "John Doe", "emails": ["john@company.com"], "phones": [{"number": "+15550123", "type": "office"}]}]}"""),
            
            ("Action Items", """## TASK: Extract actionable tasks and assignments

Identify all action items, tasks, to-dos, and assigned responsibilities from the document.

## EXTRACTION CRITERIA:
- Explicit tasks ("must do", "should complete", "need to")
- Assigned actions with responsible parties
- Follow-up items from meetings or discussions
- Pending decisions or approvals
- Dependencies between tasks
- Priority levels or urgency indicators

## OUTPUT SCHEMA:
{
  "action_items": [
    {
      "task": "description of what needs to be done",
      "assignee": "person responsible or 'unassigned'",
      "deadline": "YYYY-MM-DD or relative time or null",
      "priority": "high|medium|low|urgent|unknown",
      "status": "pending|in-progress|completed|blocked",
      "dependencies": ["list of prerequisite tasks or null"],
      "context": "why this task exists or null"
    }
  ],
  "decisions_needed": [{"decision": "what needs to be decided", "by_whom": "decision maker", "by_when": "date or null"}],
  "follow_ups": [{"item": "what to follow up on", "with_whom": "person or group"}]
}

## GUARDRAILS:
- Distinguish between completed and pending tasks (look for past vs future tense)
- If assignee is unclear, use "team" or "unassigned"
- Extract priority from keywords: urgent, ASAP, critical, must, should, could
- Note blockers explicitly ("waiting for", "pending", "blocked by")
- Preserve the original action verb ("review", "approve", "implement")

## EXAMPLE:
Input: "Sarah must review the proposal by Friday. John to follow up with client next week."
Output: {"action_items": [{"task": "review the proposal", "assignee": "Sarah", "deadline": "Friday", "priority": "high"}, {"task": "follow up with client", "assignee": "John", "deadline": "next week", "priority": "medium"}]}"""),
            
            ("Key Metrics", """## TASK: Extract quantitative data and measurements

Identify all numerical metrics, KPIs, statistics, measurements, and performance indicators.

## EXTRACTION CRITERIA:
- Numerical values with units of measurement
- Percentages, ratios, and rates
- Financial figures (revenue, costs, budgets)
- Performance metrics (growth, conversion, retention)
- Statistical data (averages, medians, ranges)
- Comparative data (year-over-year, benchmarks)
- Targets and goals with actual values

## OUTPUT SCHEMA:
{
  "metrics": [
    {
      "name": "metric name or description",
      "value": "numerical value",
      "unit": "unit of measurement (%, $, users, etc)",
      "category": "financial|performance|operational|other",
      "time_period": "Q1 2024, Jan-Dec, etc or null",
      "change": "+15%, -3%, etc or null",
      "context": "additional relevant info",
      "is_target": true|false,
      "comparison": {"baseline": "value", "type": "YoY|MoM|vs_target"}
    }
  ],
  "summary": {"total_metrics": 0, "categories": ["list of unique categories"]}
}

## GUARDRAILS:
- Always include units (convert implicit units: "2K users" → value: 2000, unit: "users")
- Distinguish between targets/goals and actual values
- Preserve precision (don't round unless specified)
- Note if value is estimated, projected, or actual
- Include time periods for temporal metrics
- Extract ranges as {"min": X, "max": Y, "unit": "Z"}
- Flag outliers or notable values

## EXAMPLE:
Input: "Q4 revenue reached $2.5M, up 23% YoY. Customer retention at 94%."
Output: {"metrics": [{"name": "Q4 revenue", "value": 2500000, "unit": "$", "category": "financial", "time_period": "Q4", "change": "+23%", "comparison": {"type": "YoY"}}, {"name": "customer retention", "value": 94, "unit": "%", "category": "performance"}]}"""),
            
            ("Requirements", """## TASK: Extract requirements and specifications

Identify all requirements, specifications, criteria, constraints, and must-have features.

## EXTRACTION CRITERIA:
- Functional requirements (what system must do)
- Non-functional requirements (performance, security, usability)
- Technical specifications and constraints
- Business rules and policies
- Compliance and regulatory requirements
- User acceptance criteria
- Dependencies and prerequisites

## OUTPUT SCHEMA:
{
  "requirements": [
    {
      "id": "auto-increment or null",
      "type": "functional|non-functional|technical|business|compliance",
      "priority": "must-have|should-have|nice-to-have|won't-have",
      "description": "clear statement of requirement",
      "rationale": "why this is needed or null",
      "acceptance_criteria": ["measurable criteria for completion"],
      "constraints": ["limitations or restrictions"],
      "dependencies": ["related requirements"]
    }
  ],
  "specifications": [
    {"parameter": "spec name", "value": "required value", "tolerance": "acceptable range or null"}
  ]
}

## GUARDRAILS:
- Prioritize using MoSCoW method keywords: must, should, could, won't
- Convert ambiguous language to specific requirements
- Extract implied constraints ("under $X" → constraint)
- Note if requirement is testable/measurable
- Preserve requirement IDs if present (REQ-001, etc.)
- Flag conflicting requirements

## EXAMPLE:
Input: "The system must process transactions in under 2 seconds. Should support 10K concurrent users."
Output: {"requirements": [{"type": "non-functional", "priority": "must-have", "description": "process transactions in under 2 seconds", "acceptance_criteria": ["transaction time < 2s"]}, {"type": "non-functional", "priority": "should-have", "description": "support 10,000 concurrent users"}]}"""),
            
            ("Risks & Issues", """## TASK: Extract risks, issues, and concerns

Identify all risks, problems, issues, concerns, threats, vulnerabilities, and potential obstacles.

## EXTRACTION CRITERIA:
- Active issues requiring attention
- Potential risks and threats
- Concerns raised by stakeholders
- Blockers and impediments
- Dependencies creating risk
- Mitigation strategies mentioned
- Severity and impact levels

## OUTPUT SCHEMA:
{
  "risks": [
    {
      "description": "risk description",
      "type": "technical|financial|operational|strategic|compliance",
      "likelihood": "high|medium|low|unknown",
      "impact": "high|medium|low|unknown",
      "mitigation": "proposed mitigation strategy or null",
      "owner": "person responsible for monitoring or null",
      "status": "open|mitigated|accepted|closed"
    }
  ],
  "issues": [
    {
      "description": "issue description",
      "severity": "critical|high|medium|low",
      "affected_area": "what is impacted",
      "reported_by": "who raised it or null",
      "reported_date": "date or null",
      "resolution_plan": "how to resolve or null",
      "status": "open|in-progress|resolved"
    }
  ],
  "concerns": [
    {"concern": "description", "stakeholder": "who raised it", "category": "budget|timeline|quality|scope|other"}
  ],
  "blockers": [
    {"blocker": "what is blocking", "blocks": "what is being blocked", "resolution_needed": "what needs to happen"}
  ]
}

## GUARDRAILS:
- Distinguish between active issues (happening now) and risks (might happen)
- Extract severity from keywords: critical, urgent, major, minor, blocker
- Look for likelihood indicators: likely, possible, unlikely, rare
- Capture both problem and solution if mentioned
- Note if issue is escalated or has dependencies
- Flag unresolved critical issues
- Preserve original concern language (don't soften)

## EXAMPLE:
Input: "Critical bug in payment system affecting 15% of transactions. High risk of regulatory penalty if not fixed by month-end. Team concerned about timeline feasibility."
Output: {"issues": [{"description": "bug in payment system affecting 15% of transactions", "severity": "critical", "affected_area": "payment system"}], "risks": [{"description": "regulatory penalty if not fixed by month-end", "type": "compliance", "likelihood": "high", "impact": "high"}], "concerns": [{"concern": "timeline feasibility", "stakeholder": "team", "category": "timeline"}]}"""),
        ]


def aggregate_custom_results(results: List[CustomExtractionResult]) -> Dict[str, Any]:
    """
    Aggregate results from multiple files.
    
    Args:
        results: List of CustomExtractionResult objects
        
    Returns:
        Dictionary with aggregated data
    """
    aggregated = {
        "total_files": len(results),
        "successful_extractions": sum(1 for r in results if r.success),
        "failed_extractions": sum(1 for r in results if not r.success),
        "by_file": {},
        "all_extracted_data": []
    }
    
    for result in results:
        aggregated["by_file"][result.source_file] = {
            "success": result.success,
            "data": result.extracted_data,
            "error": result.error_message
        }
        
        if result.success and result.extracted_data:
            aggregated["all_extracted_data"].append({
                "source": result.source_file,
                "data": result.extracted_data
            })
    
    return aggregated
