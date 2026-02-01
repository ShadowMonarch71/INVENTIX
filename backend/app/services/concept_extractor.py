"""
Inventix AI - Concept Extractor
===============================
Keyword and concept extraction with evidence-locked processing.
Uses deterministic + SLM-assisted extraction.
"""

import re
from collections import Counter
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConceptCategory(str, Enum):
    """Categories of extracted concepts."""
    COMMON_DOMAIN = "common_domain"  # Standard domain terms
    DIFFERENTIATING = "differentiating"  # Potentially unique/novel terms
    METHODOLOGICAL = "methodological"  # Methods and processes
    TECHNICAL = "technical"  # Technical specifications


@dataclass
class ExtractedConcept:
    """A single extracted concept with metadata."""
    term: str
    category: ConceptCategory
    frequency: int
    weight: float  # Relevance weight 0-1
    context: Optional[str] = None  # Surrounding context
    is_known: Optional[bool] = None  # Whether this exists in prior art


@dataclass
class ConceptExtractionResult:
    """Result of concept extraction."""
    success: bool
    concepts: List[ExtractedConcept]
    summary: Dict[str, int]  # Category counts
    differentiating_terms: List[str]
    common_terms: List[str]
    error_message: Optional[str] = None


class ConceptExtractor:
    """
    ANTIGRAVITY Concept Extractor
    
    Extracts concepts using deterministic + SLM-assisted methods:
    - Core keywords
    - Technical terms
    - Methodological phrases
    - Domain-specific concepts
    
    Weights terms by relevance and frequency.
    Distinguishes common vs differentiating terms.
    """

    # Common stopwords to filter
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'we', 'us', 'our', 'you', 'your', 'he', 'she', 'him', 'her', 'his',
        'which', 'what', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'not', 'only', 'same', 'so', 'than', 'too', 'very',
        'just', 'also', 'now', 'here', 'there', 'then', 'once', 'if', 'when',
        'any', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'however', 'therefore', 'thus', 'hence'
    }

    # Patterns for technical terms
    TECHNICAL_PATTERNS = [
        r'\b\d+(?:\.\d+)?(?:Hz|MHz|GHz|kHz)\b',  # Frequencies
        r'\b\d+(?:\.\d+)?(?:V|mV|kV|A|mA|W|kW|MW)\b',  # Electrical
        r'\b\d+(?:\.\d+)?(?:m|cm|mm|km|nm|μm)\b',  # Length
        r'\b\d+(?:\.\d+)?(?:°C|°F|K)\b',  # Temperature
        r'\b\d+(?:\.\d+)?%\b',  # Percentages
        r'\b[A-Z]{2,}(?:-[A-Z]+)*\b',  # Acronyms
    ]

    # Methodological keywords
    METHODOLOGICAL_KEYWORDS = {
        'method', 'approach', 'technique', 'algorithm', 'process', 'procedure',
        'framework', 'model', 'system', 'architecture', 'design', 'implementation',
        'analysis', 'synthesis', 'optimization', 'evaluation', 'validation',
        'training', 'testing', 'inference', 'preprocessing', 'postprocessing',
        'extraction', 'classification', 'detection', 'recognition', 'generation',
        'learning', 'regression', 'clustering', 'segmentation', 'transformation'
    }

    def __init__(self):
        self.slm_engine = None

    async def extract_concepts(
        self, 
        text: str,
        use_slm: bool = True,
        domain_context: Optional[str] = None
    ) -> ConceptExtractionResult:
        """
        Extract concepts from text using hybrid approach.
        
        Args:
            text: Input text to analyze
            use_slm: Whether to use SLM for enhanced extraction
            domain_context: Optional domain hint (e.g., "machine learning", "biotechnology")
        
        Returns:
            ConceptExtractionResult with categorized concepts
        """
        if not text or not text.strip():
            return ConceptExtractionResult(
                success=False,
                concepts=[],
                summary={},
                differentiating_terms=[],
                common_terms=[],
                error_message="No text provided for concept extraction"
            )

        try:
            # Step 1: Deterministic extraction
            deterministic_concepts = self._deterministic_extraction(text)
            
            # Step 2: Technical pattern extraction
            technical_concepts = self._extract_technical_terms(text)
            
            # Step 3: Multi-word phrase extraction
            phrase_concepts = self._extract_phrases(text)
            
            # Step 4: Combine and deduplicate
            all_concepts = self._merge_concepts(
                deterministic_concepts, 
                technical_concepts, 
                phrase_concepts
            )
            
            # Step 5: SLM-assisted enhancement (if available)
            if use_slm:
                all_concepts = await self._enhance_with_slm(
                    all_concepts, 
                    text, 
                    domain_context
                )
            
            # Step 6: Weight and categorize
            weighted_concepts = self._weight_concepts(all_concepts, text)
            
            # Step 7: Separate differentiating vs common
            differentiating = [c.term for c in weighted_concepts 
                             if c.category == ConceptCategory.DIFFERENTIATING]
            common = [c.term for c in weighted_concepts 
                     if c.category == ConceptCategory.COMMON_DOMAIN]
            
            # Build summary
            summary = {}
            for concept in weighted_concepts:
                cat = concept.category.value
                summary[cat] = summary.get(cat, 0) + 1
            
            return ConceptExtractionResult(
                success=True,
                concepts=weighted_concepts,
                summary=summary,
                differentiating_terms=differentiating[:20],  # Top 20
                common_terms=common[:20]
            )

        except Exception as e:
            return ConceptExtractionResult(
                success=False,
                concepts=[],
                summary={},
                differentiating_terms=[],
                common_terms=[],
                error_message=f"Concept extraction failed: {str(e)}"
            )

    def _deterministic_extraction(self, text: str) -> List[Dict]:
        """Extract keywords using deterministic methods."""
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]\b|\b[a-zA-Z]\b', text.lower())
        
        # Filter stopwords and short words
        filtered = [w for w in words if w not in self.STOPWORDS and len(w) > 2]
        
        # Count frequency
        freq = Counter(filtered)
        
        concepts = []
        for term, count in freq.most_common(100):
            category = ConceptCategory.COMMON_DOMAIN
            if term in self.METHODOLOGICAL_KEYWORDS:
                category = ConceptCategory.METHODOLOGICAL
            
            concepts.append({
                'term': term,
                'frequency': count,
                'category': category,
                'source': 'deterministic'
            })
        
        return concepts

    def _extract_technical_terms(self, text: str) -> List[Dict]:
        """Extract technical terms using patterns."""
        concepts = []
        
        for pattern in self.TECHNICAL_PATTERNS:
            matches = re.findall(pattern, text)
            for match in set(matches):
                concepts.append({
                    'term': match,
                    'frequency': text.count(match),
                    'category': ConceptCategory.TECHNICAL,
                    'source': 'pattern'
                })
        
        return concepts

    def _extract_phrases(self, text: str) -> List[Dict]:
        """Extract multi-word phrases (bigrams and trigrams)."""
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]\b', text.lower())
        
        # Generate bigrams
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in self.STOPWORDS and words[i+1] not in self.STOPWORDS:
                bigrams.append(f"{words[i]} {words[i+1]}")
        
        # Generate trigrams
        trigrams = []
        for i in range(len(words) - 2):
            if words[i] not in self.STOPWORDS and words[i+2] not in self.STOPWORDS:
                trigrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Count and filter
        bigram_freq = Counter(bigrams)
        trigram_freq = Counter(trigrams)
        
        concepts = []
        
        for phrase, count in bigram_freq.most_common(30):
            if count >= 2:  # Appearing at least twice
                concepts.append({
                    'term': phrase,
                    'frequency': count,
                    'category': ConceptCategory.COMMON_DOMAIN,
                    'source': 'phrase'
                })
        
        for phrase, count in trigram_freq.most_common(20):
            if count >= 2:
                concepts.append({
                    'term': phrase,
                    'frequency': count,
                    'category': ConceptCategory.COMMON_DOMAIN,
                    'source': 'phrase'
                })
        
        return concepts

    def _merge_concepts(self, *concept_lists) -> List[Dict]:
        """Merge concept lists, removing duplicates."""
        seen = set()
        merged = []
        
        for concepts in concept_lists:
            for concept in concepts:
                term_lower = concept['term'].lower()
                if term_lower not in seen:
                    seen.add(term_lower)
                    merged.append(concept)
        
        return merged

    async def _enhance_with_slm(
        self, 
        concepts: List[Dict], 
        text: str,
        domain_context: Optional[str]
    ) -> List[Dict]:
        """Enhance concept extraction with SLM analysis."""
        try:
            from app.services.slm_engine import SLMEngine, SLMRequest
            
            engine = SLMEngine()
            
            # Get top terms for SLM analysis
            top_terms = [c['term'] for c in sorted(
                concepts, 
                key=lambda x: x['frequency'], 
                reverse=True
            )[:30]]
            
            prompt = f"""Analyze these extracted terms from a {'patent claim' if domain_context == 'patent' else 'research document'}:

Terms: {', '.join(top_terms)}

Text excerpt (first 1000 chars):
{text[:1000]}

Respond in JSON:
{{
    "differentiating_terms": ["term1", "term2"],  // Terms that appear novel or unique
    "common_domain_terms": ["term3", "term4"],     // Standard domain vocabulary
    "methodological_terms": ["term5", "term6"],    // Methods and approaches
    "additional_concepts": ["concept1", "concept2"] // Important concepts missed
}}

Be conservative - only mark terms as differentiating if they represent genuinely novel combinations."""

            result = await engine.generate(SLMRequest(
                prompt=prompt,
                system_prompt="You are ANTIGRAVITY, an evidence-locked concept analysis system. Be precise and conservative.",
                response_format="json"
            ))

            if result.success and result.parsed_json:
                parsed = result.parsed_json
                
                # Update categories based on SLM analysis
                diff_terms = set(t.lower() for t in parsed.get("differentiating_terms", []))
                method_terms = set(t.lower() for t in parsed.get("methodological_terms", []))
                
                for concept in concepts:
                    term_lower = concept['term'].lower()
                    if term_lower in diff_terms:
                        concept['category'] = ConceptCategory.DIFFERENTIATING
                    elif term_lower in method_terms:
                        concept['category'] = ConceptCategory.METHODOLOGICAL
                
                # Add any additional concepts found by SLM
                for new_term in parsed.get("additional_concepts", []):
                    if new_term.lower() not in {c['term'].lower() for c in concepts}:
                        concepts.append({
                            'term': new_term,
                            'frequency': 1,
                            'category': ConceptCategory.DIFFERENTIATING,
                            'source': 'slm'
                        })

        except Exception as e:
            # SLM enhancement failed, continue with deterministic results
            pass
        
        return concepts

    def _weight_concepts(self, concepts: List[Dict], text: str) -> List[ExtractedConcept]:
        """Weight concepts by relevance and frequency."""
        total_words = len(text.split())
        max_freq = max(c['frequency'] for c in concepts) if concepts else 1
        
        weighted = []
        for concept in concepts:
            # Normalize frequency
            freq_score = concept['frequency'] / max_freq
            
            # Boost technical and differentiating terms
            category = concept.get('category', ConceptCategory.COMMON_DOMAIN)
            if isinstance(category, str):
                category = ConceptCategory(category)
            
            category_boost = {
                ConceptCategory.DIFFERENTIATING: 1.5,
                ConceptCategory.TECHNICAL: 1.3,
                ConceptCategory.METHODOLOGICAL: 1.2,
                ConceptCategory.COMMON_DOMAIN: 1.0
            }.get(category, 1.0)
            
            # Length bonus (multi-word phrases are often more specific)
            length_bonus = 1.0 + (0.1 * len(concept['term'].split()) - 1)
            
            weight = min(1.0, freq_score * category_boost * length_bonus)
            
            # Find context (sentence containing the term)
            context = None
            pattern = re.compile(
                rf'[^.]*\b{re.escape(concept["term"])}\b[^.]*\.',
                re.IGNORECASE
            )
            match = pattern.search(text)
            if match:
                context = match.group(0).strip()[:200]
            
            weighted.append(ExtractedConcept(
                term=concept['term'],
                category=category,
                frequency=concept['frequency'],
                weight=round(weight, 3),
                context=context
            ))
        
        # Sort by weight
        weighted.sort(key=lambda x: x.weight, reverse=True)
        
        return weighted[:50]  # Return top 50
