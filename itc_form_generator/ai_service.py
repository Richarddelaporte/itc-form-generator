"""AI Service for ITC Form Generator — Multi-Backend Support.

Provides intelligent document parsing, check item generation, and form review
using multiple AI backends: MetaGen (Meta internal), OpenAI, Anthropic, or local Ollama.
"""

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class AIBackend(Enum):
    """Available AI backends."""
    METAGEN = "metagen"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    NONE = "none"


@dataclass
class AIConfig:
    """Configuration for AI service."""
    backend: str = AIBackend.METAGEN.value
    model: str = ""  # Auto-selected per backend if empty
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 120
    enabled: bool = True
    fallback_on_error: bool = True
    # API keys (from env vars if not set)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    DEFAULT_MODELS = {
        AIBackend.METAGEN.value: "meta-llama/Llama-3.3-70B-Instruct",
        AIBackend.OPENAI.value: "gpt-4o",
        AIBackend.ANTHROPIC.value: "claude-sonnet-4-20250514",
        AIBackend.OLLAMA.value: "llama3.1:8b",
    }

    def get_model(self) -> str:
        """Get model name, using default for backend if not set."""
        return self.model or self.DEFAULT_MODELS.get(self.backend, "")

    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create config from environment variables."""
        backend = os.environ.get("ITC_AI_BACKEND", AIBackend.METAGEN.value)
        return cls(
            backend=backend,
            model=os.environ.get("ITC_AI_MODEL", ""),
            temperature=float(os.environ.get("ITC_AI_TEMPERATURE", "0.1")),
            max_tokens=int(os.environ.get("ITC_AI_MAX_TOKENS", "4000")),
            timeout=int(os.environ.get("ITC_AI_TIMEOUT", "120")),
            enabled=os.environ.get("ITC_AI_ENABLED", "true").lower() == "true",
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )


# ============================================================================
# Backend Abstraction Layer
# ============================================================================

class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the backend. Returns True if successful."""
        ...

    @abstractmethod
    def call(self, prompt: str, temperature: float = 0.1,
             max_tokens: int = 4000, json_mode: bool = False) -> Optional[str]:
        """Call the LLM with the given prompt. Returns response text or None."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend display name."""
        ...


class MetaGenBackend(LLMBackend):
    """MetaGen (Meta internal) backend."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._platform = None

    @property
    def name(self) -> str:
        return "MetaGen"

    def initialize(self) -> bool:
        try:
            from metagen import MetaGenPlatform
            self._platform = MetaGenPlatform()
            logger.info(f"MetaGen initialized with model: {self.config.get_model()}")
            return True
        except ImportError:
            logger.warning("MetaGen not installed. Run: pip install metagen")
            return False
        except Exception as e:
            logger.error(f"MetaGen init failed: {e}")
            return False

    def call(self, prompt: str, temperature: float = 0.1,
             max_tokens: int = 4000, json_mode: bool = False) -> Optional[str]:
        if not self._platform:
            return None
        try:
            response = self._platform.chat_completion(
                model_name=self.config.get_model(),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"MetaGen call failed: {e}")
            return None


class OpenAIBackend(LLMBackend):
    """OpenAI API backend."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._client = None

    @property
    def name(self) -> str:
        return "OpenAI"

    def initialize(self) -> bool:
        try:
            from openai import OpenAI
            api_key = self.config.openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not set. Set OPENAI_API_KEY env var.")
                return False
            self._client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI initialized with model: {self.config.get_model()}")
            return True
        except ImportError:
            logger.warning("openai package not installed. Run: pip install openai")
            return False
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
            return False

    def call(self, prompt: str, temperature: float = 0.1,
             max_tokens: int = 4000, json_mode: bool = False) -> Optional[str]:
        if not self._client:
            return None
        try:
            kwargs = {
                "model": self.config.get_model(),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return None


class AnthropicBackend(LLMBackend):
    """Anthropic API backend."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._client = None

    @property
    def name(self) -> str:
        return "Anthropic"

    def initialize(self) -> bool:
        try:
            import anthropic
            api_key = self.config.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("Anthropic API key not set. Set ANTHROPIC_API_KEY env var.")
                return False
            self._client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"Anthropic initialized with model: {self.config.get_model()}")
            return True
        except ImportError:
            logger.warning("anthropic package not installed. Run: pip install anthropic")
            return False
        except Exception as e:
            logger.error(f"Anthropic init failed: {e}")
            return False

    def call(self, prompt: str, temperature: float = 0.1,
             max_tokens: int = 4000, json_mode: bool = False) -> Optional[str]:
        if not self._client:
            return None
        try:
            response = self._client.messages.create(
                model=self.config.get_model(),
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            return None


class OllamaBackend(LLMBackend):
    """Ollama (local) backend."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._base_url = config.ollama_base_url

    @property
    def name(self) -> str:
        return "Ollama"

    def initialize(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._base_url}/api/tags")
            urllib.request.urlopen(req, timeout=5)
            logger.info(f"Ollama connected at {self._base_url}")
            return True
        except Exception as e:
            logger.warning(f"Ollama not available at {self._base_url}: {e}")
            return False

    def call(self, prompt: str, temperature: float = 0.1,
             max_tokens: int = 4000, json_mode: bool = False) -> Optional[str]:
        try:
            import urllib.request
            data = json.dumps({
                "model": self.config.get_model(),
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
                **({"format": "json"} if json_mode else {})
            }).encode()
            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(resp.read())
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return None


# ============================================================================
# Backend Factory
# ============================================================================

BACKEND_REGISTRY = {
    AIBackend.METAGEN.value: MetaGenBackend,
    AIBackend.OPENAI.value: OpenAIBackend,
    AIBackend.ANTHROPIC.value: AnthropicBackend,
    AIBackend.OLLAMA.value: OllamaBackend,
}

# Fallback order when primary backend fails
FALLBACK_ORDER = [
    AIBackend.METAGEN.value,
    AIBackend.OPENAI.value,
    AIBackend.ANTHROPIC.value,
    AIBackend.OLLAMA.value,
]


def create_backend(config: AIConfig) -> Optional[LLMBackend]:
    """Create and initialize the configured backend, with fallback."""
    # Try primary backend
    backend_cls = BACKEND_REGISTRY.get(config.backend)
    if backend_cls:
        backend = backend_cls(config)
        if backend.initialize():
            return backend
        logger.warning(f"Primary backend '{config.backend}' failed to initialize")

    # Try fallbacks if enabled
    if config.fallback_on_error:
        for fallback_name in FALLBACK_ORDER:
            if fallback_name == config.backend:
                continue
            fallback_cls = BACKEND_REGISTRY.get(fallback_name)
            if fallback_cls:
                fallback = fallback_cls(config)
                if fallback.initialize():
                    logger.info(f"Using fallback backend: {fallback_name}")
                    return fallback

    return None


# ============================================================================
# JSON Extraction Utilities
# ============================================================================

def extract_json(text: str) -> Optional[Any]:
    """Extract JSON from LLM response text.

    Handles markdown code blocks, surrounding text, and common LLM quirks.
    """
    if not text:
        return None

    # Clean markdown code blocks
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass

    # Try to find JSON array
    try:
        start = text.find('[')
        end = text.rfind(']') + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass

    # Try fixing common JSON issues (trailing commas, single quotes)
    try:
        fixed = re.sub(r',\s*([}\]])', r'\1', text)
        fixed = fixed.replace("'", '"')
        return json.loads(fixed)
    except (json.JSONDecodeError, Exception):
        pass

    logger.warning(f"Failed to extract JSON from response: {text[:200]}...")
    return None


# ============================================================================
# Prompt Templates
# ============================================================================

class PromptTemplates:
    """Structured prompt templates for each parsing task."""

    @staticmethod
    def document_structure(content: str) -> str:
        """Prompt to identify document structure and sections."""
        return f"""Analyze this HVAC/BMS Sequence of Operation (SOO) document and identify its structure.

Return ONLY valid JSON with this structure:
{{
    "title": "document title",
    "project": "project name if found",
    "document_type": "CRAH|IWM|MUA|FCU|AHU|ATS|RSB|generic",
    "sections": [
        {{
            "heading": "section heading text",
            "level": 1,
            "section_type": "system|components|operating_mode|setpoints|interlocks|alarms|general|schedule|network|other",
            "line_start": 0,
            "line_end": 50,
            "equipment_tags": ["AHU-01", "CT-1"]
        }}
    ],
    "equipment_summary": [
        {{
            "tag": "equipment tag",
            "name": "equipment name",
            "type": "CRAH|IWM|MUA|FCU|AHU|ATS|RSB|pump|fan|valve|sensor|other"
        }}
    ]
}}

Document:
{content[:8000]}"""

    @staticmethod
    def extract_systems(section_content: str, doc_context: str = "") -> str:
        """Prompt to extract systems from a document section."""
        return f"""Extract all HVAC/BMS systems and equipment from this section of an SOO document.

{f"Document context: {doc_context}" if doc_context else ""}

Return ONLY valid JSON:
{{
    "systems": [
        {{
            "name": "full system name",
            "tag": "equipment tag (e.g., AHU-01, CRAH-01A)",
            "description": "brief description of the system",
            "system_type": "CRAH|IWM|MUA|FCU|AHU|ATS|RSB|pump|fan|chiller|cooling_tower|other",
            "components": [
                {{
                    "tag": "component tag",
                    "name": "component name",
                    "type": "sensor|actuator|controller|damper|valve|fan|pump|vfd|filter|coil|other"
                }}
            ]
        }}
    ]
}}

Look for:
- Equipment tags (patterns like XX-NNN, XXX-NNA, XXXX-NN)
- Named systems (Air Handling Unit, Chiller, Cooling Tower, etc.)
- Components within systems (sensors, actuators, valves, dampers, VFDs)

Section content:
{section_content[:6000]}"""

    @staticmethod
    def extract_operating_modes(section_content: str, system_name: str = "") -> str:
        """Prompt to extract operating modes and sequences."""
        return f"""Extract all operating modes and control sequences from this SOO section.

{f"System: {system_name}" if system_name else ""}

Return ONLY valid JSON:
{{
    "operating_modes": [
        {{
            "name": "mode name (e.g., Normal Cooling, Standby, Emergency Shutdown)",
            "description": "brief description of the mode",
            "conditions": ["condition that triggers this mode"],
            "actions": ["specific action or control sequence step"],
            "setpoints_referenced": ["any setpoint names mentioned"]
        }}
    ]
}}

Look for:
- Named modes (Normal Operation, Standby, Occupied/Unoccupied, Cooling/Heating, etc.)
- Sequence steps (numbered or bulleted lists of control actions)
- Conditional logic (if/when/upon conditions)
- PID loops and control strategies
- Lead/lag, staging, changeover sequences

Section content:
{section_content[:6000]}"""

    @staticmethod
    def extract_setpoints(section_content: str, system_name: str = "") -> str:
        """Prompt to extract setpoints and parameters."""
        return f"""Extract all setpoints, parameters, and thresholds from this SOO section.

{f"System: {system_name}" if system_name else ""}

Return ONLY valid JSON:
{{
    "setpoints": [
        {{
            "name": "setpoint name",
            "value": "numeric value as string",
            "units": "units (°F, °C, %, CFM, GPM, psi, kPa, Hz, V, A, kW, seconds, minutes)",
            "description": "what this setpoint controls",
            "adjustable": true,
            "min_value": "minimum if specified",
            "max_value": "maximum if specified",
            "related_tag": "equipment tag this applies to"
        }}
    ]
}}

Look for:
- Temperature setpoints (supply air, return air, chilled water, etc.)
- Pressure setpoints (static pressure, differential pressure)
- Flow setpoints (CFM, GPM)
- Speed/frequency setpoints (Hz, %)
- Time delays and timers (seconds, minutes)
- Alarm thresholds (high/low limits)
- PID tuning parameters

Section content:
{section_content[:6000]}"""

    @staticmethod  
    def extract_interlocks_alarms(section_content: str, system_name: str = "") -> str:
        """Prompt to extract interlocks and alarms."""
        return f"""Extract all safety interlocks, alarms, and protection mechanisms from this SOO section.

{f"System: {system_name}" if system_name else ""}

Return ONLY valid JSON:
{{
    "interlocks": [
        {{
            "description": "interlock description",
            "trigger_condition": "what triggers this interlock",
            "action": "what happens when triggered",
            "priority": "CRITICAL|HIGH|MEDIUM|LOW"
        }}
    ],
    "alarms": [
        {{
            "description": "alarm description",
            "trigger_condition": "alarm threshold or condition",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "action_required": "operator action needed"
        }}
    ]
}}

Section content:
{section_content[:6000]}"""

    @staticmethod
    def identify_points_columns(header_rows: str) -> str:
        """Prompt to identify column mapping in a points list."""
        return f"""Analyze these header rows from a BMS/Controls points list spreadsheet.
Map each column index to its semantic meaning.

Return ONLY valid JSON:
{{
    "column_mapping": {{
        "point_name": <column_index or null>,
        "tag": <column_index or null>,
        "point_type": <column_index or null>,
        "description": <column_index or null>,
        "units": <column_index or null>,
        "range_min": <column_index or null>,
        "range_max": <column_index or null>,
        "design_value": <column_index or null>,
        "alarms": <column_index or null>,
        "system": <column_index or null>,
        "equipment": <column_index or null>,
        "area": <column_index or null>,
        "process_area": <column_index or null>,
        "end_device": <column_index or null>,
        "software_function": <column_index or null>
    }},
    "header_row_count": <number of header rows to skip>,
    "format_type": "standard|gtn|custom"
}}

Column indices are 0-based. Set to null if not found.

Header rows:
{header_rows}"""

    @staticmethod
    def classify_point_type(point_name: str, description: str) -> str:
        """Prompt to classify a point's I/O type."""
        return f"""Classify this BMS control point type.

Point name: {point_name}
Description: {description}

Return ONLY one of: AI, AO, DI, DO, AV, BV, IAV, IBV, UNKNOWN

Rules:
- AI (Analog Input): temperature sensors, pressure transducers, flow meters, humidity sensors
- AO (Analog Output): VFD speed commands, valve position commands, damper position commands
- DI (Digital Input): status signals, switches, alarms, proof of flow/pressure
- DO (Digital Output): start/stop commands, enable/disable, on/off
- AV (Analog Value): setpoints, calculated values, PID outputs
- BV (Binary Value): mode selections, enable flags, schedule values
"""


# ============================================================================
# Confidence Scoring
# ============================================================================

@dataclass

    @staticmethod
    def comprehensive_extraction(content: str) -> str:
        """Single comprehensive prompt that extracts everything at once.
        
        This prompt was validated to extract:
        - 26 components (vs 9 regex) from MUA docs
        - 20 setpoints (vs 12 regex) from MUA docs  
        - 12 modes (vs 7 regex) from MUA docs
        - 8 interlocks (vs 4 regex) from MUA docs
        - 9 alarms (vs 2 regex) from MUA docs
        """
        return f"""You are an expert BMS/HVAC engineer parsing a Sequence of Operations (SOO) document.

Extract ALL of the following from this document and return as valid JSON:

1. **systems**: Each major system described (name, type, description)
2. **components**: ALL equipment/components mentioned (name, type, parent_system)
3. **setpoints**: ALL setpoints/parameters with their values and units. Look for:
   - Tables with PARAMETER/SET POINT/TIME DELAY columns
   - Inline values like "maintain temperature above 50°F"  
   - Any numeric thresholds, delays, or limits mentioned
4. **operating_modes**: All modes of operation (name, description, conditions)
5. **interlocks**: Safety interlocks and conditions
6. **alarms**: Alarm conditions and thresholds

Return ONLY valid JSON in this exact format:
{{{{
  "document_type": "CRAH|IWM|MUA|FCU|AHU|ATS|RSB|generic",
  "title": "document title",
  "systems": [{{{{"name": "...", "type": "...", "description": "..."}}}}],
  "components": [{{{{"name": "...", "type": "...", "parent_system": "..."}}}}],
  "setpoints": [{{{{"name": "...", "value": "...", "units": "...", "time_delay": "...", "context": "..."}}}}],
  "operating_modes": [{{{{"name": "...", "description": "...", "conditions": "..."}}}}],
  "interlocks": [{{{{"name": "...", "condition": "...", "action": "..."}}}}],
  "alarms": [{{{{"name": "...", "condition": "...", "threshold": "..."}}}}]
}}}}

Be thorough. Extract every component, every setpoint value, every mode of operation.
Do not skip tables, inline values, or prose descriptions.

=== DOCUMENT ===
{{content}}
=== END DOCUMENT ===

Return valid JSON only."""


class ParseResult:
    """A parsed result with confidence scoring."""
    data: Any
    confidence: float = 0.0  # 0.0 to 1.0
    source: str = "unknown"  # "ai", "regex", "hybrid"
    warnings: list[str] = field(default_factory=list)

    @property
    def is_reliable(self) -> bool:
        return self.confidence >= 0.6


def score_extraction(result: dict, content: str) -> float:
    """Score the quality of an extraction result against the source content.

    Returns confidence score 0.0-1.0.
    """
    if not result:
        return 0.0

    score = 0.5  # Base score for any valid result

    # Check if systems were found
    systems = result.get("systems", [])
    if systems:
        score += 0.1
        # Check if system tags match patterns found in content
        content_tags = set(re.findall(r'\b([A-Z]{2,5}[-_]?\d{1,4}[A-Z]?)\b', content))
        result_tags = set()
        for sys in systems:
            if sys.get("tag"):
                result_tags.add(sys["tag"])
            for comp in sys.get("components", []):
                if comp.get("tag"):
                    result_tags.add(comp["tag"])

        if content_tags and result_tags:
            overlap = len(content_tags & result_tags) / max(len(content_tags), 1)
            score += overlap * 0.2

    # Check if setpoints have values
    for sys in systems:
        setpoints = sys.get("setpoints", [])
        if setpoints:
            has_values = sum(1 for sp in setpoints if sp.get("value"))
            score += min(has_values / max(len(setpoints), 1) * 0.1, 0.1)

    # Check if operating modes were found
    for sys in systems:
        modes = sys.get("operating_modes", [])
        if modes:
            score += 0.1
            break

    return min(score, 1.0)


# ============================================================================
# Main AI Service
# ============================================================================

class AIService:
    """AI service with multi-backend support for intelligent form generation.

    Supports MetaGen (Meta internal), OpenAI, Anthropic, and Ollama backends.
    Automatically falls back to available backends if primary fails.

    Usage:
        # Auto-detect backend from environment
        ai = AIService()

        # Explicit backend
        ai = AIService(AIConfig(backend="openai"))

        # Parse SOO document  
        result = ai.parse_soo_document(soo_content)
    """

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig.from_env()
        self._backend: Optional[LLMBackend] = None
        self._initialized = False
        self._init_error: Optional[str] = None

    def _initialize(self) -> bool:
        """Lazy initialization of AI backend."""
        if self._initialized:
            return self._backend is not None

        self._initialized = True
        self._backend = create_backend(self.config)

        if self._backend:
            logger.info(f"AI service initialized with {self._backend.name} backend")
        else:
            self._init_error = "No AI backend available"
            logger.warning(self._init_error)

        return self._backend is not None

    @property
    def is_available(self) -> bool:
        return self._initialize() and self.config.enabled

    @property
    def backend_name(self) -> str:
        if self._backend:
            return self._backend.name
        return "None"

    @property
    def initialization_error(self) -> Optional[str]:
        self._initialize()
        return self._init_error

    def _call_llm(self, prompt: str, temperature: Optional[float] = None,
                  max_tokens: Optional[int] = None, json_mode: bool = False) -> Optional[str]:
        """Call the LLM with the given prompt."""
        if not self._initialize():
            return None
        return self._backend.call(
            prompt,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            json_mode=json_mode
        )

    def _call_and_parse_json(self, prompt: str, temperature: float = 0.1,
                              max_tokens: int = 4000) -> Optional[Any]:
        """Call LLM and extract JSON from response."""
        response = self._call_llm(prompt, temperature, max_tokens, json_mode=True)
        return extract_json(response)

    # ========================================================================
    # Document Structure Analysis
    # ========================================================================

    def analyze_document_structure(self, content: str) -> Optional[dict]:
        """Analyze document structure to identify sections and equipment.

        First pass of multi-pass parsing — identifies the document layout
        so subsequent passes can target specific sections.
        """
        prompt = PromptTemplates.document_structure(content)
        return self._call_and_parse_json(prompt, max_tokens=3000)

    # ========================================================================
    # SOO Document Parsing (Multi-Pass)
    # ========================================================================

    def parse_soo_document(self, content: str) -> Optional[dict]:
        """Parse SOO document using multi-pass AI extraction.

        Pass 1: Analyze document structure
        Pass 2: Extract systems and components per section
        Pass 3: Extract modes, setpoints, interlocks per system

        Returns structured dict compatible with existing parser interface.
        """
        # Use comprehensive single-pass extraction (proven most effective)
        # Falls back to multi-pass only if single-pass fails
        try:
            result = self._parse_soo_comprehensive(content)
            if result and result.get('systems'):
                return result
        except Exception as e:
            logger.warning(f"Comprehensive parse failed: {e}, trying multi-pass")
        
        # Fallback: multi-pass for very long documents or if comprehensive fails
        if len(content) > 15000:
            return self._parse_soo_multi_pass(content)
        return self._parse_soo_single_pass(content)


    def _parse_soo_comprehensive(self, content: str) -> Optional[dict]:
        """Parse SOO using the proven comprehensive extraction prompt.
        
        Single LLM call that extracts systems, components, setpoints, modes,
        interlocks, and alarms all at once. Validated to significantly outperform
        regex and multi-pass approaches.
        """
        import json as _json
        
        prompt = PromptTemplates.comprehensive_extraction(content)
        response = self._call_backend(prompt)
        
        if not response:
            return None
        
        # Parse JSON from response (handle markdown code fences)
        text = response.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
        text = text.strip()
        
        try:
            data = _json.loads(text)
        except _json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]+\}', text)
            if json_match:
                try:
                    data = _json.loads(json_match.group())
                except _json.JSONDecodeError:
                    logger.error("Failed to parse AI response as JSON")
                    return None
            else:
                return None
        
        # Restructure flat AI output to nested format expected by parser
        # AI returns: {systems: [...], components: [...], setpoints: [...], ...}
        # Parser expects: {systems: [{..., components: [...], setpoints: [...]}]}
        if 'systems' in data and isinstance(data.get('components'), list):
            # Flat format detected — restructure to nested
            systems_by_name = {}
            for sys in data.get('systems', []):
                sys_name = sys.get('name', 'Unknown')
                sys.setdefault('components', [])
                sys.setdefault('setpoints', [])
                sys.setdefault('operating_modes', [])
                sys.setdefault('interlocks', [])
                sys.setdefault('alarms', [])
                sys.setdefault('tag', '')
                systems_by_name[sys_name.lower()] = sys
            
            # Helper: find best matching system for an item
            def find_system(item, field='parent_system'):
                parent = (item.get(field) or item.get('context') or '').lower()
                if parent:
                    # Exact match
                    if parent in systems_by_name:
                        return systems_by_name[parent]
                    # Partial match
                    for sys_name, sys in systems_by_name.items():
                        if parent in sys_name or sys_name in parent:
                            return sys
                # Default to first system
                if systems_by_name:
                    return next(iter(systems_by_name.values()))
                return None
            
            # Distribute components into systems
            for comp in data.get('components', []):
                sys = find_system(comp)
                if sys:
                    sys['components'].append(comp)
            
            # Distribute setpoints into systems
            for sp in data.get('setpoints', []):
                sys = find_system(sp)
                if sys:
                    sys['setpoints'].append(sp)
            
            # Distribute operating_modes into systems
            for mode in data.get('operating_modes', []):
                sys = find_system(mode)
                if sys:
                    sys['operating_modes'].append(mode)
            
            # Distribute interlocks into systems
            for intlk in data.get('interlocks', []):
                sys = find_system(intlk)
                if sys:
                    sys['interlocks'].append(intlk)
            
            # Distribute alarms into systems
            for alarm in data.get('alarms', []):
                sys = find_system(alarm)
                if sys:
                    sys['alarms'].append(alarm)
            
            # Clean up: remove top-level flat lists
            data.pop('components', None)
            data.pop('setpoints', None)
            data.pop('operating_modes', None)
            data.pop('interlocks', None)
            data.pop('alarms', None)
            
            logger.info(f"AI comprehensive: restructured {len(systems_by_name)} systems")
        
        return data
    
    def _call_backend(self, prompt: str) -> Optional[str]:
        """Call the configured AI backend with a prompt."""
        if not self.backend:
            if not self.initialize():
                return None
        
        try:
            return self.backend.call(prompt)
        except Exception as e:
            logger.error(f"AI backend call failed: {e}")
            return None

    def _parse_soo_single_pass(self, content: str) -> Optional[dict]:
        """Single-pass parsing for short documents."""
        prompt = f"""Analyze this Sequence of Operation (SOO) document for HVAC/BMS systems and extract structured data.

Return ONLY valid JSON with this structure:
{{
    "title": "document title",
    "project": "project name if found",
    "systems": [
        {{
            "name": "system name",
            "tag": "equipment tag (e.g., AHU-01)",
            "description": "brief system description",
            "components": [{{"tag": "tag", "name": "name", "type": "sensor|actuator|controller|damper|valve|fan|pump|vfd|other"}}],
            "operating_modes": [{{"name": "mode name", "description": "", "conditions": [], "actions": []}}],
            "setpoints": [{{"name": "name", "value": "numeric", "units": "units", "adjustable": true, "min_value": null, "max_value": null}}],
            "interlocks": ["interlock description"],
            "alarms": ["alarm description"]
        }}
    ],
    "general_requirements": []
}}

SOO Document:
{content}"""
        return self._call_and_parse_json(prompt, max_tokens=4000)

    def _parse_soo_multi_pass(self, content: str) -> Optional[dict]:
        """Multi-pass parsing for longer documents."""
        lines = content.split('\n')

        # Pass 1: Document structure
        structure = self.analyze_document_structure(content)

        result = {
            "title": "",
            "project": "",
            "systems": [],
            "general_requirements": []
        }

        if structure:
            result["title"] = structure.get("title", "")
            result["project"] = structure.get("project", "")

            # Use structure to guide extraction
            sections = structure.get("sections", [])
            equipment = structure.get("equipment_summary", [])

            # Pass 2: Extract systems from identified sections
            system_sections = [s for s in sections if s.get("section_type") in ("system", "components")]
            if system_sections:
                for sec in system_sections:
                    start = sec.get("line_start", 0)
                    end = sec.get("line_end", len(lines))
                    section_content = '\n'.join(lines[start:min(end + 1, len(lines))])

                    sys_data = self._call_and_parse_json(
                        PromptTemplates.extract_systems(section_content, result["title"]),
                        max_tokens=3000
                    )
                    if sys_data and "systems" in sys_data:
                        result["systems"].extend(sys_data["systems"])

            # If no systems from sections, try equipment summary
            if not result["systems"] and equipment:
                for equip in equipment:
                    result["systems"].append({
                        "name": equip.get("name", ""),
                        "tag": equip.get("tag", ""),
                        "description": "",
                        "components": [],
                        "operating_modes": [],
                        "setpoints": [],
                        "interlocks": [],
                        "alarms": []
                    })

            # Pass 3: Extract modes, setpoints, interlocks for each system
            for system in result["systems"]:
                sys_name = system.get("name", "")
                sys_tag = system.get("tag", "")

                # Find relevant sections for this system
                relevant_sections = []
                for sec in sections:
                    sec_tags = sec.get("equipment_tags", [])
                    if sys_tag and sys_tag in sec_tags:
                        relevant_sections.append(sec)
                    elif sec.get("section_type") in ("operating_mode", "setpoints", "interlocks", "alarms"):
                        relevant_sections.append(sec)

                if relevant_sections:
                    combined_content = ""
                    for sec in relevant_sections:
                        start = sec.get("line_start", 0)
                        end = sec.get("line_end", len(lines))
                        combined_content += '\n'.join(lines[start:min(end + 1, len(lines))]) + '\n\n'
                else:
                    # Use full document if no specific sections found
                    combined_content = content[:6000]

                # Extract operating modes
                if not system.get("operating_modes"):
                    modes_data = self._call_and_parse_json(
                        PromptTemplates.extract_operating_modes(combined_content, sys_name),
                        max_tokens=3000
                    )
                    if modes_data and "operating_modes" in modes_data:
                        system["operating_modes"] = modes_data["operating_modes"]

                # Extract setpoints
                if not system.get("setpoints"):
                    sp_data = self._call_and_parse_json(
                        PromptTemplates.extract_setpoints(combined_content, sys_name),
                        max_tokens=2000
                    )
                    if sp_data and "setpoints" in sp_data:
                        system["setpoints"] = sp_data["setpoints"]

                # Extract interlocks and alarms
                if not system.get("interlocks") and not system.get("alarms"):
                    ia_data = self._call_and_parse_json(
                        PromptTemplates.extract_interlocks_alarms(combined_content, sys_name),
                        max_tokens=2000
                    )
                    if ia_data:
                        if "interlocks" in ia_data:
                            system["interlocks"] = [
                                i.get("description", str(i)) for i in ia_data["interlocks"]
                            ]
                        if "alarms" in ia_data:
                            system["alarms"] = [
                                a.get("description", str(a)) for a in ia_data["alarms"]
                            ]

        # Fallback: if structure analysis failed, try single pass on truncated content
        if not result["systems"]:
            truncated = content[:8000] if len(content) > 8000 else content
            return self._parse_soo_single_pass(truncated)

        return result

    # ========================================================================
    # Points List Parsing Support
    # ========================================================================

    def identify_points_columns(self, header_rows: list[list[str]]) -> Optional[dict]:
        """Use AI to identify column mapping in a points list.

        Args:
            header_rows: First few rows of the spreadsheet as lists of strings

        Returns:
            Dict with column_mapping, header_row_count, format_type
        """
        # Format header rows for the prompt
        header_text = ""
        for i, row in enumerate(header_rows[:5]):
            header_text += f"Row {i}: {' | '.join(str(c) for c in row)}\n"

        prompt = PromptTemplates.identify_points_columns(header_text)
        return self._call_and_parse_json(prompt, max_tokens=1500)

    def classify_point_type(self, point_name: str, description: str) -> str:
        """Use AI to classify a control point type.

        Returns point type string (AI, AO, DI, DO, AV, BV, etc.)
        """
        prompt = PromptTemplates.classify_point_type(point_name, description)
        response = self._call_llm(prompt, temperature=0.0, max_tokens=50)
        if response:
            response = response.strip().upper()
            valid_types = {"AI", "AO", "DI", "DO", "AV", "BV", "IAV", "IBV"}
            if response in valid_types:
                return response
        return "UNKNOWN"

    def cross_reference_points_to_systems(
        self, points_summary: str, systems_summary: str
    ) -> Optional[dict]:
        """Cross-reference points list with SOO systems.

        Returns mapping of point names to system tags.
        """
        prompt = f"""Match these BMS control points to the systems they belong to.

Systems found in SOO:
{systems_summary}

Points to match:
{points_summary}

Return ONLY valid JSON:
{{
    "mappings": [
        {{
            "point_name": "point name",
            "system_tag": "matched system tag",
            "confidence": 0.9
        }}
    ]
}}

Match based on naming conventions, equipment tags, and functional descriptions."""

        return self._call_and_parse_json(prompt, max_tokens=3000)

    # ========================================================================
    # Check Item Generation (backward compatible)
    # ========================================================================

    def generate_check_items(self, system_info: dict, form_type: str) -> Optional[list]:
        """Generate context-aware check items for a system.

        Backward compatible with existing interface.
        """
        feedback_context = self._get_feedback_context(system_info)

        prompt = f"""Generate commissioning check items for this HVAC/BMS system.

System Information:
- Name: {system_info.get('name', 'Unknown')}
- Tag: {system_info.get('tag', 'N/A')}
- Components: {json.dumps(system_info.get('components', [])[:10])}
- Setpoints: {json.dumps(system_info.get('setpoints', [])[:10])}
- Operating Modes: {json.dumps(system_info.get('operating_modes', [])[:5])}
- Interlocks: {json.dumps(system_info.get('interlocks', [])[:5])}

Form Type: {form_type}
{feedback_context}

Return ONLY a JSON array of 10-20 check items:
[
    {{
        "description": "specific check item description",
        "check_type": "VISUAL|MEASUREMENT|FUNCTIONAL|DOCUMENTATION|VERIFICATION",
        "priority": "CRITICAL|HIGH|MEDIUM|LOW",
        "acceptance_criteria": "measurable pass/fail criteria",
        "method": "step-by-step method",
        "expected_value": "expected result"
    }}
]"""

        response = self._call_llm(prompt, temperature=0.2, max_tokens=4000)
        result = extract_json(response)
        return result if isinstance(result, list) else None

    def _get_feedback_context(self, system_info: dict) -> str:
        """Get feedback context for AI prompts."""
        context_parts = []
        system_type = self._extract_system_type(
            system_info.get('name', ''), system_info.get('tag', '')
        )
        try:
            from .feedback_store import get_feedback_store
            store = get_feedback_store()
            ctx = store.generate_ai_context(system_type, system_info.get('name', ''))
            if ctx:
                context_parts.append(ctx)
        except Exception:
            pass
        try:
            from .example_form_parser import get_example_store
            store = get_example_store()
            ctx = store.generate_ai_context(system_type)
            if ctx:
                context_parts.append(ctx)
        except Exception:
            pass
        return "\n".join(context_parts)

    def _extract_system_type(self, name: str, tag: str) -> str:
        """Extract system type from name/tag."""
        name_lower = name.lower()
        tag_upper = tag.upper() if tag else ""

        type_map = {
            'crah': ['crah', 'computer room air'],
            'iwm': ['iwm', 'industrial water', 'facility water'],
            'mua': ['mua', 'makeup air'],
            'fcu': ['fcu', 'fan coil'],
            'ahu': ['ahu', 'air handling'],
            'ats': ['ats', 'automatic transfer'],
            'rsb': ['rsb', 'remote switchboard'],
            'chiller': ['chiller', 'ch-'],
            'cooling_tower': ['cooling tower', 'ct-'],
            'pump': ['pump', 'p-'],
        }

        for sys_type, keywords in type_map.items():
            if any(kw in name_lower or kw in tag_upper.lower() for kw in keywords):
                return sys_type
        return "generic"




