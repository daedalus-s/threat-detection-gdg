from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class ThreatAnalyzer:
    """Analyze detection results and determine threat level and required actions"""
    
    def __init__(self):
        self.threat_history = []  # Store recent threats for correlation
        self.max_history = 100
    
    def analyze_vision_threat(self, vision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze vision detection results and determine if it constitutes a threat
        
        Returns:
            Threat alert dictionary if threat detected, None otherwise
        """
        threats = []
        
        # Critical: Weapon + Unfamiliar face
        if (vision_result.get('weapons_detected', False) and 
            vision_result.get('weapon_confidence', 0) >= settings.weapon_confidence_threshold and
            vision_result.get('unfamiliar_faces', False) and
            vision_result.get('unfamiliar_confidence', 0) >= settings.unknown_person_confidence_threshold):
            
            threats.append({
                'type': 'WEAPON_INTRUDER',
                'severity': 'CRITICAL',
                'description': f"Weapon ({vision_result.get('weapon_type', 'unknown')}) detected with unfamiliar person",
                'action_required': 'CALL_911',
                'confidence': min(vision_result.get('weapon_confidence', 0), 
                                vision_result.get('unfamiliar_confidence', 0))
            })
        
        # High: Weapon detected (even with familiar face - could be threatening family)
        elif (vision_result.get('weapons_detected', False) and 
              vision_result.get('weapon_confidence', 0) >= settings.weapon_confidence_threshold):
            
            threats.append({
                'type': 'WEAPON_DETECTED',
                'severity': 'HIGH',
                'description': f"Weapon ({vision_result.get('weapon_type', 'unknown')}) detected",
                'action_required': 'NOTIFY_OWNER',
                'confidence': vision_result.get('weapon_confidence', 0)
            })
        
        # High: Aggressive behavior
        if vision_result.get('aggressive_behavior', False):
            threats.append({
                'type': 'AGGRESSIVE_BEHAVIOR',
                'severity': 'HIGH',
                'description': vision_result.get('aggression_description', 'Aggressive behavior detected'),
                'action_required': 'NOTIFY_OWNER',
                'confidence': 0.75
            })
        
        # Critical: Fire/Smoke
        if vision_result.get('fire_smoke', False):
            threats.append({
                'type': 'FIRE_DETECTED',
                'severity': 'CRITICAL',
                'description': 'Fire or smoke detected',
                'action_required': 'CALL_911',
                'confidence': 0.85
            })
        
        # Medium: Person on ground (potential fall)
        if vision_result.get('person_on_ground', False):
            threats.append({
                'type': 'PERSON_DOWN',
                'severity': 'MEDIUM',
                'description': 'Person detected on ground - possible fall',
                'action_required': 'CHECK_VITALS',
                'confidence': 0.70
            })
        
        # Medium: Unusual crowd
        if vision_result.get('crowd_alert', False):
            threats.append({
                'type': 'CROWD_ALERT',
                'severity': 'MEDIUM',
                'description': f"Unusual number of people detected: {vision_result.get('people_count', 0)}",
                'action_required': 'NOTIFY_OWNER',
                'confidence': 0.65
            })
        
        # Return highest severity threat if any
        if threats:
            # Sort by severity and confidence
            severity_order = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
            threats.sort(key=lambda x: (severity_order[x['severity']], x['confidence']), reverse=True)
            
            primary_threat = threats[0]
            
            alert = {
                'alert_type': primary_threat['type'],
                'severity': primary_threat['severity'],
                'description': primary_threat['description'],
                'action_required': primary_threat['action_required'],
                'confidence': primary_threat['confidence'],
                'camera_id': vision_result.get('camera_id'),
                'timestamp': datetime.now().isoformat(),
                'all_threats': threats,
                'vision_summary': vision_result.get('summary', ''),
                'source': 'vision'
            }
            
            self._add_to_history(alert)
            return alert
        
        return None
    
    def analyze_sensor_threat(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze sensor data for threats
        
        Returns:
            Threat alert dictionary if threat detected, None otherwise
        """
        device_type = sensor_data.get('device_type')
        
        # Smartwatch vitals analysis
        if device_type == 'smartwatch':
            return self._analyze_vitals(sensor_data)
        
        # Accelerometer fall detection
        elif device_type == 'accelerometer':
            event = sensor_data.get('event')
            if event in ['FALL_DETECTED', 'HIGH_IMPACT']:
                return {
                    'alert_type': 'FALL_DETECTED',
                    'severity': 'HIGH',
                    'description': f"Fall or high impact detected - magnitude: {sensor_data.get('magnitude', 0):.2f}",
                    'action_required': 'CHECK_VITALS',
                    'confidence': 0.85,
                    'device_id': sensor_data.get('device_id'),
                    'timestamp': sensor_data.get('timestamp'),
                    'sensor_data': sensor_data,
                    'source': 'accelerometer'
                }
        
        # Microphone audio events
        elif device_type == 'microphone':
            event = sensor_data.get('event')
            if event == 'SCREAM_DETECTED':
                return {
                    'alert_type': 'SCREAM_DETECTED',
                    'severity': 'HIGH',
                    'description': f"Scream detected - {sensor_data.get('sound_level_db', 0):.1f} dB",
                    'action_required': 'CHECK_CAMERAS',
                    'confidence': sensor_data.get('confidence', 0.8),
                    'device_id': sensor_data.get('device_id'),
                    'timestamp': sensor_data.get('timestamp'),
                    'sensor_data': sensor_data,
                    'source': 'microphone'
                }
            elif event in ['LOUD_NOISE', 'GLASS_BREAK']:
                return {
                    'alert_type': event,
                    'severity': 'MEDIUM',
                    'description': f"{event.replace('_', ' ').title()} - {sensor_data.get('sound_level_db', 0):.1f} dB",
                    'action_required': 'CHECK_CAMERAS',
                    'confidence': sensor_data.get('confidence', 0.75),
                    'device_id': sensor_data.get('device_id'),
                    'timestamp': sensor_data.get('timestamp'),
                    'sensor_data': sensor_data,
                    'source': 'microphone'
                }
        
        # Smoke detector
        elif device_type == 'smoke_detector':
            event = sensor_data.get('event')
            if event == 'FIRE_DETECTED':
                return {
                    'alert_type': 'FIRE_DETECTED',
                    'severity': 'CRITICAL',
                    'description': f"Fire detected in {sensor_data.get('location', 'unknown location')}",
                    'action_required': 'CALL_911',
                    'confidence': 0.95,
                    'device_id': sensor_data.get('device_id'),
                    'timestamp': sensor_data.get('timestamp'),
                    'sensor_data': sensor_data,
                    'source': 'smoke_detector'
                }
            elif event == 'SMOKE_DETECTED':
                return {
                    'alert_type': 'SMOKE_DETECTED',
                    'severity': 'HIGH',
                    'description': f"Smoke detected in {sensor_data.get('location', 'unknown location')}",
                    'action_required': 'CHECK_CAMERAS',
                    'confidence': 0.85,
                    'device_id': sensor_data.get('device_id'),
                    'timestamp': sensor_data.get('timestamp'),
                    'sensor_data': sensor_data,
                    'source': 'smoke_detector'
                }
        
        return None
    
    def _analyze_vitals(self, smartwatch_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze smartwatch vitals for health threats"""
        issues = []
        
        heart_rate = smartwatch_data.get('heart_rate', 70)
        spo2 = smartwatch_data.get('spo2', 95)
        bp = smartwatch_data.get('blood_pressure', {})
        systolic = bp.get('systolic', 120)
        
        # Check for abnormal vitals
        if heart_rate >= settings.heart_rate_spike_threshold:
            issues.append(f"Elevated heart rate: {heart_rate} bpm")
        
        if heart_rate <= settings.heart_rate_drop_threshold:
            issues.append(f"Critically low heart rate: {heart_rate} bpm")
        
        if spo2 < settings.spo2_threshold:
            issues.append(f"Low oxygen saturation: {spo2}%")
        
        if systolic < 90:
            issues.append(f"Low blood pressure: {systolic}/{bp.get('diastolic', 60)}")
        
        if issues:
            severity = 'CRITICAL' if (heart_rate <= 40 or spo2 < 85) else 'HIGH'
            
            return {
                'alert_type': 'VITALS_ABNORMAL',
                'severity': severity,
                'description': '; '.join(issues),
                'action_required': 'CHECK_PERSON' if severity == 'HIGH' else 'CALL_911',
                'confidence': 0.90,
                'device_id': smartwatch_data.get('device_id'),
                'timestamp': smartwatch_data.get('timestamp'),
                'sensor_data': smartwatch_data,
                'source': 'smartwatch'
            }
        
        return None
    
    def _add_to_history(self, alert: Dict[str, Any]):
        """Add alert to history for correlation"""
        self.threat_history.append(alert)
        if len(self.threat_history) > self.max_history:
            self.threat_history.pop(0)
    
    def correlate_threats(self, time_window_seconds: int = 30) -> List[Dict[str, Any]]:
        """Find correlated threats within a time window"""
        # For demo: simple correlation logic
        # In production: more sophisticated temporal correlation
        return self.threat_history[-5:]  # Return last 5 threats

# Global analyzer instance
_analyzer_instance = None

def get_analyzer() -> ThreatAnalyzer:
    """Get or create global analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ThreatAnalyzer()
    return _analyzer_instance