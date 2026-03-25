"""AI Service for ITC Form Generator using MetaGen API.

Provides intelligent document parsing, check item generation, and form review
using Meta's internal Llama models via the MetaGen platform.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Available AI models via MetaGen."""
    LLAMA_3_3_70B = "meta-llama/Llama-3.3-70B-Instruct"
    LLAMA_3_1_70B = "meta-llama/Llama-3.1-70B-Instruct"
    LLAMA_3_1_8B = "meta-llama/Llama-3.1-8B-Instruct"


@dataclass
class AIConfig:
    """Configuration for AI service."""
    model: str = AIModel.LLAMA_3_3_70B.value
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60
    enabled: bool = True
    fallback_on_error: bool = True


class AIService:
    """AI service using MetaGen for intelligent form generation.

    This service provides AI-powered capabilities for:
    - Parsing SOO documents with better accuracy than regex
    - Generating context-aware check items
    - Enhancing acceptance criteria
    - Reviewing form completeness

    Usage:
        ai = AIService()
        result = ai.parse_soo_document(soo_content)
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize AI service with optional configuration.

        Args:
            config: AIConfig object with model settings. Uses defaults if None.
        """
        self.config = config or AIConfig()
        self._platform = None
        self._initialized = False
        self._init_error: Optional[str] = None

    def _initialize(self) -> bool:
        """Lazy initialization of MetaGen platform.

        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return self._platform is not None

        self._initialized = True

        try:
            from metagen import MetaGenPlatform
            self._platform = MetaGenPlatform()
            logger.info(f"MetaGen initialized with model: {self.config.model}")
            return True
        except ImportError as e:
            self._init_error = f"MetaGen not installed: {e}. Run 'pip install metagen'"
            logger.warning(self._init_error)
            return False
        except Exception as e:
            self._init_error = f"Failed to initialize MetaGen: {e}"
            logger.error(self._init_error)
            return False

    @property
    def is_available(self) -> bool:
        """Check if AI service is available and properly configured."""
        return self._initialize() and self.config.enabled

    @property
    def initialization_error(self) -> Optional[str]:
        """Get initialization error message if any."""
        self._initialize()
        return self._init_error

    def _call_llm(self, prompt: str, temperature: Optional[float] = None,
                  max_tokens: Optional[int] = None) -> Optional[str]:
        """Call the LLM with the given prompt.

        Args:
            prompt: The prompt to send to the model
            temperature: Override default temperature (lower = more deterministic)
            max_tokens: Override default max tokens

        Returns:
            Model response text, or None if call failed
        """
        if not self._initialize():
            logger.warning(f"AI service not available: {self._init_error}")
            return None

        try:
            response = self._platform.chat_completion(
                model_name=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[Any]:
        """Extract JSON from LLM response.

        Handles responses that may contain markdown code blocks or
        additional text around the JSON.

        Args:
            text: Raw LLM response text

        Returns:
            Parsed JSON object (dict or list), or None if parsing failed
        """
        if not text:
            return None

        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Try to parse as-is first
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

        logger.warning(f"Failed to extract JSON from response: {text[:200]}...")
        return None

    def parse_soo_document(self, content: str) -> Optional[dict]:
        """Use AI to extract structured data from SOO document.

        This provides better extraction than regex for messy or OCR'd documents.

        Args:
            content: Raw SOO document text

        Returns:
            Structured dict with title, systems, components, setpoints, etc.
            Returns None if AI parsing fails.
        """
        # Truncate content to fit token limits while preserving important sections
        max_content_length = 6000
        if len(content) > max_content_length:
            # Keep beginning and end which often have key info
            half = max_content_length // 2
            content = content[:half] + "\n\n[...content truncated...]\n\n" + content[-half:]

        prompt = f"""Analyze this Sequence of Operation (SOO) document for HVAC/BMS systems and extract structured data.

Return ONLY valid JSON (no explanation) with this structure:
{{
    "title": "document title",
    "project": "project name if found",
    "systems": [
        {{
            "name": "system name (e.g., Air Handling Unit 1)",
            "tag": "equipment tag (e.g., AHU-01, FCU-101)",
            "description": "brief system description",
            "components": [
                {{
                    "tag": "component tag",
                    "name": "component name",
                    "type": "sensor|actuator|controller|damper|valve|fan|pump|other"
                }}
            ],
            "operating_modes": [
                {{
                    "name": "mode name (e.g., Cooling Mode, Occupied, Standby)",
                    "conditions": ["list of conditions that trigger this mode"],
                    "actions": ["list of actions/sequences in this mode"]
                }}
            ],
            "setpoints": [
                {{
                    "name": "setpoint name",
                    "value": "numeric value",
                    "units": "units (°F, %, CFM, etc.)",
                    "adjustable": true or false,
                    "min_value": "minimum if specified",
                    "max_value": "maximum if specified"
                }}
            ],
            "interlocks": ["list of safety interlocks and their conditions"],
            "alarms": ["list of alarm conditions"]
        }}
    ],
    "general_requirements": ["any general requirements found"]
}}

Extract ALL systems, components, setpoints, and operating modes you can find.
For equipment tags, look for patterns like AHU-01, FCU-101, VAV-201, CT-1, etc.

SOO Document:
{content}
"""

        response = self._call_llm(prompt, temperature=0.1, max_tokens=4000)
        return self._extract_json(response)

    def generate_check_items(self, system_info: dict, form_type: str) -> Optional[list]:
        """Generate context-aware check items for a system.

        Creates specific, actionable check items based on the actual
        system configuration rather than generic templates.

        Args:
            system_info: Dict with system name, tag, components, setpoints, modes
            form_type: Type of form (PFI, FPT, IST, CXC, ITC)

        Returns:
            List of check item dicts, or None if generation fails
        """
        # Get feedback context for this system type
        feedback_context = self._get_feedback_context(system_info)

        prompt = f"""Generate commissioning check items for this HVAC/BMS system.

System Information:
- Name: {system_info.get('name', 'Unknown')}
- Tag: {system_info.get('tag', 'N/A')}
- Components: {json.dumps(system_info.get('components', []))}
- Setpoints: {json.dumps(system_info.get('setpoints', []))}
- Operating Modes: {json.dumps(system_info.get('operating_modes', []))}
- Interlocks: {json.dumps(system_info.get('interlocks', []))}

Form Type: {form_type}
- PFI = Pre-Functional Inspection (visual checks, installation verification)
- FPT = Functional Performance Test (operational testing, sequence verification)
- IST = Integrated Systems Test (multi-system coordination)
- CXC = Commissioning Checklist (comprehensive checklist)
- ITC = Combined Inspection, Testing & Commissioning (all-in-one comprehensive form)
{feedback_context}
Return ONLY a JSON array of check items (no explanation):
[
    {{
        "description": "specific, actionable check item description",
        "check_type": "VISUAL|MEASUREMENT|FUNCTIONAL|DOCUMENTATION|VERIFICATION",
        "priority": "CRITICAL|HIGH|MEDIUM|LOW",
        "acceptance_criteria": "specific, measurable pass/fail criteria",
        "method": "step-by-step method to perform the check",
        "expected_value": "expected result or measurement range"
    }}
]

Guidelines:
1. Safety-critical items (interlocks, emergency stops) should be CRITICAL priority
2. Include actual setpoint values from the system info in acceptance criteria
3. Reference specific component tags where applicable
4. For functional tests, describe the specific sequence to verify
5. Make acceptance criteria measurable and specific
6. Generate 10-20 relevant check items based on the form type
"""

        response = self._call_llm(prompt, temperature=0.2, max_tokens=4000)
        result = self._extract_json(response)
        return result if isinstance(result, list) else None

    def _get_feedback_context(self, system_info: dict) -> str:
        """Get feedback context for AI prompts.

        Retrieves learned feedback patterns to improve generation.

        Args:
            system_info: System information dict

        Returns:
            Formatted context string for AI prompts
        """
        context_parts = []

        system_type = self._extract_system_type(
            system_info.get('name', ''),
            system_info.get('tag', '')
        )

        # Get feedback context
        try:
            from .feedback_store import get_feedback_store
            store = get_feedback_store()
            feedback_context = store.generate_ai_context(system_type, system_info.get('name', ''))
            if feedback_context:
                context_parts.append(feedback_context)
        except Exception as e:
            logger.debug(f"Could not load feedback context: {e}")

        # Get learned examples context
        try:
            from .example_form_parser import get_example_store
            example_store = get_example_store()
            examples_context = example_store.generate_ai_context(system_type)
            if examples_context:
                context_parts.append(examples_context)
        except Exception as e:
            logger.debug(f"Could not load examples context: {e}")

        return "\n".join(context_parts)

    def _extract_system_type(self, name: str, tag: str) -> str:
        """Extract system type from name/tag."""
        name_lower = name.lower()
        tag_upper = tag.upper() if tag else ""

        type_keywords = {
            'AHU': ['ahu', 'air handling', 'air handler'],
            'FCU': ['fcu', 'fan coil'],
            'VAV': ['vav', 'variable air volume'],
            'Chiller': ['chiller', 'ch-'],
            'Boiler': ['boiler', 'blr'],
            'Cooling Tower': ['cooling tower', 'ct-'],
            'Pump': ['pump', 'pmp'],
            'CRAH': ['crah', 'computer room'],
            'Data Hall': ['data hall', 'dh-'],
        }

        for sys_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in name_lower or kw.upper() in tag_upper:
                    return sys_type

        if tag_upper:
            return tag_upper.split('-')[0] if '-' in tag_upper else tag_upper[:3]
        return 'General'

    def enhance_check_item(self, description: str, context: str) -> Optional[dict]:
        """Enhance a check item with specific acceptance criteria.

        Takes a generic check item and makes it specific to the system.

        Args:
            description: Original check item description
            context: System context (name, setpoints, etc.)

        Returns:
            Dict with enhanced description, acceptance_criteria, method, expected_value
        """
        prompt = f"""Improve this commissioning check item with specific acceptance criteria.

Original Check Item: {description}

System Context: {context}

Return ONLY JSON (no explanation):
{{
    "enhanced_description": "more specific description referencing actual equipment",
    "acceptance_criteria": "specific, measurable pass/fail criteria with values",
    "method": "detailed step-by-step verification method",
    "expected_value": "specific expected value or acceptable range"
}}

Make the criteria measurable and actionable for a commissioning technician.
"""

        response = self._call_llm(prompt, temperature=0.2, max_tokens=500)
        return self._extract_json(response)

    def match_points_to_system(self, points: list[dict], system_info: dict) -> Optional[dict]:
        """Match BMS points to system components and setpoints.

        Uses AI to intelligently match point names to the appropriate
        system components, even when naming conventions vary.

        Args:
            points: List of BMS points with name, description, etc.
            system_info: System info with components and setpoints

        Returns:
            Dict mapping point names to matched components/setpoints
        """
        # Limit points to avoid token limits
        points_subset = points[:50] if len(points) > 50 else points

        prompt = f"""Match these BMS points to the system components and setpoints.

System: {system_info.get('name')} ({system_info.get('tag')})
Components: {json.dumps(system_info.get('components', []))}
Setpoints: {json.dumps(system_info.get('setpoints', []))}

BMS Points:
{json.dumps(points_subset, indent=2)}

Return ONLY JSON mapping each point to its match:
{{
    "point_name": {{
        "component_tag": "matched component tag or null",
        "component_name": "matched component name or null",
        "setpoint_name": "matched setpoint name or null",
        "point_type": "sensor|command|status|setpoint|alarm",
        "suggested_check": "what check item this point enables",
        "confidence": 0.0 to 1.0
    }}
}}

Only include points with confidence > 0.5.
"""

        response = self._call_llm(prompt, temperature=0.1, max_tokens=4000)
        return self._extract_json(response)

    def review_form_completeness(self, form_summary: dict, soo_summary: dict) -> Optional[dict]:
        """Review generated form for completeness and suggest improvements.

        Compares the generated form against the original SOO to identify
        gaps and suggest additional checks.

        Args:
            form_summary: Summary of generated form (title, sections, item counts)
            soo_summary: Summary of original SOO (systems, setpoints, modes, etc.)

        Returns:
            Review results with score, missing items, and suggestions
        """
        prompt = f"""Review this commissioning form for completeness against the original SOO.

Generated Form Summary:
- Title: {form_summary.get('title')}
- System: {form_summary.get('system')}
- Total Check Items: {form_summary.get('total_items')}
- Sections: {json.dumps(form_summary.get('sections', []))}

Original SOO Summary:
- Systems: {soo_summary.get('system_count', 0)}
- Components: {soo_summary.get('component_count', 0)}
- Setpoints: {soo_summary.get('setpoint_count', 0)}
- Operating Modes: {soo_summary.get('mode_count', 0)}
- Interlocks: {soo_summary.get('interlock_count', 0)}
- Alarms: {soo_summary.get('alarm_count', 0)}

Return ONLY JSON (no explanation):
{{
    "completeness_score": 0 to 100,
    "coverage": {{
        "setpoints_covered": true or false,
        "modes_covered": true or false,
        "interlocks_covered": true or false,
        "components_covered": true or false
    }},
    "missing_items": [
        "specific items that should be checked but aren't"
    ],
    "suggestions": [
        "specific improvements to make the form better"
    ],
    "risk_areas": [
        "safety or operational risks not covered by current checks"
    ],
    "summary": "brief overall assessment"
}}

Focus on safety-critical gaps and missing setpoint verifications.
"""

        response = self._call_llm(prompt, temperature=0.3, max_tokens=1500)
        return self._extract_json(response)

    def suggest_test_procedure(self, system_info: dict, mode_name: str) -> Optional[dict]:
        """Generate a detailed test procedure for an operating mode.

        Creates step-by-step test procedures for verifying system sequences.

        Args:
            system_info: System information dict
            mode_name: Name of the operating mode to test

        Returns:
            Dict with test procedure steps, prerequisites, and expected results
        """
        # Find the mode details
        modes = system_info.get('operating_modes', [])
        mode_details = next((m for m in modes if m.get('name', '').lower() == mode_name.lower()), {})

        prompt = f"""Generate a detailed functional test procedure for this operating mode.

System: {system_info.get('name')} ({system_info.get('tag')})
Operating Mode: {mode_name}
Mode Details: {json.dumps(mode_details)}
System Setpoints: {json.dumps(system_info.get('setpoints', []))}
System Interlocks: {json.dumps(system_info.get('interlocks', []))}

Return ONLY JSON (no explanation):
{{
    "test_name": "Functional Test - [Mode Name]",
    "objective": "what this test verifies",
    "prerequisites": [
        "list of conditions that must be met before testing"
    ],
    "safety_notes": [
        "safety considerations for this test"
    ],
    "procedure_steps": [
        {{
            "step_number": 1,
            "action": "specific action to take",
            "expected_result": "what should happen",
            "verification_method": "how to verify",
            "pass_criteria": "specific pass/fail criteria"
        }}
    ],
    "restore_steps": [
        "steps to return system to normal after test"
    ],
    "estimated_duration": "estimated time in minutes"
}}
"""

        response = self._call_llm(prompt, temperature=0.2, max_tokens=2000)
        return self._extract_json(response)


# Convenience function for simple usage
def get_ai_service(enabled: bool = True, model: str = None) -> AIService:
    """Get an AI service instance with optional configuration.

    Args:
        enabled: Whether AI features should be enabled
        model: Model name to use (defaults to Llama 3.3 70B)

    Returns:
        Configured AIService instance
    """
    config = AIConfig(
        enabled=enabled,
        model=model or AIModel.LLAMA_3_3_70B.value
    )
    return AIService(config)
