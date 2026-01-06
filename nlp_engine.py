"""
nlp_engine.py
Natural Language Processing engine for intent detection.
Parses user commands and extracts intent and parameters.
"""

import re
from typing import Dict, List, Optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("[NLP] Warning: spaCy not available, using rule-based parsing only")


class IntentParser:
    """
    Parses natural language commands and extracts user intent.
    Uses rule-based matching with optional spaCy enhancement.
    """
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize the NLP engine.
        
        Args:
            use_spacy: Whether to use spaCy for advanced parsing (default: True)
        """
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.nlp = None
        
        if self.use_spacy:
            try:
                print("[NLP] Loading spaCy model...")
                self.nlp = spacy.load("en_core_web_sm")
                print("[NLP] spaCy model loaded successfully.")
            except Exception as e:
                print(f"[NLP] Could not load spaCy model: {e}")
                print("[NLP] Falling back to rule-based parsing")
                self.use_spacy = False
        
        # Define command patterns and their intents
        self.intent_patterns = {
            'open_app': [
                r'\b(?:open|launch|start|run)\s+(.+)',
                r'\b(?:can you |please )?open\s+(.+)',
            ],
            'close_app': [
                r'\b(?:close|quit|exit|stop)\s+(.+)',
            ],
            'search': [
                r'\b(?:search|look up|find|google)\s+(?:for\s+)?(.+)',
                r'\bwhat is\s+(.+)',
                r'\bwho is\s+(.+)',
                r'\btell me about\s+(.+)',
            ],
            'play_media': [
                r'\b(?:play|start playing)\s+(.+)',
                r'\bput on\s+(.+)',
            ],
            'system_command': [
                r'\b(shutdown|restart|reboot|sleep|lock)\s*(?:computer|system|pc)?',
                r'\b(?:turn off|shut down)\s+(?:the\s+)?(?:computer|system|pc)',
            ],
            'time': [
                r'\b(?:what time is it|tell me the time|current time)',
                r'\bwhat\'?s the time',
            ],
            'date': [
                r'\b(?:what\'?s (?:the )?date|today\'?s date|what day is it)',
            ],
            'weather': [
                r'\b(?:what\'?s the weather|weather forecast|how\'?s the weather)',
                r'\b(?:is it )?(?:raining|sunny|cloudy)',
            ],
            'volume': [
                r'\b(?:volume|sound)\s+(up|down|mute|unmute|\d+)',
                r'\b(?:increase|decrease|raise|lower)\s+(?:the\s+)?volume',
                r'\b(?:mute|unmute)',
            ],
            'exit': [
                r'\b(?:exit|quit|stop listening|goodbye|bye)',
            ],
        }
        
        # Application name mappings
        self.app_mappings = {
            'chrome': ['chrome', 'browser', 'google chrome'],
            'notepad': ['notepad', 'note pad', 'text editor'],
            'explorer': ['explorer', 'file explorer', 'files', 'my computer'],
            'calculator': ['calculator', 'calc'],
            'word': ['word', 'microsoft word'],
            'excel': ['excel', 'microsoft excel'],
            'powerpoint': ['powerpoint', 'microsoft powerpoint', 'ppt'],
            'spotify': ['spotify', 'music'],
            'vlc': ['vlc', 'vlc player', 'video player'],
        }
    
    def _normalize_app_name(self, app_name: str) -> str:
        """
        Normalize application names to standard forms.
        
        Args:
            app_name: Raw application name from speech
        
        Returns:
            Normalized application name
        """
        app_name_lower = app_name.lower().strip()
        
        for standard_name, aliases in self.app_mappings.items():
            if app_name_lower in aliases or app_name_lower == standard_name:
                return standard_name
        
        return app_name_lower
    
    def _extract_with_spacy(self, text: str) -> Dict[str, any]:
        """
        Use spaCy for advanced text analysis (optional enhancement).
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with extracted entities
        """
        doc = self.nlp(text)
        
        entities = {
            'nouns': [token.text for token in doc if token.pos_ == 'NOUN'],
            'verbs': [token.text for token in doc if token.pos_ == 'VERB'],
            'named_entities': [(ent.text, ent.label_) for ent in doc.ents],
        }
        
        return entities
    
    def parse_intent(self, text: str) -> Dict[str, any]:
        """
        Parse text and extract user intent with parameters.
        
        Args:
            text: User's spoken command as text
        
        Returns:
            Dictionary with intent and extracted parameters
            Format: {"intent": "action_type", "target": "parameter", "confidence": float}
        """
        if not text:
            return {"intent": "unknown", "error": "empty_input"}
        
        text = text.lower().strip()
        print(f"[NLP] Parsing: '{text}'")
        
        # Optional spaCy analysis
        spacy_data = None
        if self.use_spacy:
            try:
                spacy_data = self._extract_with_spacy(text)
            except Exception as e:
                print(f"[NLP] spaCy analysis failed: {e}")
        
        # Try to match against intent patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result = {"intent": intent, "confidence": 0.8}
                    
                    # Extract target/parameter if available
                    if match.groups():
                        target = match.group(1).strip()
                        
                        # Special handling for different intent types
                        if intent in ['open_app', 'close_app']:
                            result['target'] = self._normalize_app_name(target)
                        elif intent == 'search':
                            result['query'] = target
                        elif intent == 'play_media':
                            result['media'] = target
                        elif intent == 'system_command':
                            result['command'] = target if target else match.group(0).split()[0]
                        elif intent == 'volume':
                            result['action'] = target
                        else:
                            result['target'] = target
                    else:
                        # For intents without parameters (time, date, etc.)
                        if intent == 'system_command':
                            # Extract the actual command
                            words = text.split()
                            for word in ['shutdown', 'restart', 'reboot', 'sleep', 'lock']:
                                if word in text:
                                    result['command'] = word
                                    break
                    
                    print(f"[NLP] Intent detected: {result}")
                    return result
        
        # If no pattern matched, return unknown
        print(f"[NLP] No intent matched for: '{text}'")
        return {
            "intent": "unknown",
            "original_text": text,
            "confidence": 0.0
        }


def parse_intent(text: str) -> Dict[str, any]:
    """
    Standalone function to parse intent from text.
    
    Args:
        text: Input command text
    
    Returns:
        Intent dictionary
    """
    parser = IntentParser()
    return parser.parse_intent(text)


if __name__ == "__main__":
    # Test the NLP engine
    print("=== NLP Intent Parser Test ===\n")
    
    test_commands = [
        "open chrome",
        "search for weather today",
        "play some music",
        "shutdown the computer",
        "what time is it",
        "close notepad",
        "volume up",
        "tell me about python programming",
        "random gibberish that makes no sense",
    ]
    
    parser = IntentParser(use_spacy=True)
    
    for command in test_commands:
        print(f"\nCommand: '{command}'")
        result = parser.parse_intent(command)
        print(f"Result: {result}")
        print("-" * 50)