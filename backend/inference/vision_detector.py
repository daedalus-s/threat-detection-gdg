import google.generativeai as genai
import base64
from typing import Dict, Any, List
from PIL import Image
import io
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class VisionDetector:
    """Use Google AI Studio (Gemini) for vision-based threat detection"""
    
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Vision detector initialized with Gemini model")
    
    def analyze_frame(self, frame_base64: str, camera_id: int) -> Dict[str, Any]:
        """
        Analyze a camera frame for threats
        
        Returns:
            Dictionary with detection results including threats, people, objects
        """
        try:
            # Decode base64 to image
            image_data = base64.b64decode(frame_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Comprehensive threat detection prompt
            prompt = """Analyze this security camera image for potential threats or concerning situations. 

            Please identify:
            1. **Weapons**: Any visible weapons (guns, knives, blunt objects used aggressively)
            2. **People**: Number of people and whether they appear to be family/authorized (relaxed posture, casual clothing) or unfamiliar/threatening (masks, dark clothing, aggressive posture)
            3. **Aggressive behavior**: Fighting, raising arms to strike, forceful movements
            4. **Fire/Smoke**: Any signs of fire, flames, or smoke
            5. **Unusual situations**: People on the ground (potential fall), broken items, signs of forced entry
            6. **Crowd density**: Unusually high number of people for a home setting

            Respond in JSON format:
            {
                "weapons_detected": true/false,
                "weapon_type": "gun/knife/blunt_object/none",
                "weapon_confidence": 0.0-1.0,
                "people_count": number,
                "unfamiliar_faces": true/false,
                "unfamiliar_confidence": 0.0-1.0,
                "aggressive_behavior": true/false,
                "aggression_description": "description",
                "fire_smoke": true/false,
                "person_on_ground": true/false,
                "crowd_alert": true/false,
                "overall_threat_level": "none/low/medium/high/critical",
                "summary": "brief description of scene"
            }"""
            
            response = self.model.generate_content([prompt, image])
            
            # Parse response
            result = self._parse_response(response.text, camera_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Vision analysis failed for camera {camera_id}: {e}")
            return self._default_result(camera_id, error=str(e))
    
    def _parse_response(self, response_text: str, camera_id: int) -> Dict[str, Any]:
        """Parse Gemini response into structured format"""
        import json
        
        try:
            # Extract JSON from response (Gemini sometimes adds markdown)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
            result['camera_id'] = camera_id
            result['success'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse vision response: {e}\nResponse: {response_text[:200]}")
            
            # Fallback: Try to extract key information with simple parsing
            return {
                'camera_id': camera_id,
                'weapons_detected': 'weapon' in response_text.lower() or 'gun' in response_text.lower(),
                'people_count': 0,
                'unfamiliar_faces': False,
                'aggressive_behavior': 'aggress' in response_text.lower() or 'fight' in response_text.lower(),
                'fire_smoke': 'fire' in response_text.lower() or 'smoke' in response_text.lower(),
                'overall_threat_level': 'unknown',
                'summary': response_text[:200],
                'success': False,
                'parse_error': str(e)
            }
    
    def _default_result(self, camera_id: int, error: str = None) -> Dict[str, Any]:
        """Return default result when analysis fails"""
        return {
            'camera_id': camera_id,
            'weapons_detected': False,
            'weapon_type': 'none',
            'weapon_confidence': 0.0,
            'people_count': 0,
            'unfamiliar_faces': False,
            'unfamiliar_confidence': 0.0,
            'aggressive_behavior': False,
            'aggression_description': '',
            'fire_smoke': False,
            'person_on_ground': False,
            'crowd_alert': False,
            'overall_threat_level': 'none',
            'summary': 'Analysis failed',
            'success': False,
            'error': error
        }
    
    def detect_specific_threat(self, frame_base64: str, threat_type: str) -> Dict[str, Any]:
        """
        Focused detection for specific threat types
        
        Args:
            frame_base64: Base64 encoded image
            threat_type: 'weapon', 'fire', 'fall', 'crowd', 'aggression'
        """
        try:
            image_data = base64.b64decode(frame_base64)
            image = Image.open(io.BytesIO(image_data))
            
            prompts = {
                'weapon': 'Is there any weapon (gun, knife, bat, etc.) visible in this image? Respond with confidence level 0-100.',
                'fire': 'Is there any fire, flames, or heavy smoke in this image? Respond with confidence level 0-100.',
                'fall': 'Is there a person lying on the ground who may have fallen? Respond with confidence level 0-100.',
                'crowd': 'How many people are in this image? Is it an unusually large crowd for a home?',
                'aggression': 'Are there signs of physical aggression, fighting, or threatening gestures? Respond with confidence level 0-100.'
            }
            
            prompt = prompts.get(threat_type, 'Analyze this image for threats.')
            
            response = self.model.generate_content([prompt, image])
            
            return {
                'threat_type': threat_type,
                'detected': True,  # Parse from response
                'confidence': 0.0,  # Parse from response
                'description': response.text
            }
            
        except Exception as e:
            logger.error(f"Specific threat detection failed: {e}")
            return {
                'threat_type': threat_type,
                'detected': False,
                'confidence': 0.0,
                'error': str(e)
            }

# Global detector instance
_detector_instance = None

def get_detector() -> VisionDetector:
    """Get or create global detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = VisionDetector()
    return _detector_instance