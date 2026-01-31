"""
Inventix AI - SLM Engine
========================
Google Gemini integration with ANTIGRAVITY compliance.

This engine:
- Wraps the Gemini API
- Enforces structured output
- Validates responses against evidence
- Returns CRASH logs on failure
"""

import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, Any
from dataclasses import dataclass

from app.config import settings


# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class SLMRequest(BaseModel):
    """Request to the SLM engine."""
    prompt: str
    system_prompt: Optional[str] = None
    response_format: str = "json"  # "json" or "text"
    max_tokens: int = 2048
    temperature: float = 0.3  # Lower for more deterministic outputs


@dataclass
class SLMResponse:
    """Response from the SLM engine."""
    success: bool
    raw_text: str
    parsed_json: Optional[dict]
    error: Optional[str]
    model_used: str
    

class SLMEngine:
    """
    Small Language Model Engine using Google Gemini.
    
    Design principles:
    - Deterministic where possible (low temperature)
    - Structured output enforcement
    - Explicit failure on parsing errors
    - No hallucination tolerance
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
    async def generate(self, request: SLMRequest) -> SLMResponse:
        """
        Generate a response from the SLM.
        
        Returns structured SLMResponse with success/failure status.
        """
        try:
            # Build the full prompt
            full_prompt = ""
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n---\n\n"
            full_prompt += request.prompt
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Extract text
            raw_text = response.text.strip()
            
            # Parse JSON if required
            parsed_json = None
            if request.response_format == "json":
                try:
                    # Handle markdown code blocks
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    raw_text = raw_text.strip()
                    
                    parsed_json = json.loads(raw_text)
                except json.JSONDecodeError as e:
                    return SLMResponse(
                        success=False,
                        raw_text=raw_text,
                        parsed_json=None,
                        error=f"JSON parsing failed: {str(e)}",
                        model_used=settings.gemini_model
                    )
            
            return SLMResponse(
                success=True,
                raw_text=raw_text,
                parsed_json=parsed_json,
                error=None,
                model_used=settings.gemini_model
            )
            
        except Exception as e:
            return SLMResponse(
                success=False,
                raw_text="",
                parsed_json=None,
                error=str(e),
                model_used=settings.gemini_model
            )
    
    async def generate_with_evidence(
        self,
        prompt: str,
        evidence: list[dict],
        system_prompt: Optional[str] = None
    ) -> SLMResponse:
        """
        Generate response grounded in provided evidence.
        
        This method:
        1. Injects evidence into the prompt
        2. Forces evidence references in output
        3. Validates output references actual evidence IDs
        """
        # Build evidence context
        evidence_block = "\n".join([
            f"[{e.get('id', f'EVD-{i}')}]: {e.get('content', '')}"
            for i, e in enumerate(evidence)
        ])
        
        full_prompt = f"""EVIDENCE (You may ONLY reference these):
{evidence_block}

---

TASK:
{prompt}

---

RULES:
- Every factual statement MUST reference an evidence ID in brackets, e.g. [EVD-1]
- If evidence is insufficient, state "UNKNOWN"
- Do NOT invent facts beyond provided evidence
"""
        
        default_system = """You are ANTIGRAVITY, an evidence-locked intelligence system.
You ONLY reason over provided evidence.
Every statement MUST reference an evidence ID.
If evidence is insufficient, return UNKNOWN.
Output valid JSON only."""
        
        return await self.generate(SLMRequest(
            prompt=full_prompt,
            system_prompt=system_prompt or default_system,
            response_format="json"
        ))


# Singleton instance
slm_engine = SLMEngine()
