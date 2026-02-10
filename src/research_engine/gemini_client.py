"""Google Gemini API client for LLM-based analysis."""

import json
import structlog
import google.generativeai as genai
from typing import Dict, Any

from schemas.payload import LLMPayload
from schemas.llm_output import AnalysisOutput
from .prompts import PromptManager

logger = structlog.get_logger()


class GeminiClient:
    """Client for Google Gemini API.
    
    Generates investment analysis using structured prompts.
    Validates output against Pydantic schema.
    """
    
    def __init__(self, api_key: str, prompt_manager: PromptManager):
        """Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
            prompt_manager: Prompt manager with active prompt version
        """
        genai.configure(api_key=api_key)
        
        self.prompt_manager = prompt_manager
        self.logger = logger.bind(
            service="gemini_client",
            prompt_version=prompt_manager.version
        )
        
        # Initialize model with config from prompt
        config = prompt_manager.config
        self.model = genai.GenerativeModel(
            model_name=config.get('model', 'gemma-3-27b-it'),
            generation_config={
                'temperature': config.get('temperature', 0.3),
                'top_p': config.get('top_p', 0.8),
                'max_output_tokens': config.get('max_output_tokens', 4096),
            }
        )
    
    def generate_analysis(
        self,
        payload: LLMPayload,
        max_retries: int = 2
    ) -> AnalysisOutput:
        """Generate investment analysis from payload.
        
        Args:
            payload: Structured data payload
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Validated AnalysisOutput
            
        Raises:
            Exception: If generation fails after retries
        """
        self.logger.info("analysis_generation_started")
        
        for attempt in range(max_retries):
            try:
                # Build full prompt
                full_prompt = self._build_prompt(payload)
                
                # Generate response
                self.logger.debug("calling_gemini_api")
                response = self.model.generate_content(full_prompt)
                
                # Extract text
                response_text = response.text
                
                # Parse JSON
                self.logger.debug("parsing_json_response")
                parsed = self._extract_json(response_text)
                
                # Normalize LLM output (convert lists to strings if needed)
                parsed = self._normalize_llm_output(parsed)
                
                # Validate against schema
                analysis = AnalysisOutput.model_validate(parsed)
                
                self.logger.info(
                    "analysis_generation_complete",
                    opportunity_count=len(analysis.opportunities),
                    scenario_count=len(analysis.scenarios)
                )
                
                return analysis
                
            except Exception as e:
                self.logger.warning(
                    "generation_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt >= max_retries - 1:
                    self.logger.error("generation_failed_permanently")
                    raise
        
        raise Exception("Should not reach here")
    
    def _build_prompt(self, payload: LLMPayload) -> str:
        """Build complete prompt from system + user templates.
        
        Args:
            payload: Data payload
            
        Returns:
            Complete prompt string
        """
        # Convert payload to JSON
        json_payload = payload.model_dump_json(indent=2)
        
        # Format user prompt
        user_prompt = self.prompt_manager.format_user_prompt(
            json_payload=json_payload,
            weekly_budget=payload.weekly_budget_usd,
            investment_horizon=payload.investment_horizon_years,
            fear_greed_label=payload.macro_environment.fear_greed_label,
            fear_greed_score=payload.macro_environment.fear_greed_score
        )
        
        # Combine system + user
        full_prompt = f"{self.prompt_manager.system_prompt}\n\n{user_prompt}"
        
        return full_prompt
    
    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response text.
        
        Gemini sometimes wraps JSON in markdown code blocks.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed JSON dict
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        elif text.startswith('```'):
            text = text[3:]  # Remove ```
        
        if text.endswith('```'):
            text = text[:-3]  # Remove trailing ```
        
        text = text.strip()
        
        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.logger.error("json_parse_failed", error=str(e), text_preview=text[:200])
            raise
    
    def _normalize_llm_output(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize LLM output to match schema expectations.
        
        Sometimes the LLM returns lists when strings are expected.
        Convert them to comma-separated strings.
        
        Args:
            parsed: Raw parsed JSON from LLM
            
        Returns:
            Normalized dict matching schema
        """
        # Convert list fields to strings if needed
        list_to_string_fields = ['themes_in_focus', 'risks_to_watch']
        
        for field in list_to_string_fields:
            if field in parsed and isinstance(parsed[field], list):
                # Join list items with commas
                parsed[field] = ', '.join(str(item) for item in parsed[field])
                self.logger.debug(
                    "normalized_list_field",
                    field=field,
                    original_type="list",
                    converted_to="string"
                )
        
        return parsed

